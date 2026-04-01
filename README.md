<p align="center">
  <h2 align="center">Odin Navigation Stack</h2>
</p>

<div align="center">
  <a href="https://ManifoldTechLtd.github.io/Odin-Nav-Stack-Webpage">
  <img src='https://img.shields.io/badge/Webpage-OdinNavStack-blue' alt='webpage'></a>  
  <a href="https://www.apache.org/licenses/LICENSE-2.0">
  <img src='https://img.shields.io/badge/License-Apache2.0-green' alt='Apache2.0'></a>  
  <a href="https://www.youtube.com/watch?v=du038MPxc0s">
  <img src='https://img.shields.io/badge/Video-YouTube-red' alt='youtube'></a>  
  <a href="https://www.bilibili.com/video/BV1sFBXBmEum/">
  <img src='https://img.shields.io/badge/Video-bilibili-pink' alt='bilibili'></a>  
  <a href="https://wiki.ros.org/noetic">
  <img src='https://img.shields.io/badge/ROS1-Noetic-orange' alt='noetic'></a>
  <a href="https://docs.ros.org/en/humble/">
  <img src='https://img.shields.io/badge/ROS2-Humble-blue' alt='humble'></a>
</div>

**Odin Navigation Stack** is a comprehensive autonomous navigation framework supporting multiple robot platforms and ROS versions. Built around high-performance sensing and neural-based planning, the stack enables robust navigation in complex environments.

## Supported Platforms

| Platform | ROS Version | Framework | Status |
|----------|-------------|-----------|--------|
| **Unitree Go2** | ROS1 Noetic | Odin1 Sensor | ✅ Production |
| **Dobot Mini Hex V2** | ROS2 Humble | Custom Sensors | ✅ Production |

## Key Features

- **High-Accuracy SLAM & Persistent Relocalization** (Odin1 sensor)  
  Real-time mapping with long-term relocalization using compact binary maps.
  
