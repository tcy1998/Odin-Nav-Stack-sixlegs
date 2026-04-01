# NeuPAN ROS2 Package

**Version:** 1.0.0  
**Robot:** Dobot Mini Hex V2  
**Framework:** ROS2

---

## Overview

This package provides the ROS2 implementation of **NeuPAN** (Neural Parallel Autonomy Navigation) for the Dobot hexapod robot. NeuPAN combines:

- **DUNE:** Neural distance predictor (trained offline)
- **NRMP:** MPC-based trajectory optimizer (runs online)

---

## Installation

### 1. Dependencies

```bash
# ROS2 system packages
sudo apt install \
  ros-humble-geometry-msgs \
  ros-humble-sensor-msgs \
  ros-humble-nav-msgs \
  ros-humble-tf2-ros \
  ros-humble-tf2-geometry-msgs

# Python packages
pip3 install torch numpy scipy cvxpy cvxpylayers
```

### 2. Build

```bash
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws
colcon build --packages-select neupan_ros2
source install/setup.bash
```

---

## Usage

### Run NeuPAN Node

```bash
# Source workspace
source /home/chuyuan/Odin-Nav-Stack/ros2_ws/install/setup.bash

# Add NeuPAN to PYTHONPATH
export PYTHONPATH=/home/chuyuan/Odin-Nav-Stack/NeuPAN:$PYTHONPATH

# Run node
ros2 run neupan_ros2 neupan_node
```

### Send Goal

```bash
# Send goal position (x, y, yaw)
ros2 topic pub --once /goal geometry_msgs/PoseStamped '{
  header: {frame_id: "map"},
  pose: {
    position: {x: 5.0, y: 3.0, z: 0.0},
    orientation: {w: 1.0}
  }
}'
```

---

## Topics

### Subscriptions

| Topic | Type | Description |
|-------|------|-------------|
| `/scan` | `sensor_msgs/LaserScan` | 2D laser scan (processed from lidar) |
| `/goal` | `geometry_msgs/PoseStamped` | Goal position in map frame |
| `/path` | `nav_msgs/Path` | Initial path (optional) |
| `/waypoints` | `nav_msgs/Path` | Waypoints to follow |
| `/neupan/q_s` | `std_msgs/Float32` | Tune parameter q_s |
| `/neupan/p_u` | `std_msgs/Float32` | Tune parameter p_u |

### Publications

| Topic | Type | Description |
|-------|------|-------------|
| `/vel_cmd` | `geometry_msgs/Twist` | Velocity command to robot |
| `/neupan_plan` | `nav_msgs/Path` | Optimized trajectory |
| `/neupan_ref_state` | `nav_msgs/Path` | Reference state |
| `/neupan_initial_path` | `nav_msgs/Path` | Initial path |
| `/arrive` | `std_msgs/Empty` | Signal when goal reached |

---

## Configuration

### config.yaml

Located in `config/config.yaml`:

```yaml
frame:
  map: "map"
  base: "link_trunk"
  lidar: "livox_frame"

topic:
  cmd_vel: "/vel_cmd"
  scan: "/scan"
  goal: "/goal"
  path: "/path"
  waypoints: "/waypoints"
  arrive: "/arrive"

scan_angle: [-3.14159, 3.14159]  # Full 360°
scan_range: [0.1, 10.0]  # meters
scan_downsample: 1
flip_angle: false

planner_config_file: "configs/planner.yaml"
dune_checkpoint: "example/dune_train/model/dobot_hex_v2/model_5000.pth"
```

### planner.yaml

Located in `config/planner.yaml` (use existing from NeuPAN/neupan/ros/configs/planner.yaml):

```yaml
ref_speed: 0.2
max_speed: [0.2, 0.28]  # [linear, angular]
robot:
  length: 0.5
  width: 0.1275
  min_radius: 0.15
collision_threshold: 0.3
dune_checkpoint: "example/dune_train/model/dobot_hex_v2/model_5000.pth"
```

---

## Parameters

### Runtime Tuning

Adjust parameters during runtime:

```bash
# Increase smoothness weight (default: ~1.0)
ros2 topic pub /neupan/q_s std_msgs/Float32 "data: 2.0"

# Increase urgency (default: ~1 0)
ros2 topic pub /neupan/p_u std_msgs/Float32 "data: 1.5"
```

---

## Troubleshooting

### Error: "NeuPAN module not found"

**Solution:**
```bash
export PYTHONPATH=/home/chuyuan/Odin-Nav-Stack/NeuPAN:$PYTHONPATH
```

Add to `~/.bashrc` for persistence.

---

### Error: "config.yaml not found"

**Solution:** Copy config files:
```bash
cd /home/chuyuan/Odin-Nav-Stack/ros2_ws/src/neupan_ros2
mkdir -p config
cp /home/chuyuan/Odin-Nav-Stack/NeuPAN/neupan/ros/configs/*.yaml config/
```

---

### Error: "DUNE checkpoint not found"

**Solution:** Check model path:
```bash
ls -lh /home/chuyuan/Odin-Nav-Stack/NeuPAN/example/dune_train/model/dobot_hex_v2/model_5000.pth
```

If missing, training is incomplete. See `HEXAPOD_MIGRATION_GUIDE.md`.

---

### Warning: "No obstacle points"

**Cause:** No `/scan` data received.

**Check:**
```bash
# Check if scan topic exists
ros2 topic list | grep scan

# Monitor scan data
ros2 topic echo /scan
```

**Solution:** Start lidar node or bridge from ROS2 hexapod lidar.

---

### Warning: "Could not transform"

**Cause:** TF tree not complete.

**Check:**
```bash
# View TF tree
ros2 run tf2_tools view_frames

# Check specific transform
ros2 run tf2_ros tf2_echo map link_trunk
```

**Solution:** Ensure localization node is publishing TF transforms.

---

## Development

### File Structure

```
neupan_ros2/
├── package.xml          # Package metadata
├── setup.py             # Python setup
├── setup.cfg            # Install config
├── resource/            # Resource markers
├── neupan_ros2/         # Python module
│   ├── __init__.py      # Package init
│   ├── neupan_node.py   # Main planner node
│   └── dune_node.py     # DUNE inference node (TODO)
├── launch/              # Launch files (TODO)
├── config/              # Configuration files
│   ├── config.yaml      # Node config
│   └── planner.yaml     # Planner config
└── README.md            # This file
```

---

### Next Steps

- [ ] Copy config files from NeuPAN
- [ ] Implement visualization markers
- [ ] Create launch files
- [ ] Add DUNE standalone node
- [ ] Integration testing with hexapod

---

## Related Packages

- **hexapod_bridge:** ROS1↔ROS2 bridge (temporary)
- **yolo_ros2:** Object detection for ROS2
- **navigation_planner:** A* global planner

---

**Author:** tcy1998  
**License:** MIT  
**Original:** Ruihua Han, Hongle Mo (ROS1)
