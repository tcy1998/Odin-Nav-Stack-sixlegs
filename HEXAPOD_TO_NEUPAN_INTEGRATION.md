# Hexapod to NeuPAN Integration Guide

**Robot:** Dobot Mini Hex V2  
**Date:** 2026-03-31  
**Purpose:** Connect hexapod sensors and control to NeuPAN navigation

---

## 📡 Available Data from Hexapod

### 1. **Robot State** (ROS2 Topic)

**Topic:** `/robot_state`  
**Type:** `custom_msg/RobotState`  
**Rate:** ~50 Hz  
**Framework:** ROS2

**Message Contents:**
```yaml
header: std_msgs/Header
control_cmd: uint8                 # Current control command

# Joint states (18 DOF)
jtau_leg[18]: float32             # Joint torques
jvel_leg[18]: float32             # Joint velocities
jpos_leg[18]: float32             # Joint positions
jerror[18]: float32               # Joint errors
jtau_leg_des[18]: float32         # Desired torques
jvel_leg_des[18]: float32         # Desired velocities
jpos_leg_des[18]: float32         # Desired positions

# Body state
pos_body[3]: float32              # Body position [x, y, z]
vel_body[3]: float32              # Body velocity [vx, vy, vz]
acc_body[3]: float32              # Body acceleration
ori_body[4]: float32              # Body orientation (quaternion)
omega_body[3]: float32            # Angular velocity

# Other
temp[12]: float32                 # Temperature sensors
                                  # temp[10] = robot FSM state
```

**Robot State Machine:**
- `0` = PASSIVE
- `1` = STAND_DOWN
- `2` = STAND_UP
- `3` = BALANCE_STAND
- `4` = WALK (must be in this state to move)

---

### 2. **Lidar Data** (ROS2 Topic)

**Topic:** `/livox/lidar` (likely)  
**Type:** `custom_msg/LivoxPointcloud` (custom) or `sensor_msgs/PointCloud2` (standard)  
**Rate:** ~10-20 Hz  
**Framework:** ROS2

**LivoxPointcloud Message:**
```yaml
header: std_msgs/Header
timebase: uint64
point_num: uint32                  # Number of points
lidar_id: uint8
rsvd[3]: uint8                     # Reserved

points[]: CustomPoint[]
  # Each point contains:
  offset_time: uint32
  x, y, z: float32                 # 3D position
  reflectivity: uint8
  tag: uint8
  line: uint8
```

**Data Format:** 3D pointcloud (x, y, z coordinates)

---

### 3. **Camera Data** (ROS2 Topic)

**Package:** `realsense_camera_node`  
**Topics (expected):**
- `/camera/color/image_raw` - RGB image
- `/camera/depth/image_raw` - Depth image
- `/camera/color/camera_info` - Camera calibration

**Type:** Intel RealSense (D435/D455)  
**Framework:** ROS2

---

## 🔌 Control Interface to Hexapod

### **Velocity Command** (ROS2 Topic)

**Topic:** `/vel_cmd`  
**Type:** `geometry_msgs/Twist`  
**Rate:** ~50 Hz (recommended)  
**Framework:** ROS2

**Message Structure:**
```yaml
linear:
  x: float64     # Forward/backward velocity (m/s)
  y: float64     # Left/right velocity (m/s)
  z: float64     # Up/down (not used for ground robot)

angular:
  x: float64     # Roll (not used)
  y: float64     # Pitch (not used)
  z: float64     # Yaw rotation (rad/s)
```

**Velocity Limits:**
```yaml
linear.x: ±0.2 m/s      # After 0.5× scaling
linear.y: ±0.16 m/s     # After 0.4× scaling (omnidirectional)
angular.z: ±0.28 rad/s  # After 0.35× scaling
```

---

### **State Control** (ROS2 Topic)

**Topic:** `/robot_cmd`  
**Type:** `custom_msg/RobotCommand`  
**Framework:** ROS2

**Usage:** Switch robot modes (PASSIVE → STAND_UP → WALK)

---

## 🌉 ROS1 ↔ ROS2 Bridge Required

### Why Bridge is Needed

```
NeuPAN (ROS1 Noetic)  ←→  Bridge  ←→  Hexapod (ROS2)
     /cmd_vel                           /vel_cmd
     /scan                              /livox/lidar
     /odom                              /robot_state
```

