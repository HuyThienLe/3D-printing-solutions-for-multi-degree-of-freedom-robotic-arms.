#!/bin/bash
# 🤖 SMART3DX LAB - Full System Launcher
# Chạy toàn bộ hệ thống: Arduino + Robot + GUI

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     SMART3DX LAB - 5 AXIS PRINTER CONTROL          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}\n"

# ========== STEP 1: Cấp quyền cho Arduino Port ==========
echo -e "${YELLOW}[STEP 1/3] Cấp quyền cho Arduino port...${NC}"
if [ -c /dev/ttyUSB0 ]; then
    sudo chmod 666 /dev/ttyUSB0
    echo -e "${GREEN}✓ Arduino port ready: /dev/ttyUSB0${NC}\n"
else
    echo -e "${RED}⚠ Warning: /dev/ttyUSB0 not found${NC}"
    echo -e "${YELLOW}   Kiểm tra Arduino có kết nối không${NC}\n"
fi

# ========== STEP 2: Khởi động Robot + RViz ==========
echo -e "${YELLOW}[STEP 2/3] Khởi động Robot Doosan A0509...${NC}"
echo -e "${BLUE}   Chạy: ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py${NC}"
echo -e "${YELLOW}   ⏳ Đang khởi động... (chờ ~10 giây)${NC}\n"

# Chạy ROS2 launch ở background
ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py model:=a0509 color:=blue &
ROBOT_PID=$!

# Chờ robot khởi động
sleep 10

echo -e "${GREEN}✓ Robot PID: $ROBOT_PID${NC}\n"

# ========== STEP 3: Khởi động Printer Node ==========
echo -e "${YELLOW}[STEP 3/3] Khởi động Printer Node với GUI...${NC}"
echo -e "${BLUE}   Chạy: ros2 run doosan_printing_app doosan_printer_node${NC}"
echo -e "${YELLOW}   GUI sẽ hiển thị trong vài giây...${NC}\n"

# Setup ROS2
cd /home/lehuythien/ros2_ws/doosan_in3d_ws
source install/setup.bash

# Chạy printer node (blocking)
export ENABLE_GUI=1
ros2 run doosan_printing_app doosan_printer_node

# ========== Cleanup ==========
echo -e "\n${YELLOW}Cleaning up...${NC}"
kill $ROBOT_PID 2>/dev/null || true
wait $ROBOT_PID 2>/dev/null || true

echo -e "${GREEN}✓ System shutdown complete${NC}"
