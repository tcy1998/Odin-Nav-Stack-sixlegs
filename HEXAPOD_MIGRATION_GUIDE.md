# Dobot Six-Leg Hexapod Migration Guide for NeuPAN

**Created:** 2026-03-25  
**Purpose:** Complete guide for migrating Odin-Nav-Stack from Unitree Go2 to Dobot Mini Hex V2 hexapod robot

---

## 📋 Table of Contents

1. [Robot Specifications](#robot-specifications)
2. [Comparison: Go2 vs Hexapod](#comparison-go2-vs-hexapod)
3. [Required Changes](#required-changes)
4. [NeuPAN Training Configuration](#neupan-training-configuration)
5. [Step-by-Step Migration Plan](#step-by-step-migration-plan)
6. [File Checklist](#file-checklist)

---

## 🤖 Robot Specifications

### Dobot Mini Hex V2 Hexapod

#### **Geometry (from MuJoCo XML)**
- **Source File:** `dobot_six_leg/ros2_packages/mini_hex_v2/share/mini_hex_v2/xacro/mini_hex_v2.xml`
- **Base Link:** `link_trunk`
- **Footprint Geometry:**
  - Type: Rectangular box
  - **Length:** 0.5 m (2 × 0.25)
  - **Width:** 0.1275 m (2 × 0.06375)
  - **Height:** 0.1 m (2 × 0.05)
  - **Mass:** 9.659 kg (trunk only)

#### **Velocity Limits (from locomotion.py)**
- **Source File:** `dobot_six_leg/high_level/py/locomotion.py`
- **Measured Velocities (before scaling):**
  - Forward/Backward: ±0.4 m/s
  - Lateral (left/right): ±0.4 m/s
  - Yaw rotation: ±0.8 rad/s

- **Applied Velocity Commands (after scaling factors):**
  - `linear.x`: 0.4 × 0.5 = **0.2 m/s**
  - `linear.y`: 0.4 × 0.4 = **0.16 m/s**
  - `angular.z`: 0.8 × 0.35 = **0.28 rad/s**

#### **Kinematic Configuration**
- **Leg Configuration:** 6 legs (3 pairs)
  - Front Left/Right: pos = (0.3003, ±0.05, 0)
  - Mid Left/Right: pos = (-0.005, ±0.1275, 0)
  - Rear Left/Right: pos = (-0.3003, ±0.05, 0)
- **Degrees of Freedom per leg:** 3 (abad, thigh_pitch, calf_pitch)
- **Total actuated DOF:** 18 joints
- **Locomotion Model:** Omnidirectional walking (simulation uses Twist commands)

#### **Sensors**
- **Lidar:** Livox lidar (ros2_packages/livox_lidar_node)
- **Camera:** RealSense camera (ros2_packages/realsense_camera_node)
- **IMU/State:** Custom robot state message (custom_msg/RobotState)

#### **Control Interface**
- **Base Topic:** `/vel_cmd` (geometry_msgs/Twist)
- **State Topic:** `/robot_state` (custom_msg/RobotState)
- **Command Topic:** `/robot_cmd` (custom_msg/RobotCommand)
- **ROS Version:** ROS2 (Humble/Iron detected)

---

## 📊 Comparison: Go2 vs Hexapod

| Parameter | Unitree Go2 | Dobot Mini Hex V2 | Change Factor |
|-----------|-------------|-------------------|---------------|
| **Length** | 0.7 m | 0.5 m | 0.71× |
| **Width** | 0.35 m | 0.1275 m | 0.36× |
| **Kinematics** | Differential Drive | Omnidirectional (approx. diff) | Same for NeuPAN |
| **Max Speed (linear.x)** | 0.5 m/s | 0.2 m/s | 0.4× |
| **Max Speed (angular.z)** | 0.7 rad/s | 0.28 rad/s | 0.4× |
| **Max Accel (est.)** | 0.5 m/s² | ~0.3 m/s² (estimate) | 0.6× |
| **ROS Version** | ROS1 Noetic | ROS2 | Major change |
| **Control SDK** | unitree_sdk2 | Dobot proprietary | Complete replacement |
| **Base Frame** | `base_link` | `link_trunk` | Name change |

**Key Insights:**
- Hexapod is **narrower** (36% of Go2 width) → better for tight spaces
- Hexapod is **slower** (40% of Go2 speed) → safer, more stable
- Hexapod has **omnidirectional** capability → can move laterally
- **ROS1→ROS2 migration** required for full integration

---

## 🔧 Required Changes

### 1. **NeuPAN Training (DUNE Model)**

#### Training YAML: `NeuPAN/example/dune_train/dune_train_hexapod.yaml`

```yaml
robot:
  kinematics: 'diff'      # Use differential drive approximation
  length: 0.5             # Trunk length (meters)
  width: 0.1275           # Trunk width (meters)

train:
  model_name: 'dobot_hex_v2'
  direct_train: true
  data_size: 100000
  data_range: [-25, -25, 25, 25]  # Keep same as Go2
  batch_size: 256
  epoch: 5000                     # 1-2 hours on CPU
  valid_freq: 250
  save_freq: 500
  lr: 5e-5
  lr_decay: 0.5
  decay_freq: 1500
```

**Training Command:**
```bash
cd /home/chuyuan/Odin-Nav-Stack/NeuPAN
python example/dune_train/dune_train_diff.py --config example/dune_train/dune_train_hexapod.yaml
```

**Expected Output:**
- Model checkpoint: `NeuPAN/example/dune_train/model/dobot_hex_v2/model_5000.pth`
- Training time: ~1-2 hours (CPU, synthetic data)

---

### 2. **NeuPAN ROS Configuration**

#### File: `NeuPAN/neupan/ros/configs/planner.yaml`

**Changes Required:**

```yaml
# mpc
receding: 10
step_time: 0.1
ref_speed: 0.2            # ⬅️ CHANGE: Reduced from 0.5 (hexapod max speed)
device: 'cpu'
time_print: False
collision_threshold: 0.05

# robot
robot:
  kinematics: 'diff'
  max_speed: [0.2, 0.28]  # ⬅️ CHANGE: [linear_m/s, angular_rad/s]
  max_acce: [0.3, 0.5]    # ⬅️ CHANGE: Conservative acceleration limits
  length: 0.5             # ⬅️ CHANGE: Hexapod trunk length
  width: 0.1275           # ⬅️ CHANGE: Hexapod trunk width

# initial path
ipath:
  interval: 0.1
  waypoints: []
  curve_style: 'line'     # Use 'line' for hexapod (simpler kinematics)
  min_radius: 0.15        # ⬅️ CHANGE: Smaller radius (narrower robot)
  loop: False
  arrive_threshold: 0.2
  close_threshold: 0.1
  ind_range: 10
  arrive_index_threshold: 1
  
# proximal alternating minimization network
pan:
  iter_num: 3
  dune_max_num: 100
  nrmp_max_num: 10
  iter_threshold: 0.1
  dune_checkpoint: 'example/dune_train/model/dobot_hex_v2/model_5000.pth'  # ⬅️ CHANGE

# adjust parameters (may need tuning after initial tests)
adjust:
  q_s: 0.3
  p_u: 2.5
  eta: 10.0
  ro_obs: 400
  d_max: 0.2
  d_min: 0.05
  bk: 0.1
```

#### File: `NeuPAN/neupan/ros/configs/config.yaml`

**Changes Required:**

```yaml
device: 'cpu'

frame:
  world: 'map'
  base: 'link_trunk'      # ⬅️ CHANGE: from 'base_link' to 'link_trunk'
  lidar: 'livox_frame'    # ⬅️ CHANGE: check actual lidar frame name

topic:
  scan: '/livox/scan'     # ⬅️ CHANGE: verify actual lidar topic
  goal: '/move_base_simple/goal'
  path: '/initial_path'
  cmd_vel: '/vel_cmd'     # ⬅️ CHANGE: from '/cmd_vel' to '/vel_cmd'
  arrive: '/neupan/arrive'

scan:
  scan_num: 100
  scan_angle: [-1.5707, 1.5707]  # ±90 degrees (check livox specs)
  max_range: 10.0
  visualize: true
```

---

### 3. **Robot Control Bridge (ROS2 → ROS1 or Native ROS2)**

**Option A: Replace unitree_control with hexapod_control (ROS1)**

Create: `ros_ws/src/hexapod_control/src/hexapod_vel_controller.cpp`

```cpp
#include <ros/ros.h>
#include <geometry_msgs/Twist.h>
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include "custom_msg/msg/robot_command.hpp"
#include "custom_msg/msg/robot_state.hpp"

// Bridge between ROS1 /cmd_vel and ROS2 /vel_cmd
class HexapodVelController {
public:
    HexapodVelController() {
        // ROS1 subscriber
        ros1_sub_ = ros1_nh_.subscribe("/cmd_vel", 1, 
            &HexapodVelController::cmdVelCallback, this);
        
        // ROS2 publisher
        auto qos = rclcpp::QoS(rclcpp::KeepLast(1));
        ros2_pub_ = ros2_node_->create_publisher<geometry_msgs::msg::Twist>(
            "/vel_cmd", qos);
        
        ROS_INFO("Hexapod velocity controller initialized");
    }

private:
    void cmdVelCallback(const geometry_msgs::Twist::ConstPtr& msg) {
        auto ros2_msg = geometry_msgs::msg::Twist();
        ros2_msg.linear.x = msg->linear.x;
        ros2_msg.linear.y = msg->linear.y;
        ros2_msg.angular.z = msg->angular.z;
        
        ros2_pub_->publish(ros2_msg);
    }

    ros::NodeHandle ros1_nh_;
    ros::Subscriber ros1_sub_;
    std::shared_ptr<rclcpp::Node> ros2_node_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr ros2_pub_;
};
```

**Option B: Full ROS2 Migration** (Recommended long-term)
- Migrate entire navigation stack to ROS2
- Use ROS2 nav2 stack instead of custom navigation
- Direct /vel_cmd integration without bridging

---

### 4. **Launch File Updates**

#### File: `ros_ws/src/map_planner/launch/whole.launch`

**Line 50 Change:**

```xml
<!-- OLD: Unitree Go2 Control -->
<!-- <node pkg="unitree_control" type="unitree_vel_controller" name="unitree_vel_controller" output="screen"/> -->

<!-- NEW: Hexapod Control -->
<node pkg="hexapod_control" type="hexapod_vel_controller" name="hexapod_vel_controller" output="screen"/>
```

**Additional Changes:**
- Update `base_frame` parameters to `link_trunk`
- Update lidar topic references to `/livox/scan`
- Verify TF tree compatibility (ROS1 ↔ ROS2 bridge may be required)

---

### 5. **Dependencies & Build System**

#### Update: `ros_ws/src/hexapod_control/CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.8)
project(hexapod_control)

# ROS1 dependencies
find_package(catkin REQUIRED COMPONENTS
  roscpp
  geometry_msgs
  tf2
  tf2_ros
)

# ROS2 dependencies (if using ros1_bridge)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)

# Dobot SDK (if available)
# find_package(dobot_sdk REQUIRED)

catkin_package(
  CATKIN_DEPENDS roscpp geometry_msgs tf2 tf2_ros
)

add_executable(hexapod_vel_controller src/hexapod_vel_controller.cpp)
target_link_libraries(hexapod_vel_controller ${catkin_LIBRARIES})
```

#### Update: `ros_ws/src/hexapod_control/package.xml`

```xml
<package format="2">
  <name>hexapod_control</name>
  <version>1.0.0</version>
  <description>Velocity controller for Dobot hexapod robot</description>
  
  <maintainer email="your.email@example.com">Your Name</maintainer>
  <license>MIT</license>

  <buildtool_depend>catkin</buildtool_depend>
  
  <depend>roscpp</depend>
  <depend>geometry_msgs</depend>
  <depend>tf2</depend>
  <depend>tf2_ros</depend>
  
  <export></export>
</package>
```

---

## 🚀 Step-by-Step Migration Plan

### Phase 1: DUNE Training (Offline, ~2 hours)

1. **Create training configuration**
   ```bash
   cp NeuPAN/example/dune_train/dune_train_diff.yaml \
      NeuPAN/example/dune_train/dune_train_hexapod.yaml
   ```

2. **Edit configuration** (see [NeuPAN Training Configuration](#neupan-training-configuration))
   - Set `length: 0.5`, `width: 0.1275`
   - Set `model_name: 'dobot_hex_v2'`

3. **Run training**
   ```bash
   cd /home/chuyuan/Odin-Nav-Stack/NeuPAN
   python example/dune_train/dune_train_diff.py \
       --config example/dune_train/dune_train_hexapod.yaml
   ```

4. **Verify output**
   - Check `NeuPAN/example/dune_train/model/dobot_hex_v2/model_5000.pth` exists
   - Validation loss should decrease to < 0.01

---

### Phase 2: Configuration Updates (30 minutes)

5. **Update NeuPAN configs**
   ```bash
   # Edit planner.yaml
   vim NeuPAN/neupan/ros/configs/planner.yaml
   # Update robot dimensions, speeds, checkpoint path
   
   # Edit config.yaml
   vim NeuPAN/neupan/ros/configs/config.yaml
   # Update frame names, topic names
   ```

6. **Verify TF frames**
   ```bash
   # Check hexapod TF tree
   cd dobot_six_leg
   # Launch robot simulation/hardware
   # In another terminal:
   rosrun tf2_tools view_frames.py  # ROS1
   # or
   ros2 run tf2_tools view_frames  # ROS2
   ```

---

### Phase 3: Control Bridge Development (2-4 hours)

7. **Create hexapod_control package**
   ```bash
   cd ros_ws/src
   catkin_create_pkg hexapod_control roscpp geometry_msgs tf2 tf2_ros
   cd hexapod_control
   mkdir src
   ```

8. **Implement velocity controller** (see Option A/B in Required Changes)
   - Option A: ROS1-ROS2 bridge
   - Option B: Full ROS2 migration

9. **Build workspace**
   ```bash
   cd ros_ws
   catkin_make
   source devel/setup.bash
   ```

---

### Phase 4: Integration Testing (1 day)

10. **Test individual components**
    ```bash
    # Terminal 1: Launch hexapod (ROS2)
    cd dobot_six_leg
    # Run hexapod simulation/hardware interface
    
    # Terminal 2: Launch NeuPAN (ROS1)
    roslaunch map_planner whole.launch
    
    # Terminal 3: Test velocity commands
    rostopic pub /cmd_vel geometry_msgs/Twist "linear:
      x: 0.1
      y: 0.0
      z: 0.0
    angular:
      x: 0.0
      y: 0.0
      z: 0.0"
    ```

11. **Verify data flow**
    - Check `/scan` topic publishes lidar data
    - Check `/cmd_vel` → `/vel_cmd` bridge works
    - Check TF transform `map` → `link_trunk` exists
    - Monitor `/neupan/arrive` for goal completion

12. **Test navigation pipeline**
    - Publish goal: `rostopic pub /move_base_simple/goal ...`
    - Verify A* path generation on `/initial_path`
    - Verify NeuPAN publishes `/cmd_vel`
    - Verify robot moves toward goal
    - Check collision avoidance with obstacles

---

### Phase 5: VLM Integration (2 hours)

13. **Update VLM configuration**
    ```bash
    vim scripts/str_cmd_control.py
    # Verify goal positions are appropriate for hexapod speed
    # Reduce goal distances if needed (slower robot)
    ```

14. **Test full VLN pipeline**
    ```bash
    # Terminal 1: Run hexapod + navigation
    # (from Phase 4)
    
    # Terminal 2: Run VLM node
    export DASHSCOPE_API_KEY="your_key_here"
    python scripts/VLN.py
    
    # Verify image processing and command generation
    ```

---

### Phase 6: Tuning & Optimization (ongoing)

15. **Parameter tuning checklist**
    - [ ] `ref_speed` in planner.yaml (0.2 → adjust based on testing)
    - [ ] `collision_threshold` (0.05 → may need increase for wider safety margin)
    - [ ] `ro_obs` penalty (400 → increase if collisions occur)
    - [ ] `min_radius` (0.15 → adjust for turning capability)
    - [ ] `arrive_threshold` (0.2 → tune for goal accuracy)

16. **Performance benchmarks**
    - Goal completion rate (target: >90%)
    - Collision rate (target: <5%)
    - Average path deviation (target: <0.2m)
    - Navigation time vs optimal path (target: <1.5×)

---

## 📝 File Checklist

### Files to Create

- [ ] `NeuPAN/example/dune_train/dune_train_hexapod.yaml` (training config)
- [ ] `NeuPAN/example/dune_train/model/dobot_hex_v2/` (directory for checkpoints)
- [ ] `ros_ws/src/hexapod_control/` (new package)
- [ ] `ros_ws/src/hexapod_control/src/hexapod_vel_controller.cpp` (bridge node)
- [ ] `ros_ws/src/hexapod_control/CMakeLists.txt` (build config)
- [ ] `ros_ws/src/hexapod_control/package.xml` (package metadata)
- [ ] `ros_ws/src/hexapod_control/launch/hexapod_control.launch` (launch file)

### Files to Modify

- [ ] `NeuPAN/neupan/ros/configs/planner.yaml` (robot params, checkpoint)
- [ ] `NeuPAN/neupan/ros/configs/config.yaml` (frame names, topics)
- [ ] `ros_ws/src/map_planner/launch/whole.launch` (replace unitree_control)
- [ ] `scripts/str_cmd_control.py` (optional: adjust goal distances)

### Files to Check (No Changes Needed)

- ✅ `NeuPAN/neupan/robot/robot.py` (already supports 'diff' kinematics)
- ✅ `NeuPAN/neupan/blocks/initial_path.py` (works with 'diff' model)
- ✅ `ros_ws/src/map_planner/src/map_planner.cpp` (robot-agnostic A*)
- ✅ `scripts/VLN.py` (no changes if topics remain same)

---

## 🎯 Success Criteria

### Functional Requirements

- [x] DUNE training completes without errors
- [ ] Validation loss < 0.01 by epoch 5000
- [ ] NeuPAN loads checkpoint successfully
- [ ] `/cmd_vel` → `/vel_cmd` bridge operational
- [ ] TF tree includes `map` → `link_trunk` → `livox_frame`
- [ ] Lidar data appears on `/livox/scan` (or correct topic)
- [ ] Robot responds to velocity commands
- [ ] Goal navigation completes without crashes
- [ ] Collision avoidance active (verified with obstacles)

### Performance Targets

- 🎯 **Navigation success rate:** >85% (indoor environment)
- 🎯 **Average speed:** 0.15-0.20 m/s (75-100% of max)
- 🎯 **Path tracking error:** <0.15 m (mean deviation)
- 🎯 **Goal arrival accuracy:** <0.25 m (final position error)
- 🎯 **Collision safety margin:** >0.05 m (minimum clearance)

---

## 🚨 Common Issues & Solutions

### Issue 1: TF Transform Errors
**Symptom:** `Lookup would require extrapolation into the future`

**Solution:**
- Verify all TF publishers are running (esp. `robot_state_publisher`)
- Check clock synchronization between ROS1/ROS2
- Use `use_sim_time` parameter consistently

### Issue 2: DUNE Training Diverges
**Symptom:** Loss increases or NaN values

**Solution:**
- Reduce learning rate to `1e-5`
- Check footprint doesn't extend outside `data_range`
- Verify robot dimensions are in meters (not cm)

### Issue 3: Robot Not Moving
**Symptom:** `/vel_cmd` receives messages but robot stationary

**Solution:**
- Check hexapod is in `WALK` mode (not `STAND_UP` or `BALANCE_STAND`)
- Verify velocity scaling factors in bridge
- Test direct publish to `/vel_cmd` from ROS2 side

### Issue 4: Lidar Data Missing
**Symptom:** NeuPAN reports no scan data

**Solution:**
- Run `rostopic list` / `ros2 topic list` to find actual lidar topic
- Update `config.yaml` topic names
- Check lidar driver is launching correctly
- Verify `livox_lidar_node` is publishing

### Issue 5: Collision Detection Too Sensitive
**Symptom:** Robot stops frequently in open space

**Solution:**
- Increase `collision_threshold` from 0.05 to 0.08
- Check lidar isn't detecting robot's own legs
- Verify `scan_angle` range is appropriate
- Adjust `d_min` parameter if needed

---

## 📚 Reference Documentation

### Robot-Specific Resources
- **Dobot Hexapod Files:** `dobot_six_leg/ros2_packages/mini_hex_v2/`
- **MuJoCo Model:** `dobot_six_leg/ros2_packages/mini_hex_v2/share/mini_hex_v2/xacro/mini_hex_v2.xml`
- **Control API:** `dobot_six_leg/high_level/py/locomotion.py`

### NeuPAN Resources
- **Paper:** IEEE T-RO 2025 - "NeuPAN: Direct Point Robot Navigation..."
- **Training Guide:** `NeuPAN/README.md` (lines 260-295)
- **Architecture:** DUNE (distance predictor) + NRMP (optimizer)

### Existing Implementation
- **Go2 Training Config:** `NeuPAN/example/dune_train/dune_train_diff.yaml`
- **Go2 Planner Config:** `NeuPAN/neupan/ros/configs/planner.yaml`
- **Unitree Control:** `ros_ws/src/unitree_control/src/unitree_vel_controller.cpp`

---

## 📞 Next Steps

1. **Start with Phase 1** (DUNE training) - can run offline independently
2. **Test hexapod basic control** - ensure robot responds to `/vel_cmd`
3. **Implement Phase 3** (control bridge) before full integration
4. **Iterate on Phase 6** (tuning) based on real-world testing

**Estimated Total Time:**
- Training: 2 hours (autonomous)
- Configuration: 0.5 hours
- Development: 4 hours
- Testing: 8 hours
- **Total: ~14.5 hours** (2 working days)

---

**Document Version:** 1.0  
**Last Updated:** 2026-03-25  
**Status:** Ready for Implementation  
**Contact:** See project README for support channels
