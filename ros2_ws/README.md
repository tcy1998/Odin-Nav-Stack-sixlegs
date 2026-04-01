# ROS2 Workspace for Hexapod Navigation

**Created:** 2026-03-31  
**Robot:** Dobot Mini Hex V2  
**Framework:** ROS2 (Humble/Foxy/Iron)

---

## 📁 Workspace Structure

```
ros2_ws/
├── src/
│   ├── neupan_ros2/          # NeuPAN ROS2 implementation
│   ├── yolo_ros2/            # YOLOv5 ROS2 package
│   ├── hexapod_bridge/       # ROS1-ROS2 bridge (temporary)
│   └── navigation_planner/   # A* path planner ROS2
├── install/                  # Built packages (auto-generated)
├── build/                    # Build files (auto-generated)
└── log/                      # Build logs (auto-generated)
```

---

## 🎯 Purpose

This workspace contains the ROS2 migration of the Odin-Nav-Stack navigation system:

1. **neupan_ros2:** Port of NeuPAN from ROS1 to ROS2
2. **yolo_ros2:** YOLOv5 object detection for ROS2
3. **hexapod_bridge:** Bridge between ROS1 navigation and ROS2 hexapod (temporary solution)
4. **navigation_planner:** A* global planner for ROS2

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install ROS2 (example for Humble on Ubuntu 22.04)
sudo apt install ros-humble-desktop

# Install colcon build tools
sudo apt install python3-colcon-common-extensions

# Install dependencies
sudo apt install \
  ros-humble-geometry-msgs \
  ros-humble-sensor-msgs \
  ros-humble-nav-msgs \
  ros-humble-tf2-ros \
  ros-humble-cv-bridge \
  python3-opencv
```

---

### Build Workspace

```bash
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws

# Source ROS2
source /opt/ros/humble/setup.bash

# Build all packages
colcon build

# Source the workspace
source install/setup.bash
```

---

### Build Specific Package

```bash
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws

# Build only one package
colcon build --packages-select neupan_ros2

# Build with debug symbols
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
```

---

## 📦 Package Details

### 1. neupan_ros2

**Purpose:** ROS2 port of NeuPAN neural planner

**Dependencies:**
- PyTorch
- cvxpy
- NumPy
- ROS2 geometry_msgs, sensor_msgs, nav_msgs

**Key Nodes:**
- `neupan_node` - Main planning node
- `dune_node` - Distance predictor

**Topics:**
```yaml
Subscribes:
  /scan (sensor_msgs/LaserScan)
  /robot_state (custom_msg/RobotState)
  /goal (geometry_msgs/PoseStamped)

Publishes:
  /vel_cmd (geometry_msgs/Twist)
  /plan (nav_msgs/Path)
  /arrive (std_msgs/Empty)
```

---

### 2. yolo_ros2

**Purpose:** YOLOv5 object detection for ROS2

**Dependencies:**
- YOLOv5 (ultralytics)
- PyTorch
- OpenCV
- ROS2 cv_bridge

**Key Nodes:**
- `yolo_detector_node` - Object detection node

**Topics:**
```yaml
Subscribes:
  /camera/image_raw (sensor_msgs/Image)

Publishes:
  /yolo/detections (vision_msgs/Detection2DArray)
  /yolo/image_annotated (sensor_msgs/Image)
```

---

### 3. hexapod_bridge

**Purpose:** Bridge ROS1 NeuPAN with ROS2 Hexapod (temporary)

**Dependencies:**
- rclpy (ROS2 Python client)
- rospy (ROS1 Python client)
- custom_msg (hexapod messages)

**Key Nodes:**
- `hexapod_neupan_bridge` - Bidirectional bridge

**Data Flow:**
```
ROS1 /cmd_vel    →  ROS2 /vel_cmd
ROS2 /livox/lidar → ROS1 /scan
ROS2 /robot_state → ROS1 /odom
```

**Note:** This is a temporary solution. Full ROS2 migration eliminates the need for this bridge.

---

### 4. navigation_planner

**Purpose:** Global path planning with A* algorithm

**Dependencies:**
- ROS2 nav_msgs
- ROS2 tf2

**Key Nodes:**
- `map_planner_node` - A* path planner

**Topics:**
```yaml
Subscribes:
  /map (nav_msgs/OccupancyGrid)
  /goal (geometry_msgs/PoseStamped)

Publishes:
  /initial_path (nav_msgs/Path)
