from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

import os
home_path = os.path.expanduser("~")

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('name', default_value='mobile_manipulation', description='task name'),
        DeclareLaunchArgument('idx', default_value='0', description='episode index'),
        DeclareLaunchArgument('dir', default_value=home_path+'/RoboMatrixDatasets', description='vedio save directory'),
        Node(
            package='joystick_driver',
            executable='xbox_driver',
            name='xbox_driver'
        ),
        Node(
            package='robomaster_ros',
            executable='teleoperation',
            name='teleoperation'
        ),
        Node(
            package='robomaster_ros',
            executable='data_collection',
            name='data_collection',
            output='screen',
            parameters=[{
                'task_name'  : LaunchConfiguration('name'),
                "episode_idx": LaunchConfiguration('idx'),
                "save_dir"   : LaunchConfiguration('dir'),
            }]
        ),
    ])
