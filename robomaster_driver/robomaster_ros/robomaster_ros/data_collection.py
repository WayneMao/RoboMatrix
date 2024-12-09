import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from cv_bridge import CvBridge

from robomaster_msgs.msg import ChassisAttitute, ChassisPosition, ChassisEsc, ChassisIMU
from robomaster_msgs.msg import GripperStatus
from robomaster_msgs.msg import ServoStatus
from robomaster_msgs.msg import RoboticArmPosition

from collections import deque
from queue import Queue

import os, time
import json
import cv2
import threading


FPS = 30
TASK_PROMPT = "None."


class DataCollectionNode(Node):

    def __init__(self) -> None:
        super().__init__('rm_data_collection')

        # save path params
        from datetime import datetime
        now = datetime.now().date().strftime("%Y-%m-%d")
        self.declare_parameter("task_name", now).value

        self.declare_parameter("episode_idx", 0).value
        
        home_path = os.path.expanduser("~")
        self.declare_parameter("save_dir", home_path+'/RoboMatrixDatasets').value

        self._task_name: str = self.get_parameter("task_name").get_parameter_value().string_value
        self._episode_idx: str = self.get_parameter("episode_idx").get_parameter_value().integer_value
        self._save_dir: str = self.get_parameter("save_dir").get_parameter_value().string_value
        self.get_logger().info(f'task_name: {self._task_name}')
        self.get_logger().info(f'episode_idx: {self._episode_idx}')
        self.get_logger().info(f'save_dir: {self._save_dir}')
        
        self._initialize_parameters()
        
        # visual
        self._sub_image = self.create_subscription(Image, "/camera/raw/image", self._image_cb, 1000)
        self._image_deque = deque()
        self._image_queue = Queue(maxsize=2000)

        # subscribe robotic arm topic to ger end effector position
        self._sub_arm_position = self.create_subscription(RoboticArmPosition, "/arm/raw/position", self._arm_position_cb, 1000)
        self._arm_position_deque = deque()

        # subscribe servo topic to get joint value
        self._sub_servo_value = self.create_subscription(ServoStatus, "/servo/raw/value", self._servo_value_cb, 1000)
        self._servo_value_deque = deque()

        # subscribe gripper topic to get status
        self._sub_gripper_status = self.create_subscription(GripperStatus, "/gripper/raw/status", self._gripper_status_cb, 1000)
        self._gripper_status_deque = deque()

        # subscribe chassis topic to get raw data
        self._sub_chassis_esc = self.create_subscription(ChassisEsc, "/chassis/raw/esc", self._chassis_esc_cb, 1000)
        self._chassis_esc_data_deque = deque()
        self._sub_chassis_position = self.create_subscription(ChassisPosition, "/chassis/raw/position", self._chassis_position_cb, 1000)
        self._chassis_position_deque = deque()
        self._sub_chassis_attitute = self.create_subscription(ChassisAttitute, "/chassis/raw/attitute", self._chassis_attitute_cb, 1000)
        self._chassis_attitute_deque = deque()
        self._sub_chassis_imu = self.create_subscription(ChassisIMU, "/chassis/raw/imu", self._chassis_imu_cb, 1000)
        self._chassis_imu_deque = deque()

        self._sub_action = self.create_subscription(Bool, '/data_collection_start', self._action_cb, 10)

        self._cv_bridge = CvBridge()

        self._rate = 30
        self._max_frame_num = 10000

        self._can_action = False

        self.thread = threading.Thread(target=self._collect)
        self.thread.start()
        self._lock = threading.Lock()

        self.end = False
    
    def _initialize_parameters(self):
        # self._file_name = f'episode_{self._episode_idx}'
        self._file_name = f"{self._task_name}_{self._episode_idx}"
        # 数据集文件夹
        if not os.path.exists(self._save_dir): os.mkdir(self._save_dir)
        # 任务文件夹
        self._task_dir = os.path.join(self._save_dir, self._task_name)
        if not os.path.exists(self._task_dir): os.mkdir(self._task_dir)
        # 视频文件夹
        self._video_dir = os.path.join(self._task_dir, "videos")
        if not os.path.exists(self._video_dir): os.mkdir(self._video_dir)
        # 标注文件夹
        self._anno_dir = os.path.join(self._task_dir, "annotations")
        if not os.path.exists(self._anno_dir): os.mkdir(self._anno_dir)

    def _image_cb(self, msg: Image):
        try:
            if len(self._image_deque) >= 1: self._image_deque.popleft()
        except: pass
        if not self._can_action: return
        time_stamp = self.to_sec(msg.header.stamp)
        image = self._cv_bridge.imgmsg_to_cv2(msg, 'passthrough')
        data = (time_stamp, image)
        self._image_deque.append(data)
    
    def _arm_position_cb(self, msg: RoboticArmPosition):
        if len(self._arm_position_deque) >= 100: self._arm_position_deque.popleft()
        time_stamp = self.to_sec(msg.header.stamp)
        x, y = msg.x, msg.y
        data = (time_stamp, [x, y])
        self._arm_position_deque.append(data)
    
    def _servo_value_cb(self, msg: ServoStatus):
        if len(self._servo_value_deque) >= 100: self._servo_value_deque.popleft()
        time_stamp = self.to_sec(msg.header.stamp)
        values = [msg.servo_0.value, msg.servo_1.value]
        speeds = [msg.servo_0.speed, msg.servo_1.speed]
        data = (time_stamp, values, speeds)
        self._servo_value_deque.append(data)
    
    def _gripper_status_cb(self, msg: GripperStatus):
        if len(self._gripper_status_deque) >= 100: self._gripper_status_deque.popleft()
        time_stamp = self.to_sec(msg.header.stamp)
        gripper_status = msg.status
        gripper_power = msg.power
        gripper_action = msg.action
        data = (time_stamp, gripper_status, gripper_power, gripper_action)
        self._gripper_status_deque.append(data)

    def _chassis_esc_cb(self, msg: ChassisEsc):
        if len(self._chassis_esc_data_deque) >= 100: self._chassis_esc_data_deque.popleft()
        time_stamp = self.to_sec(msg.header.stamp)
        angles = [msg.front_right.angle, msg.front_left.angle, msg.back_left.angle, msg.back_right.angle]
        speeds = [msg.front_right.speed, msg.front_left.speed, msg.back_left.speed, msg.back_right.speed]
        data = (time_stamp, angles, speeds)
        self._chassis_esc_data_deque.append(data)

    def _chassis_position_cb(self, msg: ChassisPosition):
        if len(self._chassis_position_deque) >= 100: self._chassis_position_deque.popleft()
        time_stamp = self.to_sec(msg.header.stamp)
        position = [round(msg.x * 1000, 2), round(msg.y * 1000, 2)]
        data = (time_stamp, position)
        self._chassis_position_deque.append(data)
    
    def _chassis_attitute_cb(self, msg: ChassisAttitute):
        if len(self._chassis_attitute_deque) >= 100: self._chassis_attitute_deque.popleft()
        time_stamp = self.to_sec(msg.header.stamp)
        attitute = [round(msg.roll, 2), round(msg.pitch, 2), round(msg.yaw, 2)]
        data = (time_stamp, attitute)
        self._chassis_attitute_deque.append(data)
    
    def _chassis_imu_cb(self, msg: ChassisIMU):
        if len(self._chassis_imu_deque) >= 100: self._chassis_imu_deque.popleft()
        time_stamp = self.to_sec(msg.header.stamp)
        linear_acceleration = [msg.acc_x, msg.acc_y, msg.acc_z]
        angular_velocity = [msg.gyro_x, msg.gyro_y, msg.gyro_z]
        data = (time_stamp, linear_acceleration, angular_velocity)
        self._chassis_imu_deque.append(data)

    def _action_cb(self, msg: Bool):
        self._can_action = msg.data
    
    def _get_frame(self) -> bool:
        if not self._image_deque:
            # self.get_logger().error("image deque is empty")
            return False
        
        tolerance = 0.05

        frame_time = self._image_deque[-1][0] - tolerance # 图像缓存中最新的数据作为标准

        # get image
        while self._image_deque:
            time_stamp, image = self._image_deque.popleft()
            if time_stamp >= frame_time: break
        else: pass

        # get chassis position
        while self._chassis_position_deque:
            time_stamp, chassis_position = self._chassis_position_deque.popleft()
            if time_stamp >= frame_time: break
        else:
            self.get_logger().error("get chassis position fail")
            return False

        # get chassis attitute
        while self._chassis_attitute_deque:
            time_stamp, chassis_attitute = self._chassis_attitute_deque.popleft()
            if time_stamp >= frame_time: break
        else:
            self.get_logger().error("get chassis attitute fail")
            return False

        # get arm position
        while self._arm_position_deque:
            time_stamp, end_position = self._arm_position_deque.popleft()
            if time_stamp >= frame_time: break
        else:
            self.get_logger().error("get arm position fail")
            return False

        # get gripper status
        while self._gripper_status_deque:
            time_stamp, gripper_status, gripper_power, gripper_command = self._gripper_status_deque.popleft()
            gripper_action = [gripper_command, gripper_power]
            if time_stamp >= frame_time: break
        else:
            self.get_logger().error("get gripper status fail")
            return False

        frame_dict = {
            "image": image,
            "arm_position": end_position,
            "gripper_status": gripper_status,
            "gripper_action": gripper_action,
            "chassis_position": chassis_position,
            "chassis_attitute": chassis_attitute,
        }

        return frame_dict
    
    def _collect(self):
        visual = []
        observations = {
            'arm_position': [],
            'gripper_status': [],
            'gripper_action': [],
            "chassis_position": [],
            "chassis_attitute": [],
            }
        frame_count, fail_count= 0, 0

        while rclpy.ok():
            self.get_logger().info("Wait to start data collection")
            while rclpy.ok() and not self._can_action: pass
            self.get_logger().info("start collect")

            start_time = None
            while rclpy.ok() and frame_count <= self._max_frame_num and self._can_action:
                fps = int(1 / (time.time() - start_time)) if start_time else 0
                start_time = time.time()
                
                frame_dict = self._get_frame()
                if not frame_dict:
                    fail_count += 1
                    continue
                else: frame_count += 1

                if fps <= self._rate:
                    self.get_logger().info(f"Get a frame {frame_count} / {self._max_frame_num} ({fps} FPS).")
                else:
                    self.get_logger().warn(f"Get a frame {frame_count} / {self._max_frame_num} ({fps} FPS).")

                for name, data in frame_dict.items():
                    if name == "image":
                        data = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
                        visual.append(data)
                    elif name in observations.keys(): observations[name].append(data)
                
                if not rclpy.ok(): exit(-1)

                time.sleep(max(0, 1 / self._rate - (time.time() - start_time))) # 控制采样频率
            
            self.get_logger().warn(f"Fail count {fail_count}")
            # self._save_video(frame_count, visual, FPS)
            self._save_video_v2(visual, FPS)
            self._save_annotation(frame_count, observations)

            self._can_action = False
            break

        self.end = True

    def _save_video(self, frame_count, img_list, fps):
        if frame_count == 0:
            self.get_logger().error(f"No frame to save")
            return
        
        video_path = os.path.join(self._video_dir, f'{self._file_name}.mp4')

        height, width, _ = img_list[0].shape
        out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
        for t in range(frame_count):
            img = img_list[t]
            out.write(img)
        out.release()
        self.get_logger().info(f"Save video to: {video_path}")
    
    def _save_video_v2(self, images, fps):
        from moviepy.editor import ImageSequenceClip
        clip = ImageSequenceClip(images, fps=fps)
        video_path = os.path.join(self._video_dir, f'{self._file_name}.mp4')
        clip.write_videofile(video_path, codec='libx264')
        self.get_logger().info(f"Save video to: {video_path}")
    
    def _save_annotation(self, frame_count, observations):
        if frame_count == 0:
            self.get_logger().error(f"No annotation to save")
            return

        video_annotation = []

        for index in range(frame_count):
            frame_annotation = {}

            # frame_annotation['stream'] = f"{self._task_name}/videos/{self._file_name}.mp4" # video name
            frame_annotation['stream'] = f"{self._file_name}.mp4" # video name
            frame_annotation['frame_inds'] = [index] # frame index

            frame_annotation["observations"] = {}
            for key, data in observations.items():
                frame_annotation["observations"][key] = data[index]
            
            conversation = []
            conv_human, conv_agent = {}, {}
            conv_human['from'] = 'human'
            conv_human['value'] = 'prompt'
            conv_agent['from'] = 'gpt'
            conv_agent['value'] = 'tokens'
            conversation.append(conv_human)
            conversation.append(conv_agent)
            frame_annotation['conversations'] = conversation

            video_annotation.append(frame_annotation)
        
        json_path = os.path.join(self._anno_dir, f'{self._file_name}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(video_annotation, f, ensure_ascii=False, indent=4)
        self.get_logger().info(f"Save annotation to: {json_path}")

    def to_sec(self, frame_time):
        sec = frame_time.sec
        nanosec = frame_time.nanosec
        return sec + nanosec / 1e9

def main(args=None):
    rclpy.init(args=args)

    node = DataCollectionNode()
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=1)
        if node.end: break

    node.destroy_node()
    rclpy.shutdown()
