import rclpy
from rclpy.node import Node

from robomaster import robot

from sensor_msgs.msg import Imu
from pyquaternion import Quaternion
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PointStamped, TransformStamped
from std_msgs.msg import Bool
import tf2_ros

from joystick_msgs.msg import XBox360Controller
from robomaster_msgs.msg import ChassisAttitute, ChassisPosition, ChassisStatus, ChassisEsc, ChassisIMU
from robomaster_msgs.msg import GripperStatus
from robomaster_msgs.msg import ServoStatus
from robomaster_msgs.msg import RoboticArmPosition

from cv_bridge import CvBridge

from collections import deque
from threading import Thread, Event
import time


INIT_POS = (180, -70)
FINAL_POS = (100, 100)


class TeleOperationNode(Node):

    def __init__(self) -> None:
        super().__init__('rm_teleoperation')
        self._log = False

        self._robot = robot.Robot()

        self._joint_angle = [None] * 2
        self._joint_speed = [None] * 2
        self._end_position = [None] * 2 + [0]

        # arm pub
        self._pub_arm_position = self.create_publisher(RoboticArmPosition, "/arm/raw/position", 3) # end position publisher
       
        # servo pub
        self._pub_servo_value = self.create_publisher(ServoStatus, "/servo/raw/value", 3) # joint value publisher
        
        # gripper pub
        self._pub_gripper_status = self.create_publisher(GripperStatus, "/gripper/raw/status", 3) # gripper status publisher

        # img pub
        self._pub_image = self.create_publisher(Image, "/camera/raw/image", 3) # image publisher

        # chassis pub
        self._pub_chassis_attitute = self.create_publisher(ChassisAttitute, "/chassis/raw/attitute", 3) # rpy publisher
        self._pub_chassis_position = self.create_publisher(ChassisPosition, "/chassis/raw/position", 3) # xyz publisher
        self._pub_chassis_status = self.create_publisher(ChassisStatus, "/chassis/raw/status", 3) # status publisher
        self._pub_chassis_esc = self.create_publisher(ChassisEsc, "/chassis/raw/esc", 3) # esc publisher
        self._pub_chassis_imu = self.create_publisher(ChassisIMU, "/chassis/raw/imu", 3) # imu publisher

        # action pub
        self._pub_action = self.create_publisher(Bool, '/data_collection_start', 3) # code flag publisher
        
        # joy sub
        self._sub_joy = self.create_subscription(XBox360Controller, '/joystick', self._joy_cb, 3)
        
        self._cv_bridge = CvBridge()

        self._axis_threshold = 0.1
        
        self._event = Event()

        # arm
        self._arm_deque = deque()
        self._arm_moving = False
        self._arm_thread = Thread(target=self._arm_action)
        self._arm_thread.start()
        self._arm_postion = []
        
        # flags
        self._action_flag = True
        self._action_activate = False

        # main
        self._main_thread = Thread(target=self._start)
        self._main_thread.start()
        
        # chassis
        self._chassis_deque = deque()
        self._chassis_moving = False
        self._chassis_thread = Thread(target=self._chassis_action)
        self._chassis_thread.start()

        # gripper
        self._gripper_deque = deque()
        self._gripper_status = None
        self._gripper_moving = False
        self._gripper_command = "None"
        self._gripper_power = None
        self._gripper_thread = Thread(target=self._gripper_action)
        self._gripper_thread.start()

        self.shutdown = False
        self._gripper_action_end = False
        self._chassis_action_end = False
        self._arm_action_end = False
    
    def _init_sub(self, freq=50) -> bool:
        if freq not in (1, 5, 10, 20, 50): return False
        # 末端
        self._arm.sub_position(freq, self._arm_position_cb)
        # 关节
        self._servo.sub_servo_info(freq, self._servo_value_cb)
        # 夹爪
        self._gripper.sub_status(freq, self._gripper_status_cb)
        # 相机        
        self._vision.start_video_stream(display=False)
        self._cam_thread = Thread(target=self._get_image)
        self._cam_thread.start()
        # 底盘姿态
        self._init_orientation, self._last_attitude = None, None
        self._chassis.sub_attitude(freq, self._chassis_attitude_cb)
        # 底盘位置
        self._chassis.sub_position(0, freq, self._odom_cb)
        # IMU
        self._chassis.sub_imu(freq, self._chassis_imu_cb)
        # 底盘状态
        self._chassis.sub_status(freq, self._chassis_status_cb)
        # 电调
        self._chassis.sub_esc(freq, self._chassis_esc_cb)
        return True
    
    def _unsub(self):
        self._arm.unsub_position()
        self._gripper.unsub_status()
        self._servo.unsub_servo_info()

        self._vision.stop_video_stream()

        self._chassis.unsub_attitude()
        self._chassis.unsub_position()
        self._chassis.unsub_imu()
        self._chassis.unsub_status()
        self._chassis.unsub_esc()

        self._robot.close()

    def arm_move(self, position):
        x, y = position
        self._arm.move(x, y).wait_for_completed(timeout=1)
    
    def arm_moveto(self, position):
        x, y = position
        self._arm.moveto(x, y).wait_for_completed(timeout=1)
    
    def arm_recenter(self):
        self._arm.moveto(5, 5).wait_for_completed()
        self.get_logger().info("Arm recenter")
    
    def gripper(self, action, power=50):
        if power not in [power for power in range(1,100)]: return False
        
        self._gripper_command = action
        self._gripper_power = power
        if action == "grab": self._gripper.close(power)
        elif action == "release": self._gripper.open(power)
        elif action == "pause": self._gripper.pause()
        else: return
    
    def _get_image(self):
        while rclpy.ok():
            try:
                # tsn = time.time()
                img = self._vision.read_cv2_image(timeout=0.1, strategy='newest')
                # tsn2 = time.time()
                msg = self._cv_bridge.cv2_to_imgmsg(img, encoding="bgr8")
                # msg.header.stamp = tsn + (tsn2 - tsn) / 2.0
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = "camera_link_optical_frame"
                self._pub_image.publish(msg)
            except:
                pass
    
    def chassis_move(self, x_dis, y_dis, z_angle, xy_vel=0, z_w=0):
        self._chassis.move(x_dis, y_dis, z_angle, xy_vel, z_w).wait_for_completed(timeout=10)
    
    def chassis_wheels(self, wheel_speed, /, *, timeout=1):
        w1, w2, w3, w4 = wheel_speed
        self._chassis.drive_wheels(w1, w2, w3, w4, timeout)
    
    def chassis_speed(self, x_vel, y_vel, z_w, /, *, timeout=1):
        self._chassis.drive_speed(x_vel, y_vel, z_w, timeout)
    
    def _chassis_attitude_cb(self, attitude_data):
        yaw, pitch, roll = attitude_data
        if self._log: self.get_logger().info("chassis attitude: yaw:{0}".format(yaw))

        msg = ChassisAttitute()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "chassis_attitude_raw"
        msg.yaw = yaw
        msg.pitch = pitch
        msg.roll = roll
        self._pub_chassis_attitute.publish(msg)

        self._last_attitude = Quaternion(axis=(0, 0, 1), degrees=-yaw) * Quaternion(axis=(0, 1, 0), degrees=-pitch) * Quaternion(axis=(1, 0, 0), degrees=roll)
        if self._init_orientation is None: self._init_orientation = self._last_attitude
    
    def _odom_cb(self, position_data):
        x, y, z = position_data
        if self._log: self.get_logger().info("chassis position: x:{0}, y:{1}".format(x, y)) # x 前正 y 右正

        msg = ChassisPosition()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "chassis_position_raw"
        msg.x = x
        msg.y = y
        msg.z = z
        self._pub_chassis_position.publish(msg)

    def _chassis_imu_cb(self, imu_data):
        acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z = imu_data
        if self._log: print("chassis imu: acc_x:{0}, acc_y:{1}, acc_z:{2}, gyro_x:{3}, gyro_y:{4}, gyro_z:{5}".format(acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z))
        
        msg = ChassisIMU()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "chassis_imu_raw"
        msg.acc_x = acc_x
        msg.acc_y = acc_y
        msg.acc_z = acc_z
        msg.gyro_x = gyro_x
        msg.gyro_y = gyro_y
        msg.gyro_z = gyro_z
        self._pub_chassis_imu.publish(msg)
    
    def _chassis_status_cb(self, status_info):
        static_flag, up_hill, down_hill, on_slope, pick_up, slip_flag, impact_x, impact_y, impact_z, roll_over, hill_static = status_info
        if self._log: print("chassis status: static_flag:{0}, up_hill:{1}, down_hill:{2}, on_slope:{3}, "
          "pick_up:{4}, slip_flag:{5}, impact_x:{6}, impact_y:{7}, impact_z:{8}, roll_over:{9}, "
          "hill_static:{10}".format(static_flag, up_hill, down_hill, on_slope, pick_up,
                                   slip_flag, impact_x, impact_y, impact_z, roll_over, hill_static))
        
        msg = ChassisStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "chassis_status_raw"
        msg.is_static = bool(static_flag)
        msg.up_hill = bool(up_hill)
        msg.down_hill = bool(down_hill)
        msg.on_slope = bool(on_slope)
        msg.is_pick_up = bool(pick_up)
        msg.slip = bool(slip_flag)
        msg.impact_x = bool(impact_x)
        msg.impact_y = bool(impact_y)
        msg.impact_z = bool(impact_z)
        msg.roll_over = bool(roll_over)
        msg.hill = bool(hill_static)
        self._pub_chassis_status.publish(msg)

    def _chassis_esc_cb(self, esc_data):
        speed, angle, timestamp, state = esc_data
        if self._log: print("chassis esc: speed:{0}, angle:{1}, timestamp:{2}, state:{3}".format(speed, angle, timestamp, state))

        msg = ChassisEsc()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "chassis_esc_raw"
        # 前左
        msg.front_right.angle = angle[0]
        msg.front_right.speed = speed[0]
        msg.front_right.time_stamp = timestamp[0]
        msg.front_right.status = state[0]
        # 前右
        msg.front_left.angle = angle[1]
        msg.front_left.speed = speed[1]
        msg.front_left.time_stamp = timestamp[1]
        msg.front_left.status = state[1]
        # 后左
        msg.back_left.angle = angle[2]
        msg.back_left.speed = speed[2]
        msg.back_left.time_stamp = timestamp[2]
        msg.back_left.status = state[2]
        # 后右
        msg.back_right.angle = angle[3]
        msg.back_right.speed = speed[3]
        msg.back_right.time_stamp = timestamp[3]
        msg.back_right.status = state[3]
        self._pub_chassis_esc.publish(msg)
    
    def _arm_position_cb(self, position_data):
        pos_x, pos_y = position_data
        self._arm_postion = [pos_x, pos_y]
        if self._log: self.get_logger().info("Arm: x = {0}, y = {1}".format(pos_x, pos_y))

        msg = RoboticArmPosition()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "robotic_arm_position"
        msg.x = pos_x
        msg.y = pos_y
        msg.z = 0
        self._pub_arm_position.publish(msg)
    
    def _gripper_status_cb(self, status_info):
        self._gripper_status = status_info
        if self._log: print("Gripper: {}".format(self._gripper_status))

        msg = GripperStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "gripper_status_raw"
        msg.status = self._gripper_status
        msg.power = self._gripper_power
        msg.action = self._gripper_command
        self._pub_gripper_status.publish(msg)

    def _servo_value_cb(self, servo_data):
        status, speed, angle = servo_data
        if self._log: print("Servo: status: {}, speed: {}, angle: {}".format(status, speed, angle))

        msg = ServoStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.servo_0.valid = bool(status[0])
        msg.servo_0.value = angle[0]
        msg.servo_0.speed = speed[0]
        msg.servo_1.valid = bool(status[1])
        msg.servo_1.value = angle[1]
        msg.servo_1.speed = speed[1]
        msg.servo_2.valid = bool(status[2])
        msg.servo_2.value = angle[2]
        msg.servo_2.speed = speed[2]
        msg.servo_3.valid = bool(status[3])
        msg.servo_3.value = angle[3]
        msg.servo_3.speed = speed[3]

        self._pub_servo_value.publish(msg)
        
    def _start(self):
        try:
            while not self._robot.initialize(conn_type="sta", sn="3JKCJC400301RW"):
                self.get_logger().error("Initialize fail")
            self._robot.set_robot_mode(mode=robot.FREE)
            self.get_logger().info("RM init")

            self._arm = self._robot.robotic_arm
            self._gripper = self._robot.gripper
            self._servo = self._robot.servo
            self._vision = self._robot.camera
            self._chassis = self._robot.chassis

            self._init_sub()

            self._event.set()

            self.get_logger().info("Press START button to start")
            while rclpy.ok():
                if self._action_activate: break
            self.get_logger().info("Press BACK button to shut down")
            while rclpy.ok():
                if not self._action_activate: break
        except KeyboardInterrupt:
            self.get_logger().error("Shut down")
        finally:
            while not self._gripper_action_end or not self._chassis_action_end or not self._arm_action_end: pass
            self._unsub()
            self.get_logger().info("Node End")
            self.shutdown = True

    # core code
    def _joy_cb(self, msg: XBox360Controller):
        current_time = time.time()

        # data collection
        if msg.button_start == 1 and self._action_flag:
            action = Bool()
            action.data = True
            self._pub_action.publish(action)
            self._action_activate = True
            self._action_flag = False
        if msg.button_back == 1 and not self._action_flag:
            action = Bool()
            action.data = False
            self._pub_action.publish(action)
            self._action_activate = False
            self._action_flag = True

        # arm
        if msg.hat_x != 0 or msg.hat_y != 0:
            # k = 10
            k = 20
            if len(self._arm_deque) > 20: self._arm_deque.popleft()
            self._arm_deque.append((current_time, self.arm_move, (k*msg.hat_y, k*msg.hat_x)))
        # if msg.button_rb == 1: self._arm_deque.append((current_time, self.arm_moveto, (75, 145)))
        # if msg.button_lb == 1: self._arm_deque.append((current_time, self.arm_moveto, (200, -50)))
        
        # gripper
        if msg.button_a == 1: self._gripper_deque.append((current_time, self.gripper, ("release", 70)))
        if msg.button_b == 1: self._gripper_deque.append((current_time, self.gripper, ("grab", 15)))
        # if msg.button_x == 1: self._gripper_deque.append((current_time, self.gripper, ("pause", 50)))
        
        # chassis
        if msg.button_rs == 1: k, k_w = 0.4, 40
        # else: k, k_w = 0.1, 15
        else: k, k_w = 0.1, 5
        x_vel = -msg.axis_rs_y if abs(msg.axis_rs_y) >= self._axis_threshold else 0
        y_vel = msg.axis_rs_x if abs(msg.axis_rs_x) >= self._axis_threshold else 0
        delta = msg.axis_lt - msg.axis_rt
        z_w = -delta if abs(delta) >= self._axis_threshold else 0
        # z_w = 0
        if x_vel == 0 and y_vel == 0 and z_w == 0 and not self._chassis_moving: return
        if x_vel == 0 and y_vel == 0 and z_w == 0: self._chassis_moving = False
        else: self._chassis_moving = True
        self._chassis_deque.append((current_time, self.chassis_speed, (x_vel*k, y_vel*k, z_w*k_w)))
    
    def _gripper_action(self):
        self._event.wait()
        self.gripper("release", 70)
        try:
            while rclpy.ok() and not self._action_activate: pass
            self.get_logger().info("Gripper action activate")
            while rclpy.ok():
                if not self._action_activate: break
                if not self._gripper_deque: continue

                current_time = time.time()
                while self._gripper_deque:
                    stamp, func, args = self._gripper_deque.popleft()
                    if stamp > current_time: break
                func(*args)
        except KeyboardInterrupt:
            self.get_logger().error("Gripper action shut down")
        finally:
            self.gripper("release", 70)
            self.get_logger().info("Gripper action End")
            self._gripper_action_end = True
    
    def _chassis_action(self):
        self._event.wait()
        try:
            while rclpy.ok() and not self._action_activate: pass
            self.get_logger().info("Chassis action activate")
            while rclpy.ok():
                if not self._action_activate: break
                if not self._chassis_deque: continue

                current_time = time.time()
                while self._chassis_deque:
                    stamp, func, args = self._chassis_deque.popleft()
                    if stamp > current_time: break
                func(*args)
        except KeyboardInterrupt:
            self.get_logger().error("Chassis action shut down")
        finally:
            self.get_logger().info("Chassis action End")
            self._chassis_action_end = True
    
    def _arm_action(self):
        self._event.wait()
        # self.arm_moveto((100, 100))
        # time.sleep(0.5)
        self.arm_moveto(INIT_POS)
        time.sleep(0.5)
        try:
            while rclpy.ok() and not self._action_activate: pass
            self.get_logger().info("Arm action activate")
            while rclpy.ok():
                if not self._action_activate: break
                if not self._arm_deque: continue

                current_time = time.time()
                while self._arm_deque:
                    stamp, func, position = self._arm_deque.popleft()
                    if stamp > current_time: break
                func(position)
        except KeyboardInterrupt:
            self.get_logger().error("Arm action shut down")
        finally:
            self.arm_moveto(FINAL_POS)
            self.get_logger().info("Arm action End")
            self._arm_action_end = True


def main(args=None):
    rclpy.init(args=args)

    node = TeleOperationNode()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=1)
            if node.shutdown: break
    except KeyboardInterrupt: pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