**Problem:** NeuPAN runs on ROS1, hexapod runs on ROS2

---

## ✅ Integration Options

### **Option 1: ros1_bridge (Quick Setup)**

**Install:**
```bash
# On Ubuntu 20.04 with ROS Noetic + ROS2 Foxy/Humble
sudo apt install ros-noetic-ros1-bridge
```

**Run bridge:**
```bash
# Terminal 1: Source both ROS versions
source /opt/ros/noetic/setup.bash
source /opt/ros/foxy/setup.bash  # or humble
export ROS_MASTER_URI=http://localhost:11311

# Start dynamic bridge (auto-detects topics)
ros2 run ros1_bridge dynamic_bridge
```

**Topic mapping:**
- ROS1 `/scan` ↔ ROS2 `/scan` (need converter from pointcloud)
- ROS1 `/cmd_vel` ↔ ROS2 `/vel_cmd` (need remapper)
- ROS1 `/odom` ↔ ROS2 `/robot_state` (need converter)

---

### **Option 2: Custom Bridge Node (Recommended)**

Create a dedicated bridge node that handles hexapod-specific data conversion.

**File:** `ros_ws/src/hexapod_bridge/src/hexapod_neupan_bridge.py`

```python
#!/usr/bin/env python3
"""
Bridge between NeuPAN (ROS1) and Hexapod (ROS2)
Handles data conversion and topic remapping
"""

import rclpy
from rclpy.node import Node as ROS2Node
import rospy
from std_msgs.msg import Header
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan, PointCloud2
from nav_msgs.msg import Odometry
from custom_msg.msg import RobotState

# ROS2 imports
import sensor_msgs_py.point_cloud2 as pc2
import numpy as np
from math import sqrt, atan2


class HexapodNeuPANBridge:
    """
    Bridges ROS1 NeuPAN with ROS2 Hexapod
    
    ROS1 Subscribers:
      - /cmd_vel (from NeuPAN) → ROS2 /vel_cmd (to hexapod)
      
    ROS2 Subscribers:
      - /livox/lidar (pointcloud) → ROS1 /scan (laserscan)
      - /robot_state → ROS1 /odom (odometry)
    """
    
    def __init__(self):
        # Initialize ROS1 node
        rospy.init_node('hexapod_bridge')
        
        # Initialize ROS2 node
        rclpy.init()
        self.ros2_node = ROS2Node('hexapod_bridge_ros2')
        
        # ROS1 Publishers (to NeuPAN)
        self.ros1_scan_pub = rospy.Publisher('/scan', LaserScan, queue_size=10)
        self.ros1_odom_pub = rospy.Publisher('/odom', Odometry, queue_size=10)
        
        # ROS1 Subscribers (from NeuPAN)
        rospy.Subscriber('/cmd_vel', Twist, self.cmd_vel_callback)
        
        # ROS2 Publishers (to Hexapod)
        self.ros2_vel_pub = self.ros2_node.create_publisher(
            Twist, '/vel_cmd', 10)
        
        # ROS2 Subscribers (from Hexapod)
        self.ros2_node.create_subscription(
            PointCloud2, '/livox/lidar', self.pointcloud_callback, 10)
        self.ros2_node.create_subscription(
            RobotState, '/robot_state', self.robot_state_callback, 10)
        
        # State variables
        self.robot_position = [0.0, 0.0, 0.0]  # x, y, theta
        
        rospy.loginfo("Hexapod-NeuPAN Bridge initialized")
    
    def cmd_vel_callback(self, msg):
        """
        ROS1 /cmd_vel → ROS2 /vel_cmd
        Forward velocity commands from NeuPAN to hexapod
        """
        # Simply forward the message (same Twist type)
        self.ros2_vel_pub.publish(msg)
        rospy.loginfo_throttle(1.0, f"Vel cmd: x={msg.linear.x:.2f} y={msg.linear.y:.2f} z={msg.angular.z:.2f}")
    
    def pointcloud_callback(self, cloud_msg):
        """
        ROS2 /livox/lidar (PointCloud2) → ROS1 /scan (LaserScan)
        Convert 3D pointcloud to 2D laser scan
        """
        # Convert PointCloud2 to numpy array
        points = []
        for point in pc2.read_points(cloud_msg, skip_nans=True):
            x, y, z = point[:3]
            # Filter by height (only obstacles at robot height)
            if 0.0 < z < 0.5:  # 0-50cm height
                points.append([x, y])
        
        if len(points) == 0:
            return
        
        points = np.array(points)
        
        # Convert to polar coordinates
        ranges_data = np.linalg.norm(points, axis=1)
        angles = np.arctan2(points[:, 1], points[:, 0])
        
        # Create LaserScan message
        scan = LaserScan()
        scan.header = cloud_msg.header
        scan.header.frame_id = "livox_frame"
        
        # Scan parameters (±90 degrees, 360 rays)
        scan.angle_min = -1.5707  # -90°
        scan.angle_max = 1.5707   # +90°
        scan.angle_increment = (scan.angle_max - scan.angle_min) / 360
        scan.range_min = 0.2
        scan.range_max = 10.0
        
        # Initialize ranges array
        num_rays = int((scan.angle_max - scan.angle_min) / scan.angle_increment)
        scan.ranges = [float('inf')] * num_rays
        
        # Fill in measured ranges
        for i, (angle, distance) in enumerate(zip(angles, ranges_data)):
            if scan.angle_min <= angle <= scan.angle_max:
                ray_index = int((angle - scan.angle_min) / scan.angle_increment)
                if 0 <= ray_index < num_rays:
                    # Keep minimum distance for each ray
                    if distance < scan.ranges[ray_index]:
                        scan.ranges[ray_index] = distance
        
        # Publish to ROS1
        self.ros1_scan_pub.publish(scan)
    
    def robot_state_callback(self, state_msg):
        """
        ROS2 /robot_state → ROS1 /odom
        Convert hexapod state to odometry
        """
        odom = Odometry()
        odom.header.stamp = rospy.Time.now()
        odom.header.frame_id = "map"
        odom.child_frame_id = "link_trunk"
        
        # Position from state message
        odom.pose.pose.position.x = state_msg.pos_body[0]
        odom.pose.pose.position.y = state_msg.pos_body[1]
        odom.pose.pose.position.z = state_msg.pos_body[2]
        
        # Orientation (quaternion)
        odom.pose.pose.orientation.x = state_msg.ori_body[0]
        odom.pose.pose.orientation.y = state_msg.ori_body[1]
        odom.pose.pose.orientation.z = state_msg.ori_body[2]
        odom.pose.pose.orientation.w = state_msg.ori_body[3]
        
        # Velocity
        odom.twist.twist.linear.x = state_msg.vel_body[0]
        odom.twist.twist.linear.y = state_msg.vel_body[1]
        odom.twist.twist.linear.z = state_msg.vel_body[2]
        
        # Angular velocity
        odom.twist.twist.angular.x = state_msg.omega_body[0]
        odom.twist.twist.angular.y = state_msg.omega_body[1]
        odom.twist.twist.angular.z = state_msg.omega_body[2]
        
        self.ros1_odom_pub.publish(odom)
    
    def spin(self):
        """Run both ROS1 and ROS2 event loops"""
        import threading
        
        # ROS2 spin in separate thread
        ros2_thread = threading.Thread(
            target=lambda: rclpy.spin(self.ros2_node),
            daemon=True
        )
        ros2_thread.start()
        
        # ROS1 spin in main thread
        rospy.spin()


if __name__ == '__main__':
    bridge = HexapodNeuPANBridge()
    bridge.spin()
```

