import os
import re
import time
import cv2
import numpy as np
import matplotlib.pyplot as plt
from .utils import HOME_PATH, load_json, save_json, load_yaml, save_yaml, log_info, log_warn, log_error, extract_last_number, save_video_v2
from moviepy.editor import VideoFileClip
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
from robomaster import robot
from collections import deque
from threading import Thread
import requests
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class BaseTokenizeDataset():

    def __init__(self, dataset_directory) -> None:
        self._dataset_dir = dataset_directory
    
    def check_dataset(self):
        if not os.path.exists(self._dataset_dir): return False

        yaml_file = "dataset_information.yaml"
        if yaml_file not in os.listdir(self._dataset_dir): return False

        data = load_yaml(os.path.join(self._dataset_dir, yaml_file))
        
        self._task_name = data["dataset_name"]
        self._episode_info = data["episode_info"]
        self._episode_names = sorted(list(data["episode_info"].keys()), key=lambda name: extract_last_number(name, ""))
        return True

    def check_distribution(self):
        if not os.path.exists(self._dataset_dir): return False

        json_file = "data_distribution.json"
        if json_file not in os.listdir(self._dataset_dir): return False

        data = load_json(os.path.join(self._dataset_dir, json_file))

        self._data_distribution = data
        return True


class Decoder():

    def __init__(self, name, data_distribution, vocab_size, log=False) -> None:
        self._name = name
        self._data_distribution = data_distribution
        self._vocab_size = vocab_size

        self._min_value = data_distribution[0]
        self._max_value = data_distribution[1]

        self._log = log
    
    def decode(self, token: str):
        if not 0 <= int(token) <= 255:
            if self._log: print(f"[Decoder {self._name}] Wrong token: {token}")
            return None
        tile = np.linspace(self._min_value, self._max_value, self._vocab_size)[:, None]
        value = tile[int(token)][0]
        if self._log: print(f"[Decoder {self._name}] token {token} -> value {value}")
        return value