```

---

## 🔧 Development Workflow

### 1. Create New Package

```bash
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws/src

# Python package
ros2 pkg create --build-type ament_python \
  --node-name my_node \
  my_package_py

# C++ package
ros2 pkg create --build-type ament_cmake \
  --node-name my_node \
  my_package_cpp
```

---

### 2. Add Dependencies

**For Python packages** - Edit `package.xml`:
```xml
<depend>rclpy</depend>
<depend>geometry_msgs</depend>
<depend>sensor_msgs</depend>
```

**For C++ packages** - Edit `CMakeLists.txt`:
```cmake
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
```

---

### 3. Build and Test

```bash
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws

# Clean build (if packages changed)
rm -rf build install log

# Build
colcon build

# Source
source install/setup.bash

# Test single node
ros2 run neupan_ros2 neupan_node

# Launch full system
ros2 launch neupan_ros2 hexapod_navigation.launch.py
```

---

## 🐛 Debugging

### Check Package Dependencies

```bash
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws

# List all packages
colcon list

# Check specific package
ros2 pkg xml neupan_ros2
```

---

### Common Build Issues

**Problem:** "Package 'X' not found"
```bash
# Install missing ROS2 package
sudo apt install ros-humble-<package-name>

# Or check package exists
ros2 pkg list | grep <package-name>
```

**Problem:** "No module named 'X'"
```bash
# Install Python package
pip3 install <package-name>

# Or use --user flag
pip3 install --user <package-name>
```

**Problem:** "Catkin workspace found"
```bash
# Make sure you're sourcing ROS2, not ROS1
source /opt/ros/humble/setup.bash  # NOT noetic
```

---

## 📊 Comparison: ROS1 vs ROS2

| Feature | ROS1 (ros_ws) | ROS2 (ros2_ws) |
|---------|---------------|----------------|
| **Build Tool** | catkin_make | colcon build |
| **Python** | Python 2/3 | Python 3 only |
| **Messages** | catkin_make | ament_cmake |
| **Launch Files** | .launch (XML) | .launch.py (Python) |
| **Node API** | rospy/roscpp | rclpy/rclcpp |
| **QoS** | Fixed | Configurable |
| **Real-time** | Limited | Better support |

---

## 🔄 Migration Status

### Completed
- [x] Workspace structure created
- [x] Package folders initialized
- [ ] *(Add as you complete tasks)*

### In Progress
- [ ] NeuPAN ROS2 port
- [ ] YOLO ROS2 integration
- [ ] Hexapod bridge implementation
- [ ] Navigation planner port

### Pending
- [ ] Launch files for full system
- [ ] RViz2 configuration
- [ ] Parameter files
- [ ] Integration testing
- [ ] Documentation

---

## 📝 Next Steps

### Phase 1: Bridge (Quick Integration)
1. Implement hexapod_bridge package
2. Test ROS1 NeuPAN ↔ ROS2 Hexapod
3. Verify basic navigation

### Phase 2: Core Migration
1. Port NeuPAN to ROS2 (neupan_ros2)
2. Port map_planner to ROS2
3. Create ROS2 launch files

### Phase 3: Full System
1. Port YOLO to ROS2
2. Integrate VLM with ROS2
3. Remove ROS1 dependencies
4. Performance optimization

**Estimated Timeline:** 2-4 weeks for full migration

---

## 🔗 Related Directories

- **ROS1 Workspace:** `/home/chuyuan/Odin-Nav-Stack/ros_ws/`
- **NeuPAN (Python):** `/home/chuyuan/Odin-Nav-Stack/NeuPAN/`
- **Hexapod (ROS2):** `/home/chuyuan/Odin-Nav-Stack/dobot_six_leg/`
- **YOLOv5:** `/home/chuyuan/Odin-Nav-Stack/yolov5/`

---

## 📚 Resources

**ROS2 Documentation:**
- [ROS2 Humble Docs](https://docs.ros.org/en/humble/)
- [Colcon Tutorial](https://colcon.readthedocs.io/)
- [ROS1 to ROS2 Migration Guide](https://docs.ros.org/en/humble/How-To-Guides/Migrating-from-ROS1.html)

**Tutorials:**
- Creating ROS2 Packages
- Writing Publishers and Subscribers
- Launch Files in ROS2
- TF2 in ROS2

---

**Version:** 1.0  
**Last Updated:** 2026-03-31  
**Maintainer:** @tcy1998
