#!/usr/bin/env python3
"""
NeuPAN ROS2 Node

ROS2 implementation of Neural Parallel Autonomy Navigation (NeuPAN).
Subscribes to laser scan and robot localization, publishes velocity commands.

Author: tcy1998 (Ported from ROS1 by Ruihua Han & Hongle Mo)
License: MIT
"""

import os
import sys
from math import sin, cos, atan2, sqrt
import numpy as np
import yaml
import time
from typing import Optional, List, Tuple

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from rclpy.duration import Duration

from geometry_msgs.msg import Twist, PoseStamped, Quaternion, Pose, Point
from nav_msgs.msg import Odometry, Path
from std_msgs.msg import Empty, Float32, Header
from visualization_msgs.msg import MarkerArray, Marker
from sensor_msgs.msg import LaserScan, PointCloud2
from tf2_ros import TransformListener, Buffer, TransformException
import tf2_geometry_msgs

# NeuPAN imports (need to be in PYTHONPATH)
try:
    from neupan import neupan
    from neupan.util import get_transform
except ImportError:
    print("ERROR: NeuPAN module not found. Add NeuPAN to PYTHONPATH:")
    print("  export PYTHONPATH=/home/chuyuan/Odin-Nav-Stack/NeuPAN:$PYTHONPATH")
    sys.exit(1)