class BaseRobotInference():

    def __init__(self, 
                node,
                #  sn="159CK9W0060AHS", 
                sn="3JKCJC400301RW",
                dataset_dir=os.path.join(HOME_PATH, "RoboMatrixDatasetsDIY"),
                task_name="",
                url="http://localhost:7893/process_frame",
                arm_init_pose=(180, -70),
                ) -> None:
        
        self.node = node
        # self.publisher_ = self.node.create_publisher(Image, 'image_topic', 10)
        self.publisher_ = self.node.create_publisher(Image, "/camera/raw/image", 3) # image publisher
        self.bridge = CvBridge()

        self._url = url
        log_info(f"[BaseRobotInference] URL: {self._url}")
        
        self._robot = robot.Robot()
        self._robot_sn = sn
        log_info(f"[BaseRobotInference] Robot SN: {self._robot_sn}")
        self._robot_ok = False

        self.arm_init_pose = arm_init_pose
        log_info(f"[BaseRobotInference] Arm init pose: {self.arm_init_pose}")

        distribution_file = os.path.join(dataset_dir, task_name, "data_distribution.json")
        self._distribution = load_json(distribution_file)
        log_info(f"[BaseRobotInference] Distribution file: {distribution_file}")
        
        self._range = {
            "arm":
            {
                "x": self._distribution["arm"][0],
                "y": self._distribution["arm"][1],
            },
            "chassis":
            {
                "d_x": self._distribution["chassis"][0],
                "d_y": self._distribution["chassis"][1],
                "d_yaw": self._distribution["chassis"][2],
            }
        }
        log_info(f"[BaseRobotInference] Distribution info:")
        for s in self._range["chassis"]:
            s_min = self._range["chassis"][s][0]
            s_max = self._range["chassis"][s][1]
            log_info(f"Chassis {s}: {s_min} ~ {s_max}")
        for s in self._range["arm"]:
            s_min = self._range["arm"][s][0]
            s_max = self._range["arm"][s][1]
            log_info(f"Arm {s}: {s_min} ~ {s_max}")

        self._arm_position_x_decoder = Decoder("arm_x", self._range["arm"]["x"], 256)
        self._arm_position_y_decoder = Decoder("arm_y", self._range["arm"]["y"], 256)
        self._chassis_position_x_decoder = Decoder("chassis_d_x", self._range["chassis"]["d_x"], 256)
        self._chassis_position_y_decoder = Decoder("chassis_d_y", self._range["chassis"]["d_y"], 256)
        self._chassis_position_yaw_decoder = Decoder("chassis_d_yaw", self._range["chassis"]["d_yaw"], 256)

        self._rate = 30
        self._log = False

        self._images = []

        self.init_robot()

    def init_robot(self):
        while not self._robot.initialize(conn_type="sta", sn=self._robot_sn):
            log_error("[BaseRobotInference] Initialize robot fail")

        freq = 50

        # 末端
        self._arm = self._robot.robotic_arm

        self._arm.sub_position(freq, self._update_arm_position)

        self._arm_position_deque = deque()

        self.arm_moveto(self.arm_init_pose)
        
        # 关节
        self._servo = self._robot.servo

        self._servo.sub_servo_info(freq, self._update_servo)

        self._servo_value_deque = deque()
        
        # 夹爪
        self._gripper = self._robot.gripper

        self._gripper.sub_status(freq, self._update_gripper)

        self._gripper_status_deque = deque()

        self._gripper_status = None
        self._gripper_command = "None"
        self._gripper_power = None

        self.gripper("release", 70)
        
        # 相机
        self._vision = self._robot.camera
          
        self._vision.start_video_stream(display=False)

        self._image_deque = deque()
        self._current_image_data = None

        self._cam_thread = Thread(target=self._update_image)
        self._cam_thread.start()
        
        # 底盘
        self._chassis = self._robot.chassis
        # 姿态
        self._chassis.sub_attitude(freq, self._update_chassis_attitude)
        self._chassis_attitute_deque = deque()
        # 位置
        self._chassis.sub_position(0, freq, self._update_chassis_position)
        self._chassis_position_deque = deque()
        # IMU
        self._chassis.sub_imu(freq, self._update_chassis_imu)
        self._chassis_imu_deque = deque()
        # 状态
        self._chassis.sub_status(freq, self._update_chassis_status)
        self._chassis_status_deque = deque()
        # 电调
        self._chassis.sub_esc(freq, self._update_chassis_esc)
        self._chassis_esc_data_deque = deque()

        self._robot_ok = True
        self._robot.led.set_led(comp="all", r=0, g=255, b=0, effect='breath', freq=1)
        log_info("[BaseRobotInference] Initialize robot success")
        return self._robot_ok

    def start_robot(self):
        if not self._robot_ok: return False

        self._core_thread = Thread(target=self._core_loop)
        self._core_thread.start()

    def close_robot(self):
        if not self._robot_ok: return
        self._robot_ok = False
        
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
    
    def _update_arm_position(self, position_data):
        if len(self._arm_position_deque) >= 100: self._arm_position_deque.popleft()
        
        pos_x, pos_y = position_data
        time_stamp = time.time()
        data = (time_stamp, [pos_x, pos_y])

        self._arm_x, self._arm_y = pos_x, pos_y

        self._arm_position_deque.append(data)

        if self._log: print("End position: x: {0}, y: {1}".format(pos_x, pos_y))

    def _update_servo(self, servo_data):
        if len(self._servo_value_deque) >= 100: self._servo_value_deque.popleft()
        
        time_stamp = time.time()
        status, speeds, angles = servo_data
        data = (time_stamp, angles[:2], speeds[:2])
        
        self._servo_value_deque.append(data)

        if self._log: print("Servo: status: {}, speed: {}, angle: {}".format(status, speeds, angles))
    
    def _update_gripper(self, status_info):
        if len(self._gripper_status_deque) >= 100: self._gripper_status_deque.popleft()
        
        time_stamp = time.time()
        self._gripper_status = status_info
        data = (time_stamp, self._gripper_status, self._gripper_power, self._gripper_command)
        
        self._gripper_status_deque.append(data)

        if self._log: print("Gripper: {}".format(self._gripper_status))

    def _update_image(self):
        while True:
            try:
                if len(self._image_deque) >= 100: self._image_deque.popleft()
                time_stamp = time.time()
                
                image = self._vision.read_cv2_image(timeout=0.1, strategy='newest')

            
                data = (time_stamp, image)
                # self._images.append(image)
                self._images.append(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

                self._image_deque.append(data)
                self._current_image_data = data
            except:
                continue
            ros_image = self.bridge.cv2_to_imgmsg(image, encoding='bgr8')
            ros_image.header.stamp = self.node.get_clock().now().to_msg()
            # print(ros_image.header.stamp)
            ros_image.header.frame_id = "camera_link_optical_frame"
            self.publisher_.publish(ros_image)

    def _update_chassis_attitude(self, attitude_data):
        if len(self._chassis_attitute_deque) >= 100: self._chassis_attitute_deque.popleft()
        
        yaw, pitch, roll = attitude_data

        time_stamp = time.time()
        attitute = [yaw, pitch, roll]
        data = (time_stamp, attitute)
        
        self._chassis_attitute_deque.append(data)

        if self._log: print("chassis attitude: yaw:{0}, pitch:{1}, roll:{2} ".format(yaw, pitch, roll))

    def _update_chassis_position(self, position_data):
        if len(self._chassis_position_deque) >= 100: self._chassis_position_deque.popleft()
        
        x, y, z = position_data
        time_stamp = time.time()
        position = [x, y]
        data = (time_stamp, position)

        self._chassis_position_deque.append(data)
        
        if self._log: print("chassis position: x:{0}, y:{1}, z:{2}".format(x, y, z))
    
    def _update_chassis_imu(self, imu_data):
        if len(self._chassis_imu_deque) >= 100: self._chassis_imu_deque.popleft()
        
        acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z = imu_data

        time_stamp = time.time()
        linear_acceleration = [acc_x, acc_y, acc_z]
        angular_velocity = [gyro_x, gyro_y, gyro_z]
        data = (time_stamp, linear_acceleration, angular_velocity)

        self._chassis_imu_deque.append(data)
        
        if self._log: print("chassis imu: acc_x:{0}, acc_y:{1}, acc_z:{2}, gyro_x:{3}, gyro_y:{4}, gyro_z:{5}".format(acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z))
    
    def _update_chassis_status(self, status_info):
        static_flag, up_hill, down_hill, on_slope, pick_up, slip_flag, impact_x, impact_y, impact_z, roll_over, hill_static = status_info
        
        if self._log: print("chassis status: static_flag:{0}, up_hill:{1}, down_hill:{2}, on_slope:{3}, "
          "pick_up:{4}, slip_flag:{5}, impact_x:{6}, impact_y:{7}, impact_z:{8}, roll_over:{9}, "
          "hill_static:{10}".format(static_flag, up_hill, down_hill, on_slope, pick_up,
                                   slip_flag, impact_x, impact_y, impact_z, roll_over, hill_static))

    def _update_chassis_esc(self, esc_data):
        if len(self._chassis_esc_data_deque) >= 100: self._chassis_esc_data_deque.popleft()
        
        speed, angle, timestamp, state = esc_data

        time_stamp = time.time()
        angles = list(angle)
        speeds = list(speed)
        data = (time_stamp, angles, speeds)

        self._chassis_esc_data_deque.append(data)

        if self._log: print("chassis esc: speed:{0}, angle:{1}, timestamp:{2}, state:{3}".format(speed, angle, timestamp, state))

    def arm_moveto(self, position):
        x, y = position
        self._arm.moveto(x, y).wait_for_completed(timeout=1)

    def gripper(self, action, power=50):
        if power not in [power for power in range(1,100)]: return False
        
        self._gripper_command = action
        self._gripper_power = power
        if action == "grab": self._gripper.close(power)
        elif action == "release": self._gripper.open(power)
        elif action == "pause": self._gripper.pause()
        else: return
    
    def chassis_move(self, x_dis, y_dis, z_angle, xy_vel=0.5, z_w=30):
        self._chassis.move(x_dis, y_dis, z_angle, xy_vel, z_w).wait_for_completed(timeout=None)
    
    def get_image(self):
        if not self._current_image_data: return False
        _, image = self._current_image_data
        return image

    def get_llava_output(self, image, prompt, temp=1.0):
        file_path = 'ep.jpg'
        cv2.imwrite(file_path, image)
        with open(file_path, 'rb') as image_file:
            files = {'image': (file_path, image_file, 'image/jpg')}
            
            text = prompt
            data={"text": text,
                  "temperature": temp}
            
            response = requests.post(self._url, files=files, data=data)
            time.sleep(0.3)
        return response.json()['response']
        
    def _core_loop(self):
        pass


if __name__ == "__main__":
    DATASET_DIR = os.path.join(HOME_PATH, "RoboMatrixDatasets", "move_to_object")

    # transfer_video_v2(os.path.join(DATASET_DIR, "videos"))
