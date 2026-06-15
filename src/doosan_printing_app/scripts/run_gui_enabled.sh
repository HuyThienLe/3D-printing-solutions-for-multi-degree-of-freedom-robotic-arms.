#!/bin/bash
# Chạy Doosan Printing App với GUI được bật

# Thiết lập môi trường
source /home/lehuythien/ros2_ws/doosan_in3d_ws/install/setup.bash

echo "==================================="
echo "🎨 Smart3Dx Lab - GUI Enabled"
echo "==================================="
echo ""
echo "✓ GUI được bật mặc định"
echo "✓ Giao diện sẽ hiển thị trong vài giây"
echo ""

# Chặn chờ một chút để chắc chắn môi trường đã sẵn sàng
sleep 1

# Chạy node với ENABLE_GUI=1 (hoặc mặc định nếu đã cấu hình)
export ENABLE_GUI=1
ros2 run doosan_printing_app doosan_printer_node
