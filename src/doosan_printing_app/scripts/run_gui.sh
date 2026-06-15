#!/bin/bash

# Script để chạy hệ thống in 3D Doosan với GUI
# Sử dụng script này để khởi động giao diện điều khiển

echo "=== SMART3DX LAB - Doosan 5-Axis Printing System ==="
echo "Starting system with GUI..."

# Source ROS2 và workspace
source /opt/ros/humble/setup.bash
source /home/lehuythien/ros2_ws/doosan_in3d_ws/install/setup.bash

# Chạy node với GUI
python3 /home/lehuythien/ros2_ws/doosan_in3d_ws/run_with_gui.py "$@"