---

### **Option 3: Full ROS2 Migration** (Long-term)

Migrate entire navigation stack to ROS2:
- Convert NeuPAN ROS1 code to ROS2
- Use ROS2 nav2 stack
- Direct integration without bridge
- Better performance, no bridge overhead

**Pros:** Clean architecture, better performance  
**Cons:** Significant development effort

---

## 🚀 Quick Start Integration

### **Step 1: Verify Hexapod Topics**

```bash
# On hexapod machine (ROS2)
ros2 topic list

# Expected topics:
#   /robot_state
#   /robot_cmd
#   /vel_cmd
#   /livox/lidar or /livox/scan

# Check topic rates
ros2 topic hz /robot_state
ros2 topic hz /livox/lidar

# Echo robot state
ros2 topic echo /robot_state --field temp[10]  # Check FSM state
```

---

### **Step 2: Test Velocity Control**

```bash
# Make sure robot is in WALK mode first

# Test forward motion
ros2 topic pub /vel_cmd geometry_msgs/Twist \
  '{linear: {x: 0.1, y: 0, z: 0}, angular: {x: 0, y: 0, z: 0}}' \
  --once

# Test rotation
ros2 topic pub /vel_cmd geometry_msgs/Twist \
  '{linear: {x: 0, y: 0, z: 0}, angular: {x: 0, y: 0, z: 0.2}}' \
  --once

# Stop
ros2 topic pub /vel_cmd geometry_msgs/Twist \
  '{linear: {x: 0, y: 0, z: 0}, angular: {x: 0, y: 0, z: 0}}' \
  --once
```

