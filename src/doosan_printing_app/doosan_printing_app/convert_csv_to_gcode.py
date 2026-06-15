#!/usr/bin/env python3

import os
import sys
import argparse

def convert_csv_to_gcode(input_file: str, output_file: str):
    if not os.path.exists(input_file):
        print(f"Lỗi: Không tìm thấy file {input_file}")
        return

    try:
        with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
            # Ghi phần header chuẩn của file e_Gcode.txt
            header = """G21
G40
G49
G80
G90
M5
T1 M6
G54
(Position 1)
G94
"""
            f_out.write(header)

            line_count = 0
            for line in f_in:
                line = line.strip()
                # Bỏ qua các dòng trống hoặc dòng comment (bắt đầu bằng ;)
                if not line or line.startswith(';'):
                    continue
                
                parts = line.split(',')
                # Đảm bảo dòng có ít nhất 8 cột: X, Y, Z, RX, RY, RZ, E, F
                if len(parts) >= 8:
                    x, y, z, rx, ry, rz, e, f = parts[:8]
                    
                    # Dựa vào file e_Gcode.txt: 
                    # Trục xoay Y -> B
                    # Trục xoay Z -> C
                    # Lượng đùn E -> A
                    
                    out_line = f"G1 X{x} Y{y} Z{z} B{ry} C{rz} A{e} F{f}\n"
                    f_out.write(out_line)
                    line_count += 1
                    
            print(f"Đã chuyển đổi thành công {line_count} lệnh G-code.")
            print(f"File đầu ra được lưu tại: {output_file}")

    except Exception as e:
        print(f"Có lỗi xảy ra trong quá trình chuyển đổi: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chuyển đổi file Gcode định dạng CSV sang Gcode chuẩn Doosan")
    parser.add_argument('-i', '--input', type=str, default="Data_flie.gcode/ong2_new.gcode", help="Đường dẫn file đầu vào")
    parser.add_argument('-o', '--output', type=str, default="Data_Gcode_files/converted_gcode.txt", help="Đường dẫn file đầu ra")
    
    args = parser.parse_args()
    
    # Lấy đường dẫn tuyệt đối
    base_dir = os.path.dirname(os.path.abspath(__file__))
    in_path = os.path.join(base_dir, args.input) if not os.path.isabs(args.input) else args.input
    out_path = os.path.join(base_dir, args.output) if not os.path.isabs(args.output) else args.output
    
    # Tạo thư mục đầu ra nếu chưa có
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    convert_csv_to_gcode(in_path, out_path)
