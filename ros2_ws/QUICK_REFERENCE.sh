#!/bin/bash
# Quick Reference Commands for ROS2 Workspace
# Source: /home/chuyuan/Odin-Nav-Stack/ros2_ws/

# ==========================================
# 1. INITIAL SETUP (ONE TIME)
# ==========================================

# Install ROS2 and dependencies
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws
./setup_ros2.sh

# Add to ~/.bashrc (one time)
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
echo 'export PYTHONPATH=/home/chuyuan/Odin-Nav-Stack/NeuPAN:$PYTHONPATH' >> ~/.bashrc
source ~/.bashrc

# ==========================================
# 2. BUILD WORKSPACE
# ==========================================

# Build all packages
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws
colcon build

# Build specific package
colcon build --packages-select neupan_ros2

# Clean build
rm -rf build install log
colcon build

# ==========================================
# 3. RUN NODES
# ==========================================

# Source workspace first!
source /home/chuyuan/Odin-Nav-Stack/ros2_ws/install/setup.bash

# Run NeuPAN node
ros2 run neupan_ros2 neupan_node

# Or with launch file
ros2 launch neupan_ros2 neupan.launch.py

# ==========================================
# 4. SEND COMMANDS
# ==========================================

# Send goal (x=5, y=3, yaw=0)
ros2 topic pub --once /goal geometry_msgs/PoseStamped '{
  header: {frame_id: "map"},
  pose: {position: {x: 5.0, y: 3.0, z: 0.0}, orientation: {w: 1.0}}
}'

# Tune parameter q_s
ros2 topic pub --once /neupan/q_s std_msgs/Float32 "data: 2.0"

# Tune parameter p_u
ros2 topic pub --once /neupan/p_u std_msgs/Float32 "data: 1.5"

# ==========================================
# 5. MONITORING
# ==========================================

# List all topics
ros2 topic list

# Echo velocity commands
ros2 topic echo /vel_cmd

# Monitor scan data
ros2 topic echo /scan

# Check TF tree
ros2 run tf2_tools view_frames
evince frames.pdf  # View TF tree

# Check transform
ros2 run tf2_ros tf2_echo map link_trunk

# ==========================================
# 6. DEBUGGING
# ==========================================

# Check if node is running
ros2 node list

# Get node info
ros2 node info /neupan_node

# Check for errors
ros2 node info /neupan_node | grep -A 10 "Subscribers"

# View logs
ros2 run rqt_console rqt_console

# ==========================================
# 7. VISUALIZATION (RViz2)
# ==========================================

# Launch RViz2
rviz2

# Add displays in RViz2:
# - Add -> By topic -> /neupan_plan -> Path
# - Add -> By topic -> /scan -> LaserScan
# - Add -> TF
# - Fixed Frame: map

# ==========================================
# 8. TRAINING STATUS CHECK
# ==========================================

# Check if model exists
ls -lh /home/chuyuan/Odin-Nav-Stack/NeuPAN/example/dune_train/model/dobot_hex_v2/model_5000.pth

# If missing, check training progress
cd /home/chuyuan/Odin-Nav-Stack/NeuPAN
./monitor_training.sh

# ==========================================
# 9. PACKAGE DEVELOPMENT
# ==========================================

# Create new package
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws/src
ros2 pkg create --build-type ament_python \
  --node-name my_node \
  my_package

# List packages
colcon list

# Check package dependencies
ros2 pkg xml neupan_ros2

# ==========================================
# 10. TROUBLESHOOTING
# ==========================================

# "NeuPAN module not found"
export PYTHONPATH=/home/chuyuan/Odin-Nav-Stack/NeuPAN:$PYTHONPATH

# "config.yaml not found"
ls /home/chuyuan/Odin-Nav-Stack/ros2_ws/src/neupan_ros2/config/

# "Could not transform" / TF errors
ros2 run tf2_ros tf2_echo map link_trunk

# "No /scan data"
ros2 topic list | grep scan
ros2 topic hz /scan

# Build errors
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws
rm -rf build install log
colcon build --symlink-install

# ==========================================
# 11. USEFUL ALIASES (add to ~/.bashrc)
# ==========================================

# alias ros2_ws='cd /home/chuyuan/Odin-Nav-Stack/ros2_ws'
# alias ros2_build='cd /home/chuyuan/Odin-Nav-Stack/ros2_ws && colcon build'
# alias ros2_source='source /home/chuyuan/Odin-Nav-Stack/ros2_ws/install/setup.bash'
# alias ros2_clean='cd /home/chuyuan/Odin-Nav-Stack/ros2_ws && rm -rf build install log'
# alias neupan_run='ros2 run neupan_ros2 neupan_node'

# ==========================================
# 12. MULTI-TERMINAL SETUP
# ==========================================

# Terminal 1: Hexapod control (if using real robot)
# cd /home/chuyuan/Odin-Nav-Stack/dobot_six_leg
# ... launch hexapod nodes ...

# Terminal 2: NeuPAN navigation
# source /home/chuyuan/Odin-Nav-Stack/ros2_ws/install/setup.bash
# ros2 run neupan_ros2 neupan_node

# Terminal 3: YOLO detection (after Phase 4)
# source /home/chuyuan/Odin-Nav-Stack/ros2_ws/install/setup.bash
# ros2 run yolo_ros2 yolo_detector_node

# Terminal 4: RViz2 visualization
# rviz2

# Terminal 5: Command interface
# ros2 topic pub --once /goal geometry_msgs/PoseStamped ...

# ==========================================
# DOCUMENTATION
# ==========================================
# 
# ros2_ws/README.md                  - Workspace overview
# ros2_ws/MIGRATION_STATUS.md        - Migration progress
# ros2_ws/src/neupan_ros2/README.md  - NeuPAN package docs
# HEXAPOD_MIGRATION_GUIDE.md         - Original guide
# HEXAPOD_TO_NEUPAN_INTEGRATION.md   - Integration guide
#
# ==========================================
