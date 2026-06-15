#!/usr/bin/env python3

import re
import math
import os
from typing import NamedTuple
from . import config
from .orientation import bc_to_rpy, unwrap_angle

class PrintPoint(NamedTuple):
    x:     float   # mm — tọa độ robot 
    y:     float   # mm
    z:     float   # mm
    rx:    float   # degrees — Rx Doosan
    ry:    float   # degrees — Ry Doosan (180-B)
    rz:    float   # degrees — Rz Doosan 
    speed: float   # mm/s — tốc độ di chuyển của Doosan
    e:     float   # mm — LƯỢNG ĐÙN NHỰA TƯƠNG ĐỐI (Delta E)

def parse_gcode(filepath: str, start_line: int = 1) -> list[PrintPoint]:
   
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Không tìm thấy file G-code: {filepath}")

    with open(filepath, 'r') as f:
        lines = f.readlines()

    if not lines:
        raise ValueError(f"File G-code {filepath} đang trống!")

    if start_line > 1:
        print(f">>> Bỏ qua {start_line - 1} dòng đầu, bắt đầu đọc từ dòng {start_line}")
        lines = lines[start_line - 1:]

    # Trạng thái hiện tại (modal G-code: giữ giá trị từ lệnh trước)
    cur_x, cur_y, cur_z = 0.0, 0.0, 0.0
    cur_b, cur_c        = 0.0, 0.0
    cur_e               = 0.0     # BIẾN LƯU TỌA ĐỘ NHỰA TUYỆT ĐỐI HIỆN TẠI
    cur_f               = 1200.0  # mm/phút (giá trị mặc định nếu không có F)

    points: list[PrintPoint] = []
    
    # Khởi tạo biến cho Unwrap Angle
    first_point = True
    last_rx, last_ry, last_rz = 0.0, 0.0, 0.0

    for line in lines:
        line = line.strip().upper()

        # Bỏ qua dòng trống, comment, header
        if not line or line.startswith('(') or line.startswith(';') or line.startswith('O'):
            continue

        # --- BẮT LỆNH RESET BỘ ĐẾM NHỰA (G92 A0) ---
        if line.startswith('G92'):
            me_reset = re.search(r'A([-\d.]+)', line)
            if me_reset:
                cur_e = float(me_reset.group(1)) # Reset mốc nhựa về 0
            continue

        # Chỉ xử lý G0 / G1
        if not (line.startswith('G1') or line.startswith('G0')):
            continue

        # Parse từng field
        mx = re.search(r'X([-\d.]+)', line)
        my = re.search(r'Y([-\d.]+)', line)
        mz = re.search(r'Z([-\d.]+)', line)
        mb = re.search(r'B([-\d.]+)', line)
        mc = re.search(r'C([-\d.]+)', line)
        me = re.search(r'A([-\d.]+)', line)  # TÌM CHỮ 'A' ĐẠI DIỆN CHO NHỰA
        mf = re.search(r'F([-\d.]+)', line)

        pos_updated = False
        if mx: cur_x = float(mx.group(1)); pos_updated = True
        if my: cur_y = float(my.group(1)); pos_updated = True
        if mz: cur_z = float(mz.group(1)); pos_updated = True
        if mb: cur_b = float(mb.group(1)); pos_updated = True
        if mc: cur_c = float(mc.group(1)); pos_updated = True
        if mf: cur_f = float(mf.group(1))

        # --- TÍNH LƯỢNG NHỰA ĐÙN TƯƠNG ĐỐI (DELTA E) VÀ TĂNG LƯỢNG NHỰA ---
        delta_e = 0.0
        if me: 
            # Đã xóa lệnh replace('-', '') để đảm bảo không bị lỗi khi rút nhựa (Retraction)
            try:
                new_e = float(me.group(1))
                delta_e = new_e - cur_e  # Lấy nhựa MỚI trừ đi nhựa CŨ
                cur_e = new_e            # Cập nhật mốc CŨ thành mốc MỚI
                pos_updated = True
                
                # ========================================================
                # 1. TĂNG LƯỢNG NHỰA (FLOW RATE MULTIPLIER)
                # ========================================================
                if delta_e > 0:
                    FLOW_RATE = 1.6  # Hiện đang tăng 60% nhựa. (Có thể đổi thành 1.3, 1.5, 2.0 tùy ý)
                    delta_e = delta_e * FLOW_RATE
                    
            except ValueError:
                pass
        
        # Bỏ qua nếu dòng chỉ có F (không đổi vị trí hoặc đùn)
        if not pos_updated:
            continue

        # ── Giải ngược tọa độ S3_DeformFDM ─────────────────────────────────
        B_real = -cur_b          # độ (B thực của đầu in)
        C_real = -cur_c          # độ (C thực của đầu in)
        B_rad  = math.radians(B_real)
        C_rad  = math.radians(C_real)
        h      = config.TOOL_LENGTH  # mm — chiều dài đầu phun (Lấy từ config)

        # Giải ngược → tọa độ thực (px, py, pz) của bề mặt in:
        px = cur_x * math.cos(C_rad) + (cur_y + h * math.sin(B_rad)) * math.sin(C_rad)
        py = -cur_x * math.sin(C_rad) + (cur_y + h * math.sin(B_rad)) * math.cos(C_rad)
        pz = cur_z + h * (1.0 - math.cos(B_rad))

        # Áp dụng scale + offset sang hệ tọa độ robot Doosan
        final_x = px * config.SCALE + config.OFFSET_X
        final_y = py * config.SCALE + config.OFFSET_Y
        final_z = pz * config.SCALE + config.OFFSET_Z

        # Giải mã góc hướng
        rrx, rry, rrz = bc_to_rpy(B_real, C_real)

        # Gỡ rối góc xoay (Unwrap angle) để J6 không xoay 360 độ điên cuồng
        if first_point:
            last_rx, last_ry, last_rz = rrx, rry, rrz
            first_point = False
        else:
            rrx = unwrap_angle(rrx, last_rx)
            rry = unwrap_angle(rry, last_ry)
            rrz = unwrap_angle(rrz, last_rz)
            last_rx, last_ry, last_rz = rrx, rry, rrz

        # Chuyển đổi tốc độ từ mm/phút (Gcode) -> mm/giây (Doosan)
        speed_mms = cur_f / 60.0

       
        # 2. GIỚI HẠN TỐC ĐỘ IN CỦA ROBOT (ĐÃ NỚI LỎNG)
        # Chỉ áp dụng khi có lệnh đùn nhựa (đang in)
        if delta_e > 0:
            if speed_mms > 30.0:  # Giới hạn trên tăng từ 10.0 lên 30.0 mm/s
                speed_mms = 30.0
            elif speed_mms < 5.0: # Giới hạn dưới nới thành 5.0 mm/s
                speed_mms = 5.0

        pt = PrintPoint(
            x=final_x, y=final_y, z=final_z, 
            rx=rrx, ry=rry, rz=rrz, 
            speed=speed_mms,
            e=delta_e  # Đã truyền delta_e sau khi được nhân hệ số
        )
        points.append(pt)

    if len(points) < 3:
        raise ValueError("File G-code không chứa đủ điểm di chuyển X/Y/Z để in!")

    return points