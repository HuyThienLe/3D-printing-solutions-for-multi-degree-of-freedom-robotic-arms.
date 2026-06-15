#!/usr/bin/env python3

import sys
import time
import os
import glob
import serial 
import threading # Bắt buộc phải có để chạy ngầm GUI và ROS

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

try:
    from . import config
    from .gcode_parser import parse_gcode
    from .orientation import unwrap_angle
    from .robot_controller import DoosanRobotController
    from .printhead_gui import PrintHeadControlPanel # <--- IMPORT BẢNG ĐIỀU KHIỂN
except ImportError:
    import config
    from gcode_parser import parse_gcode
    from orientation import unwrap_angle
    from robot_controller import DoosanRobotController
    from printhead_gui import PrintHeadControlPanel # <--- IMPORT BẢNG ĐIỀU KHIỂN

class SmartPrinter5AxisPro(Node):
    def __init__(self):
        super().__init__('smart_printer_5axis_pro')
        self.get_logger().info(">>> KHOI DONG: SMART3DX LAB - 5-AXIS PRINTING APP <<<")

        # Auto-detect Arduino port
        self.arduino_port = self._detect_arduino_port()
        self.baudrate = 115200
        self.arduino = None  
        self.current_temp_str = "0.0" 
        self.arduino_status = "INIT"
        self.is_printing = False
        self.is_paused = False
        self.should_stop = False
        self.speed_scale_pct = 100.0
        self.fan_speed_pct = 0
        self.target_temp = 250
        self.robot_status = "Waiting"
        self.selected_file = None
        self.total_points = 0
        self.current_point = 0
        self.print_start_time = None
        
        # KHỞI TẠO GUI ĐẦU IN
        self.gui_panel = PrintHeadControlPanel(
            self.gui_lenh_arduino,
            home_callback=self.gui_lenh_home,
            speed_callback=self.gui_lenh_set_speed,
            file_callback=self.gui_lenh_select_file,
            fan_callback=self.gui_lenh_set_fan,
            start_callback=self.gui_lenh_start_print,
            pause_callback=self.gui_lenh_pause_resume,
            stop_callback=self.gui_lenh_stop,
            temp_callback=self.gui_lenh_set_temp,
            robot_status_callback=self.get_robot_status,
        )
        # GUI sẽ được khởi tạo trong main() để tránh conflict với ROS2 launcher

        try:
            self.arduino = serial.Serial(self.arduino_port, self.baudrate, timeout=0.01) 
            time.sleep(2.0) 
            self.arduino.reset_input_buffer() 
            self.get_logger().info(f">>> ĐÃ KẾT NỐI ARDUINO TẠI {self.arduino_port} <<<")
            
            # Khởi chạy luồng đọc Serial ngầm
            threading.Thread(target=self._serial_read_thread, daemon=True).start()

        except Exception as e:
            self.get_logger().error(f"!!! KHÔNG THỂ KẾT NỐI ARDUINO: {e} !!!")

        self.controller = DoosanRobotController(self) 
        if not self.controller.wait_cho_robot_ket_noi(1.0): 
            self.get_logger().error("KHÔNG KẾT NỐI ĐƯỢC ROBOT.")
        
        # Update initial robot status (delay to ensure GUI ready)
        def _update_initial_status():
            time.sleep(0.5)
            try:
                self.robot_status = "Ready - Waiting for G-code"
                if self.gui_panel and self.gui_panel.root:
                    self.gui_panel.update_robot_status(self.robot_status)
                    self.gui_panel.update_status_display("Ready - Select file to begin")
            except:
                pass
        
        threading.Thread(target=_update_initial_status, daemon=True).start()

    # --- AUTO-DETECT ARDUINO PORT ---
    def _detect_arduino_port(self):
        """Tìm port Arduino đầu tiên có sẵn"""
        import glob
        
        # Danh sách port thường dùng (theo thứ tự ưu tiên)
        possible_ports = [
            '/dev/ttyUSB0',  # Phổ biến nhất trên Linux
            '/dev/ttyUSB1',
            '/dev/ttyUSB2',
            '/dev/ttyACM0',  # Arduino Mega
            '/dev/ttyACM1',
            '/dev/ttyAMA0',  # Raspberry Pi serial
        ]
        
        # Tìm port có sẵn
        for port in possible_ports:
            if os.path.exists(port):
                self.get_logger().info(f"✓ Tìm thấy Arduino tại: {port}")
                return port
        
        # Fallback: tìm bất kỳ ttyUSB hoặc ttyACM
        usb_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        if usb_ports:
            port = usb_ports[0]
            self.get_logger().info(f"✓ Tìm thấy Arduino tại: {port}")
            return port
        
        # Không tìm thấy
        self.get_logger().warn("⚠ Không tìm thấy port Arduino. Sẽ dùng mặc định: /dev/ttyUSB0")
        return '/dev/ttyUSB0'

    # --- LUỒNG ĐỌC SERIAL VÀ CẬP NHẬT GIAO DIỆN ---
    def _serial_read_thread(self):
        while rclpy.ok() and self.arduino and self.arduino.is_open:
            try:
                if self.arduino.in_waiting > 0:
                    response = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                    if response.startswith("TEMP:"):
                        self.current_temp_str = response[5:]
                        # Đẩy nhiệt độ lên màn hình GUI
                        self.gui_panel.update_temp_display(self.current_temp_str)
                    elif response.startswith("STATUS:"):
                        self.arduino_status = response[7:]
            except Exception:
                pass
            time.sleep(0.005)

    def gui_lenh_arduino(self, cmd_str):   
        if self.arduino and self.arduino.is_open:
            cmd_send = f"{cmd_str}\n".encode('utf-8') 
            self.arduino.write(cmd_send)

    def gui_lenh_home(self):
        self.robot_status = "Moving to HOME position..."
        self.gui_panel.update_status_display("Đang về HOME robot...")
        self.gui_panel.update_robot_status(self.robot_status)
        self.controller.di_chuyen_home()
        self.robot_status = "Ready - At HOME"
        self.gui_panel.update_status_display("Robot đã về HOME")
        self.gui_panel.update_robot_status(self.robot_status)

    def gui_lenh_set_speed(self, speed_pct: float):
        self.speed_scale_pct = max(10.0, min(150.0, speed_pct))
        self.gui_panel.update_speed_display(f"{self.speed_scale_pct:.0f}%")

    def gui_lenh_select_file(self, filepath: str):
        self.selected_file = filepath
        self.gui_panel.update_status_display(f"Chọn: {filepath.split('/')[-1]}")
        self.get_logger().info(f">>> File được chọn: {filepath}")

    def gui_lenh_set_fan(self, fan_pct: int):
        self.fan_speed_pct = max(0, min(100, fan_pct))
        fan_cmd = f"M106 S{int(self.fan_speed_pct * 255 / 100)}"  # Convert % to 0-255
        self.gui_lenh_arduino(fan_cmd)

    def gui_lenh_set_temp(self, temp_pct: int):
        """Set heater temperature (0-300°C)"""
        self.target_temp = max(0, min(300, temp_pct))
        temp_cmd = f"M104 S{self.target_temp}"
        self.gui_lenh_arduino(temp_cmd)

    def get_robot_status(self):
        """Get current robot status"""
        return self.robot_status

    def gui_lenh_start_print(self):
        """Start printing from the selected file"""
        if not self.selected_file:
            self.gui_panel.update_status_display("No file selected. Please choose a file first.")
            return
        
        self.gui_panel.update_status_display("Starting print...")
        self.robot_status = "Moving to HOME"
        self.gui_panel.update_robot_status(self.robot_status)
        self.is_paused = False
        self.should_stop = False
        try:
            self.controller.di_chuyen_home()
            time.sleep(1.0)
            self.robot_status = "Printing"
            self.gui_panel.update_robot_status(self.robot_status)
            self.run_gcode_file(self.selected_file, 1)
            self.gui_lenh_arduino("STOP")
            self.gui_panel.update_status_display("Print completed!")
            self.robot_status = "Moving to HOME"
            self.gui_panel.update_robot_status(self.robot_status)
            time.sleep(10.0)
            self.controller.di_chuyen_home()
            self.robot_status = "Idle"
            self.gui_panel.update_robot_status(self.robot_status)
        except Exception as e:
            self.gui_panel.update_status_display(f"Error: {str(e)}")
            self.robot_status = "Error"
            self.gui_panel.update_robot_status(self.robot_status)
        finally:
            self.is_printing = False
            self.is_paused = False
            self.should_stop = False

    def gui_lenh_pause_resume(self):
        """Toggle pause/resume during printing"""
        if not self.is_printing:
            self.gui_panel.update_status_display("Not currently printing.")
            return
        
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.gui_panel.update_status_display("PAUSED - Click PAUSE again to resume")
        else:
            self.gui_panel.update_status_display("Resuming print...")

    def gui_lenh_stop(self):
        """Stop printing immediately"""
        if not self.is_printing:
            self.gui_panel.update_status_display("Not currently printing.")
            return
        
        self.should_stop = True
        self.is_printing = False
        self.gui_lenh_arduino("STOP")
        self.gui_panel.update_status_display("Print stopped by user")

    def cho_arduino_san_sang(self):
        print("\n>>> ĐANG CHỜ ARDUINO NUNG (250°C) VÀ ĐÙN NHỰA THỪA... <<<")
        while rclpy.ok():
            if self.arduino_status == "PURGING":
                print(f"\n[Trạng thái] Đạt 250°C. Đang tự động đùn nhựa thừa (Purging)...".ljust(config.LOG_LINE_WIDTH))
                self.arduino_status = "WAITING" 
            elif self.arduino_status == "READY_TO_PRINT":
                print(f"\n[Trạng thái] Đã xong! Doosan Robot bắt đầu di chuyển quỹ đạo.".ljust(config.LOG_LINE_WIDTH))
                return True
            else:
                print(f"[Chờ In] Nhiệt độ hiện tại: {self.current_temp_str}°C / 250.0°C".ljust(config.LOG_LINE_WIDTH), end='\r', flush=True)
            time.sleep(0.1) 
        return False

    def _print_progress(self, message: str):
        print(message.ljust(config.LOG_LINE_WIDTH)[:config.LOG_LINE_WIDTH], end='\r', flush=True)

    def run_gcode_file(self, filename: str, start_line: int = 1):
        self.is_printing = True
        self.should_stop = False
        self.is_paused = False
        points = parse_gcode(filename, start_line=start_line)
        self.get_logger().info(f">>> Đọc thành công {len(points)} điểm. Chuẩn bị chạy quỹ đạo!")
        
        self.total_points = len(points)
        self.print_start_time = time.time()
        
        ten_file_ngan = os.path.basename(filename)
        self.gui_lenh_arduino(f"PRINT:{ten_file_ngan}")
        
        if not self.cho_arduino_san_sang():
            self.get_logger().error("Quá trình chuẩn bị in bị gián đoạn!")
            return

        total_pts = len(points)
        last_rx, last_ry, last_rz = 0.0, 0.0, 0.0

        for i, pt_base in enumerate(points):
            # Check for stop flag
            if self.should_stop or not rclpy.ok():
                break 
            
            # Handle pause
            while self.is_paused and rclpy.ok() and not self.should_stop:
                time.sleep(0.1)
            
            if self.should_stop or not self.is_printing:
                break

            if i == 0:
                last_rx, last_ry, last_rz = pt_base.rx, pt_base.ry, pt_base.rz
                pt_exec = pt_base
            else:
                unwrap_rx = unwrap_angle(pt_base.rx, last_rx)
                unwrap_ry = unwrap_angle(pt_base.ry, last_ry)
                unwrap_rz = unwrap_angle(pt_base.rz, last_rz)
                pt_exec = pt_base._replace(rx=unwrap_rx, ry=unwrap_ry, rz=unwrap_rz)
                last_rx, last_ry, last_rz = unwrap_rx, unwrap_ry, unwrap_rz 

            if hasattr(pt_exec, 'e') and pt_exec.e != 0.0:
                e_val = pt_exec.e  
                f_val_mm_min = pt_exec.speed * 60.0 
                arduino_cmd = f"G1 E{e_val:.4f} F{f_val_mm_min:.1f}"
                self.gui_lenh_arduino(arduino_cmd)

            self.controller.gui_lenh_move_line(pt_exec, step=i)
            self.current_point = i

            if i % config.LOG_EVERY_N_POINTS == 0 or i == total_pts - 1:
                actual_line = start_line + i
                total_file = start_line - 1 + total_pts
                phan_tram = int((i / total_pts) * 100)
                speed_mms = pt_exec.speed * (self.speed_scale_pct / 100.0)
                
                # Calculate estimated remaining time (H:MM format)
                elapsed = time.time() - self.print_start_time
                if i > 0:
                    avg_time_per_point = elapsed / i
                    remaining_points = total_pts - i
                    remaining_time_sec = avg_time_per_point * remaining_points
                    remaining_hours = int(remaining_time_sec // 3600)
                    remaining_mins = int((remaining_time_sec % 3600) / 60)
                    time_str = f"{remaining_hours}:{remaining_mins:02d}"
                else:
                    time_str = "0:00"
                
                # Update robot status display
                self.robot_status = f"Printing: {phan_tram}% | X:{pt_exec.x:.1f} Y:{pt_exec.y:.1f} Z:{pt_exec.z:.1f}"
                self.gui_panel.update_robot_status(self.robot_status)
                
                self.gui_lenh_arduino(f"PROGRESS:{phan_tram}")
                self.gui_lenh_arduino(f"LINE:{actual_line}/{total_file}")
                self.gui_panel.update_progress_display(phan_tram)
                self.gui_panel.update_estimated_time(time_str)
                self.gui_panel.update_speed_display(f"{speed_mms:.2f} mm/s ({self.speed_scale_pct:.0f}%)")
                
                msg = f"[In {phan_tram}%] Line: {actual_line}/{total_file} | T: {self.current_temp_str}°C | Z: {pt_exec.z:.1f} | Rx:{pt_exec.rx:.1f}° Ry:{pt_exec.ry:.1f}° Rz:{pt_exec.rz:.1f}°"
                self._print_progress(msg)

        self._print_progress('')
        self.is_printing = False

def main(args=None):
    rclpy.init(args=args)
    node = SmartPrinter5AxisPro()

    # Chạy ROS 2 Spin ở luồng ngầm để không lỗi generator already executing
    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

    # Thuộc tính tìm đường dẫn file
    try:
        pkg_path = get_package_share_directory('doosan_printing_app')
        thu_muc_gcode = os.path.join(pkg_path, 'Data_Gcode_files')
    except Exception:
        thu_muc_gcode = '/home/lehuythien/ros2_ws/doosan_in3d_ws/src/doosan_printing_app/doosan_printing_app/Data_Gcode_files/'

    filename = config.DEFAULT_GCODE_FILE
    if len(sys.argv) > 1:
        nhap_vao = sys.argv[1]
        if '/' in nhap_vao:
            filename = nhap_vao
        else:
            filename = os.path.join(thu_muc_gcode, nhap_vao)

    start_line = 1
    if len(sys.argv) > 2:
        try: start_line = int(sys.argv[2])
        except ValueError: pass

    try:
        time.sleep(0.5)  # Wait for node to initialize
        
        # GUI được bật mặc định (có thể tắt bằng ENABLE_GUI=0)
        enable_gui = os.environ.get('ENABLE_GUI', '1') != '0'
        gui_started = False
        
        if enable_gui:
            # Khởi tạo GUI trong daemon thread để không block ROS2
            node.get_logger().info(">>> Khởi động GUI... <<<")
            try:
                gui_thread = threading.Thread(target=node.gui_panel.start_gui, daemon=True)
                gui_thread.start()
                time.sleep(1.0)  # Cho GUI khởi động
                
                # Kiểm tra xem GUI đã khởi động thành công không
                if node.gui_panel.root is not None:
                    gui_started = True
                    node.get_logger().info("✓ GUI khởi động thành công!")
                else:
                    node.get_logger().warn("⚠ GUI chưa khởi động. Tiếp tục mà không có giao diện...")
            except Exception as e:
                node.get_logger().error(f"✗ GUI Error: {e}")
                import traceback
                traceback.print_exc()
                node.get_logger().info("Tiếp tục mà không có GUI...")
        else:
            # Chạy mà không có GUI
            node.get_logger().info("Node ready - GUI disabled")
        
        # Main loop - Chờ người dùng tương tác hoặc keyboard interrupt
        node.get_logger().info("\n" + "="*60)
        node.get_logger().info("SMART3DX LAB - 5-AXIS PRINTER READY")
        node.get_logger().info("="*60)
        if gui_started:
            node.get_logger().info("✓ GUI đã hiển thị. Sử dụng giao diện để điều khiển.")
        else:
            node.get_logger().info("📋 Sử dụng CLI hoặc gửi ROS2 topic để điều khiển")
        node.get_logger().info("Nhấn Ctrl+C để dừng...\n")
        
        while rclpy.ok():
            time.sleep(1.0)
        
    except KeyboardInterrupt:
        node.get_logger().warn("\n!!! Emergency stop by user !!!")
        node.is_printing = False
        try:
            node.gui_lenh_arduino("STOP")
        except:
            pass
        if gui_started:
            try:
                node.gui_panel.update_status_display("Stopped by user")
            except:
                pass
        node.get_logger().info("Node stopped by user")
    finally:
        if node.arduino and node.arduino.is_open: 
            node.arduino.close()
        node.destroy_node()
        if rclpy.ok(): 
            rclpy.shutdown()

if __name__ == '__main__':
    main()