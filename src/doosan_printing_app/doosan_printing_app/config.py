#!/usr/bin/env python3

# ── CẤU HÌNH CHO ỨNG DỤNG IN 3D BẰNG ROBOT DOOSAN 

# ── VỊ TRÍ BÀN IN (offset từ gốc robot đến góc dưới-trái của vùng in) 
OFFSET_X = -400.90   # mm — dịch chuyển X (sang phải)
OFFSET_Y = 16.91    # mm — dịch chuyển Y (ra xa)
OFFSET_Z = 250.00   # mm — chiều cao an toàn (Z=0 của G-code = Z=250 robot)
SCALE       = 1.0     # tỷ lệ scale (1.0 = không thay đổi kích thước)

# ── THÔNG SỐ ĐẦU PHUN 
TOOL_LENGTH = 0.0     # mm — chiều dài từ flange robot đến đầu phun (h)
                

# ── CHUYỂN ĐỘNG
# 1. Tuyệt đối không để bằng 0. Nâng lên 0.5mm để kích hoạt chế độ bo cua (Blending) của Doosan.
RADIUS    = 1.0    # mm — bán kính bo cua giữa các đoạn

# 2. Hạ gia tốc tối đa xuống 100.0 mm/s² để triệt tiêu lực quán tính giật gắt 
MAX_ACCEL = 100.0  # mm/s² — giới hạn gia tốc bảo vệ khớp robot

# ── HOME POSITION (góc khớp khi về home) 
HOME_JOINTS     = [176.0, -2.31, 91.11, 3.57, 89.45, 0.0]  # degrees

# =========================================================================
# FIX LỖI RUNG LẮC KHI CHƯA IN (LỆNH HOME GIẬT CỤC)
# =========================================================================
# Hạ thấp xuống 10% - 15% để robot khởi hành nhẹ nhàng, lướt từ từ về HOME
# Triệt tiêu hoàn toàn cú giật cơ học ban đầu.
HOME_VEL        = 50.0   # % vận tốc tối đa khi về HOME
HOME_ACC        = 50.0   # % gia tốc tối đa khi về HOME
# =========================================================================

# ── ROS2 SERVICE TOPICS (Dùng cho Driver Doosan chính hãng)
TOPIC_MOVE_LINE  = '/dsr01/motion/move_line'
TOPIC_MOVE_JOINT = '/dsr01/motion/move_joint'
TOPIC_RVIZ       = '/hienthi_duongin_mophong'

# ── FILE G-CODE MẶC ĐỊNH (Đã sửa đường dẫn chuẩn cho máy lehuythien)
import os
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_GCODE_FILE = '/home/lehuythien/ros2_ws/doosan_in3d_ws/src/doosan_printing_app/doosan_printing_app/Data_Gcode_files/ankleBaseV1_Gcode.txt'

# ── STREAMING LOG 
LOG_EVERY_N_POINTS = 20   # in thông tin streaming mỗi N điểm
LOG_LINE_WIDTH     = 120  # chiều rộng dòng log (để \r xóa gọn)

# ── ARDUINO / EXTRUDER
ARDUINO_BAUDRATE = 115200
ARDUINO_PORTS = [
    '/dev/ttyUSB0',
    '/dev/ttyUSB1',
    '/dev/ttyUSB2',
    '/dev/ttyACM0',
    '/dev/ttyACM1',
    '/dev/ttyAMA0',
]
ARDUINO_SEARCH_GLOBS = ['/dev/ttyUSB*', '/dev/ttyACM*']