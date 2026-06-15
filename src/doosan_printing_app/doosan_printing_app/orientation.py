#!/usr/bin/env python3

# ── HÀM CHUYỂN ĐỔI GÓC B-C (G-code) SANG RPY (robot Doosan) ───────────────────────
def bc_to_rpy(b_deg: float, c_deg: float) -> tuple[float, float, float]:

    rx = 0.0
    ry = 180.0 - b_deg   # B thực → góc nghiêng đầu phun (Pitch)
    rz = c_deg           # C thực → hướng của mũi in (Yaw)
    return rx, ry, rz

# Hàm unwrap_angle để xử lý góc quay qua 360 độ 
def unwrap_angle(current: float, previous: float) -> float:
    diff = current - previous
    while diff >  180.0:
        current -= 360.0
        diff = current - previous
    while diff < -180.0:
        current += 360.0
        diff = current - previous
    return current