class NeuPANNode(Node):
    """
    NeuPAN ROS2 Node for hexapod navigation
    
    Subscriptions:
        /scan (sensor_msgs/LaserScan): Laser scan data
        /goal (geometry_msgs/PoseStamped): Goal position
        /path (nav_msgs/Path): Initial path
        /waypoints (nav_msgs/Path): Waypoints
        /neupan/q_s (std_msgs/Float32): Tune parameter q_s
        /neupan/p_u (std_msgs/Float32): Tune parameter p_u
        
    Publications:
        /vel_cmd (geometry_msgs/Twist): Velocity command
        /neupan_plan (nav_msgs/Path): Optimized trajectory
        /neupan_ref_state (nav_msgs/Path): Reference state
        /neupan_initial_path (nav_msgs/Path): Initial path
        /arrive (std_msgs/Empty): Goal reached signal
        /dune_point_markers (MarkerArray): DUNE visualization
        /nrmp_point_markers (MarkerArray): NRMP visualization
        /robot_marker (Marker): Robot footprint
    """

    def __init__(self):
        super().__init__('neupan_node')
        
        # Load configuration
        self.load_config()
        
        # Initialize NeuPAN planner
        self.initialize_planner()
        
        # Initialize data
        self.obstacle_points: Optional[np.ndarray] = None  # (2, n)
        self.robot_state: Optional[np.ndarray] = None  # (3, 1) [x, y, theta]
        self.stop = False
        self.arrive = False
        self.last_arrive_flag = False
        
        # TF2 buffer and listener
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # QoS profiles
        self.sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Publishers
        self.vel_pub = self.create_publisher(
            Twist, self.config['topic']['cmd_vel'], 10)
        self.plan_pub = self.create_publisher(
            Path, '/neupan_plan', 10)
        self.ref_state_pub = self.create_publisher(
            Path, '/neupan_ref_state', 10)
        self.ref_path_pub = self.create_publisher(
            Path, '/neupan_initial_path', 10)
        self.arrive_pub = self.create_publisher(
            Empty, self.config['topic']['arrive'], 10)
        
        # Visualization publishers
        self.point_markers_pub_dune = self.create_publisher(
            MarkerArray, '/dune_point_markers', 10)
        self.point_markers_pub_nrmp = self.create_publisher(
            MarkerArray, '/nrmp_point_markers', 10)
        self.robot_marker_pub = self.create_publisher(
            Marker, '/robot_marker', 10)
        
        # Subscribers
        self.scan_sub = self.create_subscription(
            LaserScan, self.config['topic']['scan'],
            self.scan_callback, self.sensor_qos)
        
        self.goal_sub = self.create_subscription(
            PoseStamped, self.config['topic']['goal'],
            self.goal_callback, self.reliable_qos)
        
        self.path_sub = self.create_subscription(
            Path, self.config['topic']['path'],
            self.path_callback, self.reliable_qos)
        
        self.waypoints_sub = self.create_subscription(
            Path, self.config['topic']['waypoints'],
            self.waypoints_callback, self.reliable_qos)
        
        self.qs_sub = self.create_subscription(
            Float32, '/neupan/q_s', self.qs_callback, 10)
        
        self.pu_sub = self.create_subscription(
            Float32, '/neupan/p_u', self.pu_callback, 10)
        
        # Main control timer (50 Hz)
        self.timer = self.create_timer(0.02, self.control_loop)
        
        self.get_logger().info('NeuPAN node initialized')
        self.get_logger().info(f'  Base frame: {self.config["frame"]["base"]}')
        self.get_logger().info(f'  Map frame: {self.config["frame"]["map"]}')
        self.get_logger().info(f'  Cmd topic: {self.config["topic"]["cmd_vel"]}')
        self.get_logger().info(f'  Scan topic: {self.config["topic"]["scan"]}')
        
    def load_config(self):
        """Load configuration from YAML file"""
        # Try to find config file
        config_paths = [
            os.path.join(os.path.dirname(__file__), 'configs', 'config.yaml'),
            '/home/chuyuan/Odin-Nav-Stack/NeuPAN/neupan/ros/configs/config.yaml',
            os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml'),
        ]
        
        config_path = None
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                break
        
        if config_path is None:
            self.get_logger().error('config.yaml not found!')
            self.get_logger().error(f'Searched: {config_paths}')
            raise FileNotFoundError('config.yaml not found')
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.get_logger().info(f'Loaded config from: {config_path}')
        
        # Parse scan parameters
        self.scan_angle_range = np.array(
            self.config['scan_angle'], dtype=np.float32)
        self.scan_range = np.array(
            self.config['scan_range'], dtype=np.float32)
        
    def initialize_planner(self):
        """Initialize NeuPAN planner"""
        # Find planner config file
        planner_config_file = self.config.get('planner_config_file', 
                                               'configs/planner.yaml')
        
        planner_paths = [
            os.path.join(os.path.dirname(__file__), planner_config_file),
            '/home/chuyuan/Odin-Nav-Stack/NeuPAN/neupan/ros/configs/planner.yaml',
            os.path.join(os.path.dirname(__file__), '..', 'config', 'planner.yaml'),
        ]
        
        planner_config_path = None
        for path in planner_paths:
            if os.path.exists(path):
                planner_config_path = os.path.abspath(path)
                break
        
        if planner_config_path is None:
            self.get_logger().error('planner.yaml not found!')
            raise FileNotFoundError('planner.yaml not found')
        
        # DUNE checkpoint path
        dune_checkpoint = self.config.get('dune_checkpoint',
            'example/dune_train/model/dobot_hex_v2/model_5000.pth')
        
        # Make absolute if relative
        if not os.path.isabs(dune_checkpoint):
            dune_checkpoint = os.path.join(
                '/home/chuyuan/Odin-Nav-Stack/NeuPAN', dune_checkpoint)
        
        pan = {'dune_checkpoint': dune_checkpoint}
        
        self.get_logger().info(f'Loading DUNE model from: {dune_checkpoint}')
        
        try:
            self.neupan_planner = neupan.init_from_yaml(
                planner_config_path, pan=pan)
            self.get_logger().info('NeuPAN planner initialized successfully')
        except Exception as e:
            self.get_logger().error(f'Failed to initialize planner: {e}')
            raise
        
    def quat_to_yaw(self, quat: Quaternion) -> float:
        """Convert quaternion to yaw angle"""
        siny_cosp = 2 * (quat.w * quat.z + quat.x * quat.y)
        cosy_cosp = 1 - 2 * (quat.y * quat.y + quat.z * quat.z)
        return atan2(siny_cosp, cosy_cosp)
    
    def control_loop(self):
        """Main control loop (50 Hz)"""
        # Get robot state from TF
        try:
            transform = self.tf_buffer.lookup_transform(
                self.config['frame']['map'],
                self.config['frame']['base'],
                rclpy.time.Time(),
                timeout=Duration(seconds=0.1)
            )
            
            trans = transform.transform.translation
            rot = transform.transform.rotation
            
            x, y = trans.x, trans.y
            yaw = self.quat_to_yaw(rot)
            self.robot_state = np.array([x, y, yaw]).reshape(3, 1)
            
        except TransformException as ex:
            self.get_logger().warn(
                f'Could not transform {self.config["frame"]["base"]} to '
                f'{self.config["frame"]["map"]}: {ex}',
                throttle_duration_sec=3.0)
            return
        
        # Check if robot state is valid
        if self.robot_state is None:
            self.get_logger().warn('Waiting for robot state',
                                   throttle_duration_sec=3.0)
            return
        
        # Set initial path if needed
        if (len(self.neupan_planner.waypoints) >= 1 and 
            self.neupan_planner.initial_path is None):
            self.neupan_planner.set_initial_path_from_state(self.robot_state)
        
        # Check if initial path exists
        if self.neupan_planner.initial_path is None:
            self.get_logger().warn('Waiting for initial path',
                                   throttle_duration_sec=3.0)
            return
        
        # Publish initial path (once)
        self.ref_path_pub.publish(
            self.generate_path_msg(self.neupan_planner.initial_path))
        
        # Warn if no obstacles
        if self.obstacle_points is None:
            self.get_logger().warn(
                'No obstacle points, pure path tracking mode',
                throttle_duration_sec=5.0)
        
        # Run NeuPAN planner
        if not self.last_arrive_flag:
            t_start = time.time()
        
        action, info = self.neupan_planner(
            self.robot_state, self.obstacle_points)
        
        if not self.last_arrive_flag:
            t_end = time.time()
            self.get_logger().info(
                f'Planning time: {(t_end - t_start)*1000:.1f} ms',
                throttle_duration_sec=1.0)
        
        self.stop = info['stop']
        self.arrive = info['arrive']
        
        # Publish arrive signal
        if info['arrive'] and not self.last_arrive_flag:
            self.arrive_pub.publish(Empty())
            self.get_logger().info('Arrived at target!')
        
        self.last_arrive_flag = info['arrive']
        
        # Publish trajectory and velocity
        self.plan_pub.publish(
            self.generate_path_msg(info['opt_state_list']))
        self.ref_state_pub.publish(
            self.generate_path_msg(info['ref_state_list']))
        
        if not info['arrive'] or not self.last_arrive_flag:
            self.vel_pub.publish(self.generate_twist_msg(action))
        
        # Publish visualizations
        self.point_markers_pub_dune.publish(
            self.generate_dune_points_markers_msg())
        self.point_markers_pub_nrmp.publish(
            self.generate_nrmp_points_markers_msg())
        self.robot_marker_pub.publish(
            self.generate_robot_marker_msg())
        
        # Warn if stopped
        if info['stop']:
            min_dist = self.neupan_planner.min_distance.detach().item()
            thresh = self.neupan_planner.collision_threshold
            self.get_logger().warn(
                f'STOP: min_distance={min_dist:.3f}, threshold={thresh:.3f}',
                throttle_duration_sec=0.5)
    
    def scan_callback(self, scan_msg: LaserScan):
        """Process laser scan data"""
        if self.robot_state is None:
            return
        
        ranges = np.array(scan_msg.ranges)
        angles = np.linspace(
            scan_msg.angle_min, scan_msg.angle_max, len(ranges))
        
        if self.config.get('flip_angle', False):
            angles = np.flip(angles)
        
        points = []
        downsample = self.config.get('scan_downsample', 1)
        
        for i in range(len(ranges)):
            distance = ranges[i]
            angle = angles[i]
            
            if (i % downsample == 0 and
                self.scan_range[0] <= distance <= self.scan_range[1] and
                self.scan_angle_range[0] < angle < self.scan_angle_range[1]):
                
                point = np.array([
                    [distance * cos(angle)],
                    [distance * sin(angle)]
                ])
                
                # Transform to map frame if needed
                try:
                    # Get transform from lidar to base
                    transform = self.tf_buffer.lookup_transform(
                        self.config['frame']['base'],
                        self.config['frame']['lidar'],
                        rclpy.time.Time(),
                        timeout=Duration(seconds=0.05)
                    )
                    
                    trans = transform.transform.translation
                    rot = transform.transform.rotation
                    yaw_offset = self.quat_to_yaw(rot)
                    
                    # Apply transform
                    rot_matrix = np.array([
                        [cos(yaw_offset), -sin(yaw_offset)],
                        [sin(yaw_offset), cos(yaw_offset)]
                    ])
                    point = rot_matrix @ point + np.array([
                        [trans.x], [trans.y]])
                    
                except TransformException:
                    pass  # Use point as-is if transform fails
                
                # Transform to map frame
                robot_yaw = self.robot_state[2, 0]
                rot_matrix = np.array([
                    [cos(robot_yaw), -sin(robot_yaw)],
                    [sin(robot_yaw), cos(robot_yaw)]
                ])
                
                point_map = rot_matrix @ point + self.robot_state[:2]
                points.append(point_map)
        
        if len(points) > 0:
            self.obstacle_points = np.hstack(points)  # (2, n)
        else:
            self.obstacle_points = None
    
    def goal_callback(self, msg: PoseStamped):
        """Handle goal position"""
        x = msg.pose.position.x
        y = msg.pose.position.y
        yaw = self.quat_to_yaw(msg.pose.orientation)
        
        goal = np.array([x, y, yaw]).reshape(3, 1)
        self.neupan_planner.set_initial_path_from_goal(goal)
        
        self.get_logger().info(f'Goal received: ({x:.2f}, {y:.2f}, {yaw:.2f})')
        self.last_arrive_flag = False
    
    def path_callback(self, msg: Path):
        """Handle initial path"""
        path_array = []
        for pose in msg.poses:
            x = pose.pose.position.x
            y = pose.pose.position.y
            yaw = self.quat_to_yaw(pose.pose.orientation)
            path_array.append([x, y, yaw])
        
        if len(path_array) > 0:
            path = np.array(path_array).T  # (3, n)
            self.neupan_planner.set_initial_path(path)
            self.get_logger().info(f'Path received: {len(path_array)} points')
            self.last_arrive_flag = False
    
    def waypoints_callback(self, msg: Path):
        """Handle waypoints"""
        waypoints = []
        for pose in msg.poses:
            x = pose.pose.position.x
            y = pose.pose.position.y
            waypoints.append([x, y])
        
        if len(waypoints) > 0:
            self.neupan_planner.set_waypoints(np.array(waypoints).T)
            self.get_logger().info(f'Waypoints received: {len(waypoints)} points')
            self.last_arrive_flag = False
    
    def qs_callback(self, msg: Float32):
        """Update q_s parameter"""
        self.neupan_planner.update_adjust_parameters(q_s=float(msg.data))
        self.get_logger().info(f'Updated q_s to {msg.data}')
    
    def pu_callback(self, msg: Float32):
        """Update p_u parameter"""
        self.neupan_planner.update_adjust_parameters(p_u=float(msg.data))
        self.get_logger().info(f'Updated p_u to {msg.data}')
    
    def generate_twist_msg(self, action: np.ndarray) -> Twist:
        """Generate Twist message from action array"""
        twist = Twist()
        twist.linear.x = float(action[0, 0])
        twist.angular.z = float(action[1, 0])
        return twist
    
    def generate_path_msg(self, states: Optional[np.ndarray]) -> Path:
        """Generate Path message from state array (3, n)"""
        path = Path()
        path.header.stamp = self.get_clock().now().to_msg()
        path.header.frame_id = self.config['frame']['map']
        
        if states is None or states.size == 0:
            return path
        
        for i in range(states.shape[1]):
            pose_stamped = PoseStamped()
            pose_stamped.header = path.header
            pose_stamped.pose.position.x = float(states[0, i])
            pose_stamped.pose.position.y = float(states[1, i])
            pose_stamped.pose.position.z = 0.0
            
            # Convert yaw to quaternion
            yaw = float(states[2, i])
            pose_stamped.pose.orientation.w = cos(yaw / 2.0)
            pose_stamped.pose.orientation.z = sin(yaw / 2.0)
            
            path.poses.append(pose_stamped)
        
        return path
    
    def generate_dune_points_markers_msg(self) -> MarkerArray:
        """Generate visualization markers for DUNE points"""
        # TODO: Implement visualization (copy from ROS1 version)
        return MarkerArray()
    
    def generate_nrmp_points_markers_msg(self) -> MarkerArray:
        """Generate visualization markers for NRMP points"""
        # TODO: Implement visualization (copy from ROS1 version)
        return MarkerArray()
    
    def generate_robot_marker_msg(self) -> Marker:
        """Generate robot footprint marker"""
        # TODO: Implement robot footprint visualization
        return Marker()


def main(args=None):
    """Main entry point"""
    rclpy.init(args=args)
    
    try:
        node = NeuPANNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
