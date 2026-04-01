#!/usr/bin/env python3
"""
NeuPAN ROS2 Launch File

Launches the NeuPAN navigation node for hexapod robot.

Usage:
    ros2 launch neupan_ros2 neupan.launch.py
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os

def generate_launch_description():
    """Generate launch description for NeuPAN"""
    
    # Declare arguments
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value='',
        description='Path to config.yaml (if empty, searches default locations)'
    )
    
    planner_config_arg = DeclareLaunchArgument(
        'planner_config',
        default_value='',
        description='Path to planner.yaml'
    )
    
    dune_checkpoint_arg = DeclareLaunchArgument(
        'dune_checkpoint',
        default_value='/home/chuyuan/Odin-Nav-Stack/NeuPAN/example/dune_train/model/dobot_hex_v2/model_5000.pth',
        description='Path to DUNE model checkpoint'
    )
    
    # NeuPAN node
    neupan_node = Node(
        package='neupan_ros2',
        executable='neupan_node',
        name='neupan_node',
        output='screen',
        parameters=[{
            'use_sim_time': False,
        }],
        remappings=[
            # Add remappings if needed
        ],
        environment={
            'PYTHONPATH': '/home/chuyuan/Odin-Nav-Stack/NeuPAN:' + 
                          os.environ.get('PYTHONPATH', '')
        }
    )
    
    # Info message
    info = LogInfo(msg='NeuPAN navigation node starting...')
    
    return LaunchDescription([
        config_file_arg,
        planner_config_arg,
        dune_checkpoint_arg,
        info,
        neupan_node,
    ])
