import threading
import tkinter as tk
from tkinter import ttk, filedialog
import os
import time

class PrintHeadControlPanel:
    def __init__(self, send_cmd_callback, home_callback=None, speed_callback=None, file_callback=None, 
                 fan_callback=None, start_callback=None, pause_callback=None, stop_callback=None,
                 temp_callback=None, robot_status_callback=None):
        """
        send_cmd_callback: Function to send G-code commands to Arduino.
        home_callback: Function to move robot to HOME position.
        speed_callback: Function to update print speed ratio.
        file_callback: Function to select G-code file.
        fan_callback: Function to control fan speed.
        start_callback: Function to start printing.
        pause_callback: Function to pause/resume printing.
        stop_callback: Function to stop printing.
        temp_callback: Function to set heater temperature.
        robot_status_callback: Function to get robot status string.
        """
        self.send_cmd = send_cmd_callback
        self.home_callback = home_callback
        self.speed_callback = speed_callback
        self.file_callback = file_callback
        self.fan_callback = fan_callback
        self.start_callback = start_callback
        self.pause_callback = pause_callback
        self.stop_callback = stop_callback
        self.temp_callback = temp_callback
        self.robot_status_callback = robot_status_callback
        
        self.root = None
        self.lbl_file = None
        self.lbl_temp = None
        self.lbl_status = None
        self.lbl_time = None
        self.lbl_speed = None
        self.lbl_fan = None
        self.lbl_robot_status = None
        self.progress_bar = None
        self.progress_label = None
        
        self.speed_var = None
        self.fan_var = None
        self.temp_var = None
        self.is_paused = False

    def start_gui(self):
        """Khởi tạo và chạy GUI Tkinter"""
        display = os.environ.get('DISPLAY', 'N/A')
        print(f"[GUI] DISPLAY={display}")
        
        if not display or display == 'N/A':
            print("[ERROR] Không có X server. Không thể hiển thị GUI!")
            print("[INFO] Thiết lập DISPLAY hoặc chạy với: DISPLAY=:0")
            return False
        
        try:
            print("[GUI] Initializing Tkinter window...")
            self.root = tk.Tk()
            self.root.title("Smart3Dx Lab - 3D Printer Control System")
            self.root.geometry("1300x650")
            self.root.configure(bg="#f0f0f0")
            
            # Force window to front
            self.root.attributes('-topmost', True)
            self.root.update()
            self.root.update_idletasks()
            
            print("[GUI] Tkinter window created successfully")
            
            self.speed_var = tk.DoubleVar(master=self.root, value=100.0)
            self.fan_var = tk.IntVar(master=self.root, value=0)
            self.temp_var = tk.IntVar(master=self.root, value=250)

            # ===== TITLE HEADER =====
            header = tk.Frame(self.root, bg="#1a1a2e", height=60)
            header.pack(fill="x", side="top")
            header.pack_propagate(False)
            
            title_label = tk.Label(header, text="SMART3Dx LAB", font=("Helvetica", 20, "bold"), 
                                  fg="#00d4ff", bg="#1a1a2e")
            title_label.pack(side="left", padx=20, pady=10)
            
            subtitle = tk.Label(header, text="5-Axis 3D Printer Control System", font=("Helvetica", 11), 
                               fg="#ffffff", bg="#1a1a2e")
            subtitle.pack(side="left", padx=5, pady=10)

            # ===== MAIN CONTENT FRAME =====
            main_frame = tk.Frame(self.root, bg="#f0f0f0")
            main_frame.pack(fill="both", expand=True, padx=15, pady=15)

            # ===== ROW 1: FILE SELECTION =====
            file_frame = tk.LabelFrame(main_frame, text=" 📁 Select G-code File ", font=("Arial", 11, "bold"), 
                                       bg="#f0f0f0", fg="#1a1a2e")
            file_frame.pack(fill="x", pady=(0, 10))
            
            self.lbl_file = tk.Label(file_frame, text="No file selected", font=("Arial", 10), 
                                     fg="#2c3e50", bg="#ecf0f1", relief="sunken", padx=10, pady=5)
            self.lbl_file.pack(fill="x", padx=10, pady=(10, 5))
            
            tk.Button(file_frame, text="Choose G-code File", bg="#e67e22", fg="white", 
                     font=("Arial", 10, "bold"), command=self.on_file_selected,
                     padx=10, pady=5).pack(fill="x", padx=10, pady=(5, 10))

            # ===== ROW 2: MONITORING DISPLAYS =====
            monitor_frame = tk.Frame(main_frame, bg="#f0f0f0")
            monitor_frame.pack(fill="x", pady=(0, 10))
            
            # Temperature Display (large box)
            temp_display = tk.LabelFrame(monitor_frame, text="🌡️  CURRENT TEMPERATURE", font=("Arial", 11, "bold"),
                                        bg="#fff5e1", fg="#d35400", relief="ridge", borderwidth=2)
            temp_display.pack(side="left", padx=5, fill="both", expand=True)
            self.lbl_temp = tk.Label(temp_display, text="--.- °C", font=("Helvetica", 24, "bold"), 
                                    fg="#d35400", bg="#fff5e1")
            self.lbl_temp.pack(pady=(10, 5))

            # Status Display
            status_display = tk.LabelFrame(monitor_frame, text="⚙️  STATUS", font=("Arial", 11, "bold"),
                                          bg="#e8f8f5", fg="#16a085", relief="ridge", borderwidth=2)
            status_display.pack(side="left", padx=5, fill="both", expand=True)
            self.lbl_status = tk.Label(status_display, text="Ready", font=("Arial", 10), 
                                      fg="#16a085", bg="#e8f8f5")
            self.lbl_status.pack(pady=10)

            # Estimated Time Display
            time_display = tk.LabelFrame(monitor_frame, text="⏱️  REMAINING TIME", font=("Arial", 11, "bold"),
                                        bg="#fdeef4", fg="#c0392b", relief="ridge", borderwidth=2)
            time_display.pack(side="left", padx=5, fill="both", expand=True)
            self.lbl_time = tk.Label(time_display, text="--:--", font=("Helvetica", 20, "bold"), 
                                    fg="#c0392b", bg="#fdeef4")
            self.lbl_time.pack(pady=(5, 5))

            # Robot Status Display
            robot_display = tk.LabelFrame(monitor_frame, text="🤖  ROBOT STATUS", font=("Arial", 11, "bold"),
                                         bg="#ebf5fb", fg="#2980b9", relief="ridge", borderwidth=2)
            robot_display.pack(side="left", padx=5, fill="both", expand=True)
            self.lbl_robot_status = tk.Label(robot_display, text="Waiting", font=("Arial", 9), 
                                            fg="#2980b9", bg="#ebf5fb", wraplength=120, justify="left")
            self.lbl_robot_status.pack(pady=10, padx=5)

            # ===== ROW 3: PROGRESS BAR =====
            progress_section = tk.LabelFrame(main_frame, text=" 📊 PRINT PROGRESS ", font=("Arial", 11, "bold"),
                                            bg="#f0f0f0", fg="#1a1a2e")
            progress_section.pack(fill="x", pady=(0, 10))
            
            self.progress_bar = ttk.Progressbar(progress_section, mode='determinate', length=600, 
                                               style="TProgressbar")
            self.progress_bar.pack(fill="x", padx=10, pady=(10, 5))
            
            self.progress_label = tk.Label(progress_section, text="0%", font=("Arial", 12, "bold"), 
                                          fg="#27ae60", bg="#f0f0f0")
            self.progress_label.pack(pady=(0, 10))

            # ===== ROW 4: MAIN CONTROL BUTTONS =====
            button_section = tk.LabelFrame(main_frame, text=" 🎮 MAIN CONTROLS ", font=("Arial", 11, "bold"),
                                          bg="#f0f0f0", fg="#1a1a2e")
            button_section.pack(fill="x", pady=(0, 10))
            
            button_frame = tk.Frame(button_section, bg="#f0f0f0")
            button_frame.pack(fill="x", padx=10, pady=10)
            
            tk.Button(button_frame, text="▶ START", bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                     width=14, padx=5, command=self.on_start_pressed).pack(side="left", padx=3)
            
            tk.Button(button_frame, text="⏸ PAUSE/RESUME", bg="#f39c12", fg="white", font=("Arial", 11, "bold"),
                     width=16, padx=5, command=self.on_pause_pressed).pack(side="left", padx=3)
            
            tk.Button(button_frame, text="⏹ STOP", bg="#e74c3c", fg="white", font=("Arial", 11, "bold"),
                     width=14, padx=5, command=self.on_stop_pressed).pack(side="left", padx=3)
            
            tk.Button(button_frame, text="🏠 HOME", bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                     width=14, padx=5, command=self.on_home_pressed).pack(side="left", padx=3)

            # ===== ROW 5: TEMPERATURE CONTROL =====
            temp_section = tk.LabelFrame(main_frame, text=" 🌡️  HEATER TEMPERATURE (0-300°C) ", 
                                        font=("Arial", 11, "bold"), bg="#f0f0f0", fg="#1a1a2e")
            temp_section.pack(fill="x", pady=(0, 10))
            
            temp_ctrl_frame = tk.Frame(temp_section, bg="#f0f0f0")
            temp_ctrl_frame.pack(fill="x", padx=10, pady=10)
            
            tk.Button(temp_ctrl_frame, text="Off (0°C)", bg="#95a5a6", fg="white", 
                     command=self.on_set_temp_0).pack(side="left", padx=2)
            tk.Button(temp_ctrl_frame, text="200°C", bg="#e67e22", fg="white", 
                     command=self.on_set_temp_200).pack(side="left", padx=2)
            tk.Button(temp_ctrl_frame, text="250°C", bg="#c0392b", fg="white", 
                     command=self.on_set_temp_250).pack(side="left", padx=2)
            tk.Button(temp_ctrl_frame, text="300°C", bg="#8b0000", fg="white", 
                     command=self.on_set_temp_300).pack(side="left", padx=2)
            
            tk.Label(temp_ctrl_frame, text="", width=12, bg="#f0f0f0").pack(side="left")
            tk.Label(temp_ctrl_frame, text="Target:", font=("Arial", 9, "bold"), bg="#f0f0f0").pack(side="left")
            self.lbl_temp_target = tk.Label(temp_ctrl_frame, text="250°C", font=("Arial", 11, "bold"), 
                                           fg="#c0392b", bg="#f0f0f0", width=8)
            self.lbl_temp_target.pack(side="left", padx=10)
            
            temp_slider_frame = tk.Frame(temp_section, bg="#f0f0f0")
            temp_slider_frame.pack(fill="x", padx=10, pady=(0, 10))
            tk.Scale(temp_slider_frame, from_=0, to=300, orient="horizontal", variable=self.temp_var,
                    resolution=5, command=self.on_temp_changed, bg="#f0f0f0", 
                    fg="#1a1a2e", length=600).pack(fill="x")

            # ===== ROW 6: SPEED CONTROL =====
            speed_section = tk.LabelFrame(main_frame, text=" ⚡ PRINT SPEED (10-200%) ", 
                                         font=("Arial", 11, "bold"), bg="#f0f0f0", fg="#1a1a2e")
            speed_section.pack(fill="x", pady=(0, 10))
            
            speed_btn_frame = tk.Frame(speed_section, bg="#f0f0f0")
            speed_btn_frame.pack(fill="x", padx=10, pady=10)
            
            tk.Button(speed_btn_frame, text="Slow (50%)", bg="#3498db", fg="white",
                     command=lambda: self.set_speed_mode(50)).pack(side="left", padx=2)
            tk.Button(speed_btn_frame, text="Normal (100%)", bg="#27ae60", fg="white",
                     command=lambda: self.set_speed_mode(100)).pack(side="left", padx=2)
            tk.Button(speed_btn_frame, text="Fast (150%)", bg="#e74c3c", fg="white",
                     command=lambda: self.set_speed_mode(150)).pack(side="left", padx=2)
            
            tk.Label(speed_btn_frame, text="", width=20, bg="#f0f0f0").pack(side="left")
            self.lbl_speed = tk.Label(speed_btn_frame, text="100%", font=("Arial", 11, "bold"), 
                                     fg="#2980b9", bg="#f0f0f0", width=8)
            self.lbl_speed.pack(side="right", padx=10)
            
            speed_slider_frame = tk.Frame(speed_section, bg="#f0f0f0")
            speed_slider_frame.pack(fill="x", padx=10, pady=(0, 10))
            tk.Scale(speed_slider_frame, from_=10, to=200, orient="horizontal", variable=self.speed_var,
                    resolution=5, command=self.on_speed_changed, bg="#f0f0f0", 
                    fg="#1a1a2e", length=600).pack(fill="x")

            # ===== ROW 7: FAN CONTROL =====
            fan_section = tk.LabelFrame(main_frame, text=" 🌀 COOLING FAN (0-100%) ", 
                                       font=("Arial", 11, "bold"), bg="#f0f0f0", fg="#1a1a2e")
            fan_section.pack(fill="x", pady=(0, 10))
            
            fan_btn_frame = tk.Frame(fan_section, bg="#f0f0f0")
            fan_btn_frame.pack(fill="x", padx=10, pady=10)
            
            tk.Button(fan_btn_frame, text="Off", bg="#95a5a6", fg="white",
                     command=lambda: self.set_fan_speed(0)).pack(side="left", padx=2)
            tk.Button(fan_btn_frame, text="50%", bg="#3498db", fg="white",
                     command=lambda: self.set_fan_speed(50)).pack(side="left", padx=2)
            tk.Button(fan_btn_frame, text="100%", bg="#27ae60", fg="white",
                     command=lambda: self.set_fan_speed(100)).pack(side="left", padx=2)
            
            tk.Label(fan_btn_frame, text="", width=25, bg="#f0f0f0").pack(side="left")
            self.lbl_fan = tk.Label(fan_btn_frame, text="Off", font=("Arial", 11, "bold"), 
                                   fg="#95a5a6", bg="#f0f0f0", width=8)
            self.lbl_fan.pack(side="right", padx=10)
            
            fan_slider_frame = tk.Frame(fan_section, bg="#f0f0f0")
            fan_slider_frame.pack(fill="x", padx=10, pady=(0, 10))
            tk.Scale(fan_slider_frame, from_=0, to=100, orient="horizontal", variable=self.fan_var,
                    resolution=5, command=self.on_fan_changed, bg="#f0f0f0", 
                    fg="#1a1a2e", length=600).pack(fill="x")

            # ===== ROW 8: EXTRUDER CONTROL =====
            extrude_section = tk.LabelFrame(main_frame, text=" 🔧 EXTRUDER MOTOR ", 
                                           font=("Arial", 11, "bold"), bg="#f0f0f0", fg="#1a1a2e")
            extrude_section.pack(fill="x")
            
            extrude_frame = tk.Frame(extrude_section, bg="#f0f0f0")
            extrude_frame.pack(fill="x", padx=10, pady=10)
            
            tk.Button(extrude_frame, text="➕ Extrude 10mm", bg="#2ecc71", fg="white", font=("Arial", 10, "bold"),
                     command=lambda: self.send_cmd("G1 E10 F300")).pack(side="left", padx=5)
            
            tk.Button(extrude_frame, text="➖ Retract 5mm", bg="#f39c12", fg="white", font=("Arial", 10, "bold"),
                     command=lambda: self.send_cmd("G1 E-5 F500")).pack(side="left", padx=5)

            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            print("[GUI] GUI khởi động thành công! Chờ sự kiện người dùng...")
            self.root.mainloop()
            return True
        except Exception as e:
            print(f"[ERROR] GUI Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_temp_display(self, temp_str):
        """Update temperature display"""
        if self.root and self.lbl_temp:
            try:
                self.lbl_temp.config(text=f"{temp_str} °C")
            except:
                pass

    def update_status_display(self, status_text):
        """Update status display"""
        if self.root and self.lbl_status:
            try:
                self.lbl_status.config(text=status_text)
            except:
                pass

    def update_robot_status(self, robot_status):
        """Update robot status display"""
        if self.root and self.lbl_robot_status:
            try:
                self.lbl_robot_status.config(text=robot_status)
            except:
                pass

    def update_progress_display(self, phan_tram):
        """Update progress bar and label with percentage"""
        if self.root and self.progress_bar:
            try:
                self.progress_bar['value'] = phan_tram
                self.progress_label.config(text=f"{phan_tram}%")
            except:
                pass

    def update_estimated_time(self, time_str):
        """Update estimated remaining time (format: H:MM)"""
        if self.root and self.lbl_time:
            try:
                self.lbl_time.config(text=time_str)
            except:
                pass

    def update_speed_display(self, speed_text):
        """Update speed display"""
        if self.root and self.lbl_speed:
            try:
                self.lbl_speed.config(text=speed_text)
            except:
                pass

    def on_temp_changed(self, value):
        """Temperature slider changed"""
        temp_int = int(float(value))
        if self.lbl_temp_target:
            self.lbl_temp_target.config(text=f"{temp_int}°C")
        if self.temp_callback:
            self.temp_callback(temp_int)

    def on_set_temp_0(self):
        """Set temperature to 0°C"""
        self.temp_var.set(0)
        self.on_temp_changed(0)

    def on_set_temp_200(self):
        """Set temperature to 200°C"""
        self.temp_var.set(200)
        self.on_temp_changed(200)

    def on_set_temp_250(self):
        """Set temperature to 250°C"""
        self.temp_var.set(250)
        self.on_temp_changed(250)

    def on_set_temp_300(self):
        """Set temperature to 300°C"""
        self.temp_var.set(300)
        self.on_temp_changed(300)

    def on_home_pressed(self):
        """Go to HOME position button"""
        if self.home_callback:
            threading.Thread(target=self.home_callback, daemon=True).start()

    def on_start_pressed(self):
        """Start printing button"""
        try:
            if self.start_callback:
                threading.Thread(target=self.start_callback, daemon=True).start()
        except Exception as e:
            print(f"Error in on_start_pressed: {e}")

    def on_pause_pressed(self):
        """Pause/Resume printing button"""
        try:
            if self.pause_callback:
                self.is_paused = not self.is_paused
                threading.Thread(target=self.pause_callback, daemon=True).start()
        except Exception as e:
            print(f"Error in on_pause_pressed: {e}")

    def on_stop_pressed(self):
        """Stop printing button"""
        try:
            if self.stop_callback:
                threading.Thread(target=self.stop_callback, daemon=True).start()
        except Exception as e:
            print(f"Error in on_stop_pressed: {e}")

    def on_file_selected(self):
        """File selection dialog"""
        filename = filedialog.askopenfilename(
            title="Select G-code file",
            filetypes=[("G-code files", "*.gcode *.txt"), ("All files", "*.*")],
            initialdir="/home/lehuythien/ros2_ws/doosan_in3d_ws/src/doosan_printing_app/doosan_printing_app/Data_Gcode_files"
        )
        if filename and self.file_callback:
            self.lbl_file.config(text=f"{filename.split('/')[-1]}")
            self.file_callback(filename)

    def set_speed_mode(self, speed_pct):
        """Set speed mode quickly"""
        self.speed_var.set(speed_pct)
        self.on_speed_changed(speed_pct)

    def on_speed_changed(self, value):
        """Speed slider changed"""
        if self.speed_callback:
            try:
                speed_val = float(value)
                self.lbl_speed.config(text=f"{int(speed_val)}%")
                self.speed_callback(speed_val)
            except ValueError:
                pass

    def set_fan_speed(self, fan_pct):
        """Set fan speed quickly"""
        self.fan_var.set(fan_pct)
        self.on_fan_changed(fan_pct)

    def on_fan_changed(self, value):
        """Fan slider changed"""
        fan_pct = int(float(value))
        if fan_pct == 0:
            self.lbl_fan.config(text="Off")
        else:
            self.lbl_fan.config(text=f"{fan_pct}%")
        if self.fan_callback:
            self.fan_callback(fan_pct)

    def on_close(self):
        """Close the GUI window"""
        if self.root:
            self.root.destroy()
            self.root = None
