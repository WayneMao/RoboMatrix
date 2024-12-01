#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
# from robomatrix_server.srv import Vla
# import pdb; pdb.set_trace()
from robomatrix_interface.srv import Vla, Audio
from .resource.inference_multistage import *
import time

class VLAServiceServer(Node):
    def __init__(self, robot: RobotInference):
        super().__init__('vla_service_server')
        self.robot_vla = robot

        self.vla_server = self.create_service(Vla, 'vla_service', self.handle_vla_service)
        self.audio_server = self.create_service(Audio, 'audio_service', self.handle_audio_service)

    def handle_vla_service(self, request, response):
        self.get_logger().info(f'Received: {request.task}, {request.msg}')
        # vla task
        self.robot_vla.exec_vla_task(request.task, request.msg)

        response.msg = f'Task {request.msg} complete!'
        response.success = True
        self.get_logger().info(f'Task {request.msg} complete!')
        
        return response 
    
    def handle_audio_service(self, request, response):
        self.get_logger().info(f'Received audio task')
        # audio task
        res = self.robot_vla.exec_get_audio(request.path)
        
        response.success = True
 
        self.get_logger().info(f'Audio record!')
        
        return response  

def main(args=None):
    rclpy.init(args=args)
    # robot = RobotInference()
    robot = RobotInference(
                        node=VLAServiceServer('vla_service_server'),
                        dataset_dir=os.path.join(HOME_PATH, "RoboMatrixDatasetsDIY"), 
                        task_name="skill_model_11_12", 
                        url="http://localhost:7893/process_frame", 
                        debug=False)
    service_server = VLAServiceServer(robot)
    # robot.init_robot()
    print("RM service wait for call!")
    rclpy.spin(service_server)  # 保持节点活跃，等待请求
    rclpy.shutdown()

if __name__ == '__main__':
    main()
