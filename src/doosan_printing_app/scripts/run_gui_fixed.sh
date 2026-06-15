#!/bin/bash

# Script để chạy GUI với Arduino connection
echo "=== SMART3DX LAB - GUI with Arduino ==="
echo "Starting GUI interface..."

cd /home/lehuythien/ros2_ws/doosan_in3d_ws

# Check if display is available
if [ -z "$DISPLAY" ]; then
    echo "Warning: No DISPLAY variable set. GUI may not work in headless environment."
    echo "Consider using: python3 control_terminal.py instead"
    echo ""
fi

# Run the GUI
python3 gui_simple.py