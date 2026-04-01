#!/bin/bash
# ROS2 Workspace Setup Script
# 
# This script installs ROS2 and necessary dependencies for the 
# Odin-Nav-Stack hexapod navigation system.

set -e  # Exit on error

echo "=================================="
echo " ROS2 Workspace Setup"
echo "=================================="
echo ""

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
    echo "Detected: $OS $VERSION"
else
    echo "Cannot detect OS. Exiting."
    exit 1
fi

# Check if ROS2 is already installed
if [ -d "/opt/ros/humble" ]; then
    echo "✓ ROS2 Humble already installed"
    ROS2_INSTALLED=true
elif [ -d "/opt/ros/foxy" ]; then
    echo "✓ ROS2 Foxy already installed"
    ROS2_INSTALLED=true
elif [ -d "/opt/ros/iron" ]; then
    echo "✓ ROS2 Iron already installed"
    ROS2_INSTALLED=true
else
    echo "✗ ROS2 not found"
    ROS2_INSTALLED=false
fi

if [ "$ROS2_INSTALLED" = false ]; then
    echo ""
    echo "Installing ROS2..."
    echo "This will install ROS2 Humble (recommended for Ubuntu 22.04)"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
    
    # Add ROS2 repository
    echo "Adding ROS2 repository..."
    sudo apt update
    sudo apt install -y software-properties-common
    sudo add-apt-repository universe
    sudo apt update && sudo apt install -y curl gnupg lsb-release
    
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg
    
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
        | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    
    # Install ROS2
    echo "Installing ROS2 Humble..."
    sudo apt update
    sudo apt install -y ros-humble-desktop
    
    echo "✓ ROS2 Humble installed"
fi

# Install colcon
echo ""
echo "Installing colcon build tools..."
sudo apt install -y python3-colcon-common-extensions

# Install ROS2 dependencies
echo ""
echo "Installing ROS2 dependencies..."
sudo apt install -y \
    ros-humble-geometry-msgs \
    ros-humble-sensor-msgs \
    ros-humble-nav-msgs \
    ros-humble-tf2-ros \
    ros-humble-tf2-geometry-msgs \
    ros-humble-cv-bridge \
    python3-opencv

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install --user torch numpy scipy cvxpy cvxpylayers loguru

echo ""
echo "=================================="
echo " Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Source ROS2:"
echo "   source /opt/ros/humble/setup.bash"
echo ""
echo "2. Add to ~/.bashrc for persistence:"
echo "   echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc"
echo "   echo 'export PYTHONPATH=/home/chuyuan/Odin-Nav-Stack/NeuPAN:\$PYTHONPATH' >> ~/.bashrc"
echo ""
echo "3. Build workspace:"
echo "   cd /home/chuyuan/Odin-Nav-Stack/ros2_ws"
echo "   colcon build"
echo "   source install/setup.bash"
echo ""
echo "4. Run NeuPAN node:"
echo "   ros2 run neupan_ros2 neupan_node"
echo ""
echo "See ros2_ws/README.md for full documentation."
echo ""