- **NeuPAN Neural Navigation** (fully open-sourced)  
  End-to-end neural planner combining DUNE (distance predictor) + NRMP (MPC optimizer) for real-time dynamic obstacle avoidance. [Paper](https://ieeexplore.ieee.org/document/10938329/)
  
- **Semantic Object Navigation** (fully open-sourced)  
  YOLOv5-based detection with natural language commands: _"Go to the left of the chair"_
  
- **Vision-Language Integration** (fully open-sourced)  
  VLM-powered scene understanding and description for context-aware navigation.
  
- **Multi-Platform Architecture**  
  Modular design supporting both ROS1 (Unitree Go2) and ROS2 (Dobot hexapod).

---

# Table of Contents

- [Quick Start](#quick-start)
  - [Unitree Go2 (ROS1)](#unitree-go2-ros1)
  - [Dobot Hexapod (ROS2)](#dobot-hexapod-ros2)
- [Platform-Specific Guides](#platform-specific-guides)
  - [Unitree Go2 Setup](#unitree-go2-setup)
  - [Dobot Hexapod Setup](#dobot-hexapod-setup)
- [Common Features](#common-features)
- [Documentation](#documentation)
- [FAQ](#faq)
- [Acknowledgements](#acknowledgements)

---

# Quick Start

## Unitree Go2 (ROS1)

**Tested on:** Ubuntu 20.04, ROS1 Noetic, NVIDIA Jetson Orin Nano

### 1. Clone Repository

```bash
git clone --depth 1 --recursive https://github.com/ManifoldTechLtd/Odin-Nav-Stack.git
cd Odin-Nav-Stack
```

### 2. Install Dependencies

```bash
# System packages
export ROS_DISTRO=noetic
sudo apt update && sudo apt install -y \
    ros-${ROS_DISTRO}-desktop \
    ros-${ROS_DISTRO}-tf2-ros \
    ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-pcl-ros \
    python3-pip python3-venv

# NeuPAN environment
python3 -m pip install torch numpy scipy cvxpy cvxpylayers loguru
pip install -e NeuPAN
```

### 3. Build Workspace

```bash
cd ros_ws
source /opt/ros/${ROS_DISTRO}/setup.bash
catkin_make -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash
```

### 4. Launch Navigation

```bash
# Terminal 1: Odin1 driver
roslaunch odin_ros_driver odin1_ros1.launch

# Terminal 2: Map planner
roslaunch map_planner whole.launch

# Terminal 3: NeuPAN planner
python NeuPAN/neupan/ros/neupan_ros.py
```

**See full Unitree Go2 guide:** [Unitree Go2 Setup](#unitree-go2-setup)

---

## Dobot Hexapod (ROS2)

**Tested on:** Ubuntu 22.04, ROS2 Humble, Python 3.10+

### 1. Clone Repository

```bash
git clone --depth 1 https://github.com/tcy1998/Odin-Nav-Stack.git
cd Odin-Nav-Stack
```

### 2. Install ROS2 & Dependencies

```bash
cd ros2_ws
./setup_ros2.sh  # Automated installation script
```

Or manually:

```bash
# Install ROS2 Humble
sudo apt update && sudo apt install -y \
    ros-humble-desktop \
    python3-colcon-common-extensions \
    ros-humble-tf2-ros \
    ros-humble-sensor-msgs \
    ros-humble-geometry-msgs

# Python dependencies
pip3 install torch numpy scipy cvxpy loguru
pip3 install -e ../NeuPAN
```

### 3. Build ROS2 Workspace

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
export PYTHONPATH=/path/to/Odin-Nav-Stack/NeuPAN:$PYTHONPATH
colcon build
source install/setup.bash
```

### 4. Train NeuPAN Model for Hexapod

```bash
cd NeuPAN/example/dune_train

# Run training (1-2 hours on CPU, 10-20 min on GPU)
python3 dune_train_diff.py dune_train_hexapod.yaml
```

Model will be saved to: `example/dune_train/model/dobot_hex_v2/model_5000.pth`

### 5. Launch Navigation

```bash
# Terminal 1: Launch hexapod control (from dobot_six_leg repo)
cd /path/to/dobot_six_leg
# ... launch hexapod nodes ...

# Terminal 2: Launch NeuPAN navigation
source ros2_ws/install/setup.bash
ros2 run neupan_ros2 neupan_node

# Terminal 3: Send navigation goal
ros2 topic pub --once /goal geometry_msgs/PoseStamped '{
  header: {frame_id: "map"},
  pose: {position: {x: 5.0, y: 3.0, z: 0.0}, orientation: {w: 1.0}}
}'
```

**See full hexapod guide:** [Dobot Hexapod Setup](#dobot-hexapod-setup)

---

# Platform-Specific Guides

## Unitree Go2 Setup

### System Requirements

- **OS:** Ubuntu 20.04  
- **ROS:** ROS1 Noetic  
- **Hardware:** NVIDIA Jetson Orin Nano (or x86 with GPU)  
- **Robot:** Unitree Go2  
- **Sensor:** Odin1 spatial sensing module

### 1. Clone and Update Odin Driver

```bash
git clone --depth 1 --recursive https://github.com/ManifoldTechLtd/Odin-Nav-Stack.git
cd Odin-Nav-Stack/ros_ws/src/odin_ros_driver
git fetch origin
git checkout main
git pull origin main
```

### 2. Modify Odin1 ROS Driver

Edit `ros_ws/src/odin_ros_driver/include/host_sdk_sample.h`:

#### a) Modify `ns_to_ros_time` function:

```cpp
inline ros::Time ns_to_ros_time(uint64_t timestamp_ns) {
    ros::Time t;
    #ifdef ROS2
        t.sec = static_cast<int32_t>(timestamp_ns / 1000000000);
        t.nanosec = static_cast<uint32_t>(timestamp_ns % 1000000000);
    #else
        // t.sec = static_cast<uint32_t>(timestamp_ns / 1000000000);
        // t.nsec = static_cast<uint32_t>(timestamp_ns % 1000000000);
        return ros::Time::now();
    #endif
    return t;
}
```

#### b) Comment out low-frequency TF in `publishOdometry`:

```cpp
switch(odom_type) {
    case OdometryType::STANDARD:
        {
        // geometry_msgs::TransformStamped transformStamped;
        // transformStamped.header.stamp = msg.header.stamp;
        // ... (comment out entire TF transform block)
        odom_publisher_.publish(msg);
    ...
```

#### c) Add high-frequency TF transform:

```cpp
case OdometryType::HIGHFREQ:{
    geometry_msgs::TransformStamped transformStamped;
    transformStamped.header.stamp = msg.header.stamp;
    transformStamped.header.frame_id = "odom";
    transformStamped.child_frame_id = "odin1_base_link";
    transformStamped.transform.translation.x = msg.pose.pose.position.x;
    transformStamped.transform.translation.y = msg.pose.pose.position.y;
    transformStamped.transform.translation.z = msg.pose.pose.position.z;
    transformStamped.transform.rotation.x = msg.pose.pose.orientation.x;
    transformStamped.transform.rotation.y = msg.pose.pose.orientation.y;
    transformStamped.transform.rotation.z = msg.pose.pose.orientation.z;
    transformStamped.transform.rotation.w = msg.pose.pose.orientation.w;
    tf_broadcaster->sendTransform(transformStamped);
    odom_highfreq_publisher_.publish(msg);
    break;
}
```

### 3. Install System Dependencies

```bash
export ROS_DISTRO=noetic
sudo apt update && sudo apt install -y \
    ros-${ROS_DISTRO}-tf2-ros \
    ros-${ROS_DISTRO}-tf2-geometry-msgs \
    ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-tf2-eigen \
    ros-${ROS_DISTRO}-pcl-ros \
    ros-${ROS_DISTRO}-move-base \
    ros-${ROS_DISTRO}-dwa-local-planner
```

### 4. Install Unitree Go2 SDK

Follow official guide: [Unitree Go2 SDK](https://support.unitree.com/home/zh/developer/Obtain%20SDK)

### 5. Setup Conda & NeuPAN Environment

```bash
# Install miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Install mamba
conda install -n base -c conda-forge mamba

# Create NeuPAN environment
export ROS_DISTRO=noetic
mamba create -n neupan -y
mamba activate neupan
conda config --env --add channels conda-forge
conda config --env --remove channels defaults
conda config --env --add channels robostack-${ROS_DISTRO}
mamba install -n neupan ros-${ROS_DISTRO}-desktop colcon-common-extensions -y
mamba run -n neupan pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
pip install -e NeuPAN
```

**For Jetson:** Replace PyTorch install with compatible .whl from [NVIDIA Jetson PyTorch](https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048).

### 6. Build ROS Workspace

```bash
cd ros_ws
source /opt/ros/${ROS_DISTRO}/setup.bash
catkin_make -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash
```

### 7. Set USB Rules for Odin1

```bash
sudo bash -c 'cat > /etc/udev/rules.d/99-odin-usb.rules << EOF
SUBSYSTEM=="usb", ATTR{idVendor}=="2207", ATTR{idProduct}=="0019", MODE="0666", GROUP="plugdev"
EOF'

sudo udevadm control --reload
sudo udevadm trigger
```

### 8. Mapping with Odin1

#### Configure Mapping Mode

Edit `ros_ws/src/odin_ros_driver/config/control_command.yaml`:

```yaml
custom_map_mode: 1  # Enable mapping
```

#### Launch Mapping

```bash
# Terminal 1: Odin driver
source ros_ws/devel/setup.bash
roslaunch odin_ros_driver odin1_ros1.launch

# Terminal 2: Record map
bash scripts/map_recording.sh awesome_map
```

Maps saved to:
- PCD map: `ros_ws/src/pcd2pgm/maps/`
- Grid map: `ros_ws/src/map_planner/maps/`

Edit grid map with GIMP:

```bash
sudo apt install gimp
gimp ros_ws/src/map_planner/maps/awesome_map.pgm
```

### 9. Relocalization & Navigation

#### Enable Relocalization

Edit `control_command.yaml`:

```yaml
custom_map_mode: 2
relocalization_map_abs_path: "/abs/path/to/your/map"
```

#### Launch Navigation

```bash
# Terminal 1: Odin driver
roslaunch odin_ros_driver odin1_ros1.launch

# Terminal 2: Map planner (A* global planner)
roslaunch map_planner whole.launch

# Terminal 3: NeuPAN local planner
mamba activate neupan
python NeuPAN/neupan/ros/neupan_ros.py
```

#### Verify TF Tree

Use RViz or rqt to verify: `map → odom → odin1_base_link`

Initial motion may be required to trigger relocalization.

### 10. YOLOv5 Object Detection

#### Install YOLOv5

```bash
python3 -m venv ros_ws/venvs/ros_yolo_py38
source ros_ws/venvs/ros_yolo_py38/bin/activate
pip install --upgrade pip "numpy<2.0.0"
cd ros_ws/src && git clone https://github.com/ultralytics/yolov5.git
pip install -r yolov5/requirements.txt
pip install opencv-python pillow pyyaml requests tqdm scipy matplotlib seaborn pandas empy==3.3.4 catkin_pkg ros_pkg vosk sounddevice
```

#### Download Resources

```bash
mkdir -p ros_ws/src/yolo_ros/scripts/voicemodel
cd ros_ws/src/yolo_ros/scripts/voicemodel
wget https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip
unzip vosk-model-small-cn-0.22.zip
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt -O ../models/yolov5s.pt
chmod +x ../yolo_detector.py
```

#### Calibrate Camera

Copy `Tcl_0` and `cam_0` from `odin_ros_driver/config/calib.yaml` into `yolo_detector.py`.

#### Launch

```bash
# Terminal 1: Odin driver
roslaunch odin_ros_driver odin1_ros1.launch

# Terminal 2: YOLO detector
./run_yolo_detector.sh
```

**Commands in Terminal 2:**
- `list` - Query recognized objects
- `object name` - Display 3D position in RViz
- `Move to the [Nth] [object] [direction]` - Navigate (supports Chinese)
- `mode` - Toggle text/voice input

### 11. Vision-Language Model (VLM)

```bash
# Install llama.cpp
brew install llama.cpp

# Download SmolVLM model
wget https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF/resolve/main/SmolVLM-500M-Instruct-Q8_0.gguf
wget https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF/resolve/main/mmproj-SmolVLM-500M-Instruct-Q8_0.gguf

# Terminal 1: LLaMA server
llama-server -m SmolVLM-500M-Instruct-Q8_0.gguf --mmproj mmproj-SmolVLM-500M-Instruct-Q8_0.gguf

# Terminal 2: Odin driver
roslaunch odin_ros_driver odin1_ros1.launch

# Terminal 3: VLM terminal
roslaunch odin_vlm_terminal odin_vlm_terminal.launch
```

### 12. Vision-Language Navigation (VLN)

Full pipeline: VLM → String Command → Map Planner → NeuPAN → Robot

```bash
# Terminal 1: Map planner
roslaunch map_planner whole.launch

# Terminal 2: Odin driver
roslaunch odin_ros_driver odin1_ros1.launch

# Terminal 3: NeuPAN
mamba activate neupan
python NeuPAN/neupan/ros/neupan_ros.py

# Terminal 4: String command controller
mamba activate neupan
python scripts/str_cmd_control.py

# Terminal 5: VLN interface
mamba activate neupan
python scripts/VLN.py
```

---

## Dobot Hexapod Setup

### System Requirements

- **OS:** Ubuntu 22.04  
- **ROS:** ROS2 Humble  
- **Hardware:** x86 with CPU/GPU (or Jetson)  
- **Robot:** Dobot Mini Hex V2 (6-legged hexapod)  
- **Sensors:** Livox lidar, RealSense camera

### Robot Specifications

| Parameter | Value |
|-----------|-------|
| **Footprint** | 0.5m × 0.1275m |
| **Max Linear Speed** | 0.2 m/s |
| **Max Angular Speed** | 0.28 rad/s |
| **Legs** | 6 (18 DOF total) |
| **Control** | ROS2 `/vel_cmd` (Twist) |
| **Lidar** | Livox (PointCloud2) |

### 1. Clone Repositories

```bash
# Main navigation stack
git clone --depth 1 https://github.com/tcy1998/Odin-Nav-Stack-sixlegs.git
cd Odin-Nav-Stack-sixlegs

# Hexapod MuJoCo models (separate repo)
git clone https://github.com/tcy1998/dobot_six_leg.git
```

### 2. Install ROS2 & Dependencies

#### Automated Installation

```bash
cd ros2_ws
./setup_ros2.sh
```

#### Manual Installation

```bash
# Install ROS2 Humble
sudo apt update && sudo apt install -y \
    software-properties-common \
    curl gnupg lsb-release

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update && sudo apt install -y \
    ros-humble-desktop \
    python3-colcon-common-extensions \
    ros-humble-geometry-msgs \
    ros-humble-sensor-msgs \
    ros-humble-nav-msgs \
    ros-humble-tf2-ros \
    ros-humble-tf2-geometry-msgs

# Python dependencies
pip3 install torch numpy scipy cvxpy cvxpylayers loguru
```

### 3. Install NeuPAN for Hexapod

```bash
# Clone hexapod-specific NeuPAN branch
cd Odin-Nav-Stack-sixlegs
git clone -b hexapod-support https://github.com/tcy1998/NeuPAN_sixlegs.git NeuPAN

# Install dependencies
cd NeuPAN
pip3 install --user -e .
```

**Note:** Uses Python 3.8+ compatible version with fixed type hints.

### 4. Train NeuPAN Model for Hexapod

NeuPAN requires robot-specific training due to different footprint and kinematics.

#### Quick Training (Automated)

```bash
cd NeuPAN
./setup_hexapod_training.sh    # Install dependencies
./start_hexapod_training.sh    # Start training
./monitor_training.sh          # Monitor progress
```

#### Manual Training

```bash
cd NeuPAN/example/dune_train

# CPU training (1-2 hours)
python3 dune_train_diff.py dune_train_hexapod.yaml

# GPU training (10-20 min) - change device in neupan/configuration/__init__.py
# device = torch.device("cuda")  # Line 25
```

**Training parameters:**
- Samples: 100,000 synthetic trajectories
- Epochs: 5000
- Map size: 50m × 50m
- Obstacles: Random convex polygons

**Model location:** `NeuPAN/example/dune_train/model/dobot_hex_v2/model_5000.pth`

### 5. Build ROS2 Workspace

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
export PYTHONPATH=/path/to/Odin-Nav-Stack-sixlegs/NeuPAN:$PYTHONPATH
colcon build
source install/setup.bash
```

**Add to `~/.bashrc`:**

```bash
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
echo 'export PYTHONPATH=/path/to/Odin-Nav-Stack-sixlegs/NeuPAN:$PYTHONPATH' >> ~/.bashrc
source ~/.bashrc
```

### 6. Launch Hexapod Navigation

#### Option A: Full ROS2 Migration (Recommended)

```bash
# Terminal 1: Launch hexapod control
cd dobot_six_leg
# ... launch hexapod ROS2 nodes ...
# Publishes: /robot_state, /livox/lidar
# Subscribes: /vel_cmd

# Terminal 2: Launch NeuPAN
cd Odin-Nav-Stack-sixlegs/ros2_ws
source install/setup.bash
ros2 run neupan_ros2 neupan_node

# Terminal 3: Send goal
ros2 topic pub --once /goal geometry_msgs/PoseStamped '{
  header: {frame_id: "map"},
  pose: {
    position: {x: 5.0, y: 3.0, z: 0.0},
    orientation: {w: 1.0, x: 0.0, y: 0.0, z: 0.0}
  }
}'
```

#### Option B: ROS1↔ROS2 Bridge (Temporary)

For quick testing of ROS1 NeuPAN with ROS2 hexapod:

```bash
# Terminal 1: ROS1 core
source /opt/ros/noetic/setup.bash
roscore

# Terminal 2: Bridge
source /opt/ros/noetic/setup.bash
source /opt/ros/humble/setup.bash
ros2 run ros1_bridge dynamic_bridge

# Terminal 3: Hexapod (ROS2)
cd dobot_six_leg
# ... launch hexapod ...

# Terminal 4: NeuPAN (ROS1)
cd Odin-Nav-Stack-sixlegs
source ros_ws/devel/setup.bash
python NeuPAN/neupan/ros/neupan_ros.py
```

### 7. Verify System

#### Check TF Tree

```bash
ros2 run tf2_tools view_frames
evince frames.pdf  # Should show: map → link_trunk → livox_frame
```

#### Monitor Topics

```bash
# List topics
ros2 topic list

# Check scan data (LaserScan from PointCloud2)
ros2 topic echo /scan

# Monitor velocity commands
ros2 topic echo /vel_cmd

# Check robot state
ros2 topic echo /robot_state
```

#### Visualize in RViz2

```bash
rviz2

# Add displays:
# - TF
# - LaserScan (/scan)
# - Path (/neupan_plan)
# - Path (/neupan_initial_path)
# - Marker (/robot_marker)
# Fixed Frame: map
```

### 8. Parameter Tuning

Edit `ros2_ws/src/neupan_ros2/config/planner.yaml`:

```yaml
ref_speed: 0.2           # Reference tracking speed (m/s)
max_speed: [0.2, 0.28]   # [linear, angular] max speeds
collision_threshold: 0.3 # Stop when obstacle < 0.3m
robot:
  length: 0.5            # Hexapod length (m)
  width: 0.1275          # Hexapod width (m)
  min_radius: 0.15       # Minimum turning radius (m)
```

**Runtime tuning:**

```bash
# Increase smoothness (lower q_s = smoother but slower)
ros2 topic pub /neupan/q_s std_msgs/Float32 "data: 2.0"

# Increase urgency (higher p_u = faster but less smooth)
ros2 topic pub /neupan/p_u std_msgs/Float32 "data: 1.5"
```

### 9. Troubleshooting

#### Problem: "NeuPAN module not found"

```bash
export PYTHONPATH=/path/to/NeuPAN:$PYTHONPATH
# Or add to ~/.bashrc
```

#### Problem: "config.yaml not found"

```bash
# Copy from NeuPAN
cd ros2_ws/src/neupan_ros2
mkdir -p config
cp /path/to/NeuPAN/neupan/ros/configs/*.yaml config/
```

#### Problem: "DUNE checkpoint not found"

```bash
# Verify training completed
ls -lh NeuPAN/example/dune_train/model/dobot_hex_v2/model_5000.pth

# If missing, retrain
cd NeuPAN/example/dune_train
./start_hexapod_training.sh
```

#### Problem: "Could not transform map to link_trunk"

```bash
# Check TF tree
ros2 run tf2_tools view_frames

# Check specific transform
ros2 run tf2_ros tf2_echo map link_trunk

# Ensure localization is running
```

#### Problem: "No /scan data"

```bash
# Check if Livox lidar is publishing
ros2 topic list | grep livox
ros2 topic hz /livox/lidar

# Implement PointCloud2 → LaserScan conversion
# See: ros2_ws/src/neupan_ros2/README.md
```

### 10. Migration Guides

Comprehensive documentation:

- **HEXAPOD_MIGRATION_GUIDE.md** - Full migration from Unitree Go2 to hexapod
- **HEXAPOD_TO_NEUPAN_INTEGRATION.md** - Data integration and bridge implementation
- **ros2_ws/README.md** - ROS2 workspace overview
- **ros2_ws/MIGRATION_STATUS.md** - ROS2 migration progress tracker
- **ros2_ws/QUICK_REFERENCE.sh** - Command reference

---

# Common Features

## NeuPAN Neural Navigation

**NeuPAN** (Neural Parallel Autonomy Navigation) combines:

- **DUNE:** Neural distance predictor (offline trained)
- **NRMP:** MPC-based trajectory optimizer (online)

### Why NeuPAN?

- **Fast:** 20-50 Hz control loop (typical: 10-20ms per iteration)
- **Safe:** Predicts collision distances, maintains safety margins
- **Smooth:** MPC optimization for comfortable trajectories
- **Robot-Specific:** Trained for exact robot geometry

### Architecture

```
Obstacle Points (LaserScan)  ──┐
Robot State (Odometry)       ──┼──> DUNE ──> Distance μ ──> NRMP ──> Velocity Cmd
Goal/Waypoints               ──┘           (Neural Net)   (MPC)     (Twist)
```

### Training Custom Robot

1. **Define robot geometry** in YAML config
2. **Generate synthetic data** (100k samples)
3. **Train DUNE network** (5000 epochs)
4. **Deploy model** in planner config

See: `NeuPAN/example/dune_train/dune_train_hexapod.yaml`

---

## Object Detection & Semantic Navigation

**YOLOv5** for real-time object detection + natural language navigation.

### Features

- Real-time detection (30+ FPS)
- 80 COCO classes
- 3D localization (depth + detection)
- Voice/text commands

### Usage

**ROS1 (Unitree Go2):**

```bash
./run_yolo_detector.sh
# Type: "Move to the left of the chair"
```

**ROS2 (Hexapod):**

```bash
# TODO: Port yolo_ros to ROS2
# See: ros2_ws/src/yolo_ros2/
```

---

## Vision-Language Model Integration

**VLM** for scene understanding and description.

### Supported Models

- SmolVLM (500M, recommended for edge devices)
- Qwen3-VL (online API, better accuracy)

### Use Cases

- Scene description: "Describe what you see"
- Object queries: "Is there a chair in the room?"
- Navigation context: "What's to the left of the door?"

---

# Documentation

## Repository Structure

```
Odin-Nav-Stack/
├── README.md                          # This file
├── LICENSE
├── NeuPAN/                            # Neural planner library
│   ├── neupan/
│   │   ├── neupan.py                  # Main planner
│   │   ├── blocks/dune.py             # Neural network
│   │   └── ros/
│   │       ├── neupan_ros.py          # ROS1 node
│   │       └── configs/
│   │           ├── config.yaml        # Node config
│   │           └── planner.yaml       # Planner params
│   └── example/dune_train/
│       ├── dune_train_diff.py         # Training script
│       ├── dune_train_hexapod.yaml    # Hexapod config
│       └── model/dobot_hex_v2/        # Trained models
├── ros_ws/                            # ROS1 workspace (Unitree Go2)
│   └── src/
│       ├── odin_ros_driver/           # Odin1 driver
│       ├── map_planner/               # A* global planner
│       ├── yolo_ros/                  # YOLO detection
│       ├── navigation_planner/        # Nav1 interface
│       └── model_planner/             # Custom planner
├── ros2_ws/                           # ROS2 workspace (Hexapod)
│   ├── README.md                      # Workspace guide
│   ├── MIGRATION_STATUS.md            # Progress tracker
│   ├── QUICK_REFERENCE.sh             # Commands
│   ├── setup_ros2.sh                  # Installation script
│   └── src/
│       ├── neupan_ros2/               # NeuPAN ROS2 (50% complete)
│       ├── yolo_ros2/                 # YOLO ROS2 (TODO)
│       ├── hexapod_bridge/            # ROS1↔ROS2 bridge (TODO)
│       └── navigation_planner/        # A* ROS2 (TODO)
├── dobot_six_leg/                     # Hexapod MuJoCo models (external)
├── yolov5/                            # YOLOv5 library
├── scripts/
│   ├── VLN.py                         # VLN interface
│   ├── str_cmd_control.py             # Command parser
│   └── run_yolo_detector.sh           # YOLO launcher
├── HEXAPOD_MIGRATION_GUIDE.md         # Hexapod migration guide
├── HEXAPOD_TO_NEUPAN_INTEGRATION.md   # Integration guide
└── dobot_six_leg/ROBOT_SPECS.md       # Hexapod specifications
```

## Key Documentation Files

| File | Description |
|------|-------------|
| **README.md** | This file - main documentation |
| **HEXAPOD_MIGRATION_GUIDE.md** | Unitree Go2 → Dobot hexapod migration |
| **HEXAPOD_TO_NEUPAN_INTEGRATION.md** | Data integration, bridge code |
| **ros2_ws/README.md** | ROS2 workspace guide |
| **ros2_ws/MIGRATION_STATUS.md** | ROS2 migration progress (30% complete) |
| **ros2_ws/QUICK_REFERENCE.sh** | ROS2 command cheat sheet |
| **dobot_six_leg/ROBOT_SPECS.md** | Hexapod specifications |

---

# FAQ

## General

### Q: Which platform should I use?

- **For Unitree Go2 with Odin1 sensor:** Use ROS1 workspace (`ros_ws/`)
- **For Dobot hexapod or custom robots:** Use ROS2 workspace (`ros2_ws/`)
- **For other robots:** Train NeuPAN for your robot geometry

### Q: Do I need to retrain NeuPAN?

**Yes, if:**
- Robot footprint different from Unitree Go2 (0.5m × 0.36m) or Dobot hexapod (0.5m × 0.1275m)
- Different velocity limits
- Different kinematics (e.g., car-like vs differential drive)

**No, if:**
- Using exact same robot platform
- Can use pre-trained models

### Q: Can I use NeuPAN without Odin1?

**Yes!** NeuPAN works with any 2D laser scan (`/scan` topic). You can:
- Use Livox lidar + PointCloud2→LaserScan conversion
- Use standard 2D lidar (e.g., RPLidar, SICK)
- Provide `/scan` topic from any source

### Q: What's the difference between DUNE and NRMP?

- **DUNE:** Neural network, predicts distance constraints (μ parameters)
- **NRMP:** MPC optimizer, generates velocity commands satisfying constraints

Both run together in NeuPAN planner.

## ROS1 (Unitree Go2)

### Q: How to check relocalization status?

Open RViz:
1. Set `Fixed Frame` → `map`
2. Add → `TF`
3. Verify: `map → odom → odin1_base_link` exists

### Q: Goal is occupied / start point blocked

**Solution:**
- Check inflation map: `ros2 topic echo /inflated_map`
- Reduce inflation radius in `whole.launch:inflation_radius`
- Ensure clear space around start/goal

### Q: Robot doesn't stop at goal

**Solution:**
- Increase `goal_tolerance` in `whole.launch`
- Check final waypoint visibility
- Verify `/arrive` topic published

## ROS2 (Hexapod)

### Q: Training takes too long

**Solution:**
- Use GPU: Change `device = torch.device("cuda")` in `neupan/configuration/__init__.py` line 25
- Reduce samples: Change `num_sample: 100000` → `50000` in training config
- Reduce epochs: `epochs: 5000` → `2500`

**Note:** Model quality may decrease with fewer samples/epochs.

### Q: "Could not transform map to link_trunk"

**Solution:**
- Verify hexapod publishes TF: `ros2 run tf2_tools view_frames`
- Check localization running (SLAM or pre-built map)
- Ensure all frames connected

### Q: No /scan topic

**Solution:**
Hexapod has Livox lidar (PointCloud2), need conversion:

```bash
# Install pointcloud_to_laserscan
sudo apt install ros-humble-pointcloud-to-laserscan

# Launch conversion node
ros2 run pointcloud_to_laserscan pointcloud_to_laserscan_node \
  --ros-args -r cloud_in:=/livox/lidar -r scan:=/scan
```

Or use custom bridge from `HEXAPOD_TO_NEUPAN_INTEGRATION.md`.

### Q: ROS2 migration incomplete

**Current status:** 30% complete

**Completed:**
- ✅ Workspace structure
- ✅ NeuPAN ROS2 node (main functionality)
- ✅ Package configuration
- ✅ Launch files

**TODO:**
- ⏳ Visualization markers
- ⏳ YOLO ROS2 port
- ⏳ Navigation planner ROS2
- ⏳ Full integration testing

See: `ros2_ws/MIGRATION_STATUS.md` for detailed progress.

## Troubleshooting

### libgomp Problem (ROS1)

**Error:** `libgomp` not found

**Solution:**

```bash
for f in ~/venvs/ros_yolo_py38/lib/python3.8/site-packages/torch.libs/libgomp*.so*; do
    [ -f "$f" ] && mv "$f" "$f.bak"
done
```

### torch/torchvision Conflict (ROS1)

**Error:** `torch.cuda.is_available() returns False`

**Cause:** torchvision overwrote CUDA-enabled PyTorch

**Solution:**

```bash
pip uninstall torch torchvision torchaudio
pip install torch-*.whl  # Reinstall from .whl
pip install --no-cache-dir "git+https://github.com/pytorch/vision.git@v0.16.0"
```

Or modify `yolov5/utils/general.py` to use pure PyTorch NMS (see original README).

---

# Acknowledgements

This project builds on excellent open-source work:

- **[ROS Navigation](https://github.com/ros-planning/navigation)** - Nav1 framework
- **[NeuPAN](https://github.com/hanruihua/NeuPAN)** - Neural planner ([Paper](https://ieeexplore.ieee.org/document/10938329/))
- **[YOLOv5](https://github.com/ultralytics/ultralytics)** - Object detection
- **[Qwen](https://github.com/QwenLM/Qwen3-VL)** - Vision-language model
- **Unitree Robotics** - Go2 SDK
- **Dobot** - Mini Hex V2 hexapod platform

---

# Citation

If you use this work in your research, please cite:

```bibtex
@article{neupan2025,
  title={NeuPAN: Neural Parallel Autonomy Navigation},
  author={Han, Ruihua and Mo, Hongle and others},
  journal={IEEE Transactions on Robotics},
  year={2025},
  doi={10.1109/TRO.2025.10938329}
}
```

---

# License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

# Contact

- **Issues:** [GitHub Issues](https://github.com/ManifoldTechLtd/Odin-Nav-Stack/issues)
- **Discussions:** [GitHub Discussions](https://github.com/ManifoldTechLtd/Odin-Nav-Stack/discussions)
- **Website:** [Odin Navigation Stack Webpage](https://ManifoldTechLtd.github.io/Odin-Nav-Stack-Webpage)

---

**Last Updated:** April 1, 2026  
**Version:** 2.0 (Multi-platform support)
