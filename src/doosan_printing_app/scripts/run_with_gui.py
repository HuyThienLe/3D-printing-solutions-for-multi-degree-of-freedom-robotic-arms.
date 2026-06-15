#!/usr/bin/env python3

"""
Script để chạy doosan_printer_node với GUI
Đặt ENABLE_GUI=1 để GUI hiển thị
"""

import sys
import os

# Set GUI enabled TRƯỚC khi import
os.environ['ENABLE_GUI'] = '1'

# Thêm đường dẫn package vào Python path
sys.path.insert(0, '/home/lehuythien/ros2_ws/doosan_in3d_ws/install/doosan_printing_app/lib/python3.10/site-packages')
sys.path.insert(0, '/home/lehuythien/ros2_ws/doosan_in3d_ws/src/doosan_printing_app')

if __name__ == '__main__':
    import time
    import threading
    import rclpy
    from doosan_printing_app.doosan_printer_node import SmartPrinter5AxisPro
    
    print("=== SMART3DX LAB - GUI Mode ===")
    
    # Khởi tạo ROS2
    rclpy.init()
    
    # Tạo node
    node = SmartPrinter5AxisPro()
    
    # Chạy ROS2 spin trong thread
    def spin_ros2():
        try:
            rclpy.spin(node)
        except:
            pass
    
    threading.Thread(target=spin_ros2, daemon=True).start()
    
    # Chờ node khởi tạo
    time.sleep(2)
    
    # Khởi tạo và chạy GUI
    try:
        print("Starting GUI...")
        if node.gui_panel and hasattr(node.gui_panel, 'start_gui'):
            node.gui_panel.start_gui()  # Chạy MainLoop GUI
        else:
            print("ERROR: GUI panel not initialized!")
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        node.is_printing = False
        if node.arduino and node.arduino.is_open:
            node.arduino.close()
        node.destroy_node()
        rclpy.shutdown()
        print("System shutdown complete.")