---

### **Step 3: Convert Pointcloud to LaserScan**

If hexapod publishes PointCloud2, convert to LaserScan:

```bash
# Install converter
sudo apt install ros-<distro>-pointcloud-to-laserscan

# Run converter
ros2 run pointcloud_to_laserscan pointcloud_to_laserscan_node \
  --ros-args \
  -r cloud_in:=/livox/lidar \
  -r scan:=/scan \
  -p target_frame:=livox_frame \
  -p min_height:=0.0 \
  -p max_height:=0.5 \
  -p angle_min:=-1.5707 \
  -p angle_max:=1.5707 \
  -p range_min:=0.2 \
  -p range_max:=10.0
```

---

### **Step 4: Setup ROS1-ROS2 Bridge**

```bash
# Terminal 1: Start hexapod (ROS2)
cd dobot_six_leg
# ... launch hexapod nodes ...

# Terminal 2: Start bridge
source /opt/ros/noetic/setup.bash
source /opt/ros/foxy/setup.bash
ros2 run ros1_bridge dynamic_bridge

# Terminal 3: Start NeuPAN (ROS1)
source ~/Odin-Nav-Stack/ros_ws/devel/setup.bash
roslaunch map_planner whole.launch

# Terminal 4: Test navigation
rostopic pub /move_base_simple/goal geometry_msgs/PoseStamped \
  '{header: {frame_id: "map"}, pose: {position: {x: 2.0, y: 0, z: 0}}}'
```

---

## 📊 Data Flow Summary

```
┌─────────────────────────┐
│   Hexapod (ROS2)        │
│                         │
│  /livox/lidar          │─┐
│  /robot_state          │─┤
│  /vel_cmd              │◄┤
└─────────────────────────┘ │
                            │
                            │ Bridge
                            │ (ROS1↔ROS2)
                            │
┌─────────────────────────┐ │
│   NeuPAN (ROS1)         │ │
│                         │ │
│  /scan                 │◄┘
│  /odom                 │◄─
│  /cmd_vel              │─►
└─────────────────────────┘
```

---

## ✅ Checklist

### Before Integration
- [ ] Hexapod responds to `/vel_cmd` commands
- [ ] Lidar publishes data (`/livox/lidar` or `/livox/scan`)
- [ ] Robot state publishes at ~50 Hz
- [ ] TF tree correct (map → link_trunk → livox_frame)

### After Bridge Setup
- [ ] `/scan` topic visible in ROS1
- [ ] `/cmd_vel` forwarded to `/vel_cmd`
- [ ] NeuPAN receives scan data
- [ ] Robot moves in response to NeuPAN commands
- [ ] Collision avoidance works

---

## 🔧 Troubleshooting

**Problem:** No lidar data in ROS1  
**Solution:** Check pointcloud-to-laserscan converter is running

**Problem:** Robot doesn't move  
**Solution:** Ensure robot is in WALK state (temp[10] == 4)

**Problem:** Bridge drops messages  
**Solution:** Increase QoS buffer sizes, check network latency

**Problem:** TF lookup errors  
**Solution:** Publish static TF between ROS1 and ROS2 frames

---

## 📚 Next Steps

1. ✅ **Training complete** - model_5000.pth ready
2. ⏳ **Build bridge** - Choose Option 1 or 2 above
3. ⏳ **Test integration** - Verify data flow
4. ⏳ **Tune parameters** - Adjust speeds, thresholds
5. ⏳ **Test navigation** - Send goals, verify obstacle avoidance

**Estimated time:** 4-8 hours for initial integration

---

**Version:** 1.0  
**Date:** 2026-03-31  
**Repository:** https://github.com/tcy1998/Odin-Nav-Stack-sixlegs
