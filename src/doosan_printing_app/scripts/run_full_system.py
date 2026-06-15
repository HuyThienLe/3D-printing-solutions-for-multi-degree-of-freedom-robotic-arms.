#!/usr/bin/env python3
"""
SMART3DX LAB - Full System Launcher (Python Version)
Chạy toàn bộ hệ thống: Arduino + Robot + Printer Node + GUI
"""

import os
import sys
import subprocess
import time
import signal
import atexit
from pathlib import Path

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

WORKSPACE = Path.home() / 'ros2_ws' / 'doosan_in3d_ws'
processes = []

def cleanup():
    """Kill all background processes"""
    print(f"\n{YELLOW}Cleaning up...{NC}")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            try:
                proc.kill()
            except:
                pass
    print(f"{GREEN}✓ All processes terminated{NC}")

def run_command(cmd, name, background=False, silent=False):
    """Run command and handle errors"""
    print(f"{YELLOW}[{name}] {' '.join(cmd)}{NC}")
    try:
        if background:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE if silent else None,
                                   stderr=subprocess.PIPE if silent else None)
            processes.append(proc)
            return proc
        else:
            result = subprocess.run(cmd, check=True)
            return result.returncode
    except FileNotFoundError:
        print(f"{RED}✗ Command not found: {cmd[0]}{NC}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"{RED}✗ Command failed: {e}{NC}")
        if not background:
            sys.exit(1)
        return None

def main():
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    
    print(f"\n{BLUE}╔════════════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║     SMART3DX LAB - 5 AXIS PRINTER CONTROL          ║{NC}")
    print(f"{BLUE}╚════════════════════════════════════════════════════╝{NC}\n")
    
    # ========== STEP 1: Arduino Permission ==========
    print(f"{YELLOW}[STEP 1/3] Cấp quyền cho Arduino port...{NC}")
    ttyusb = Path('/dev/ttyUSB0')
    if ttyusb.exists():
        os.system(f'sudo chmod 666 {ttyusb}')
        print(f"{GREEN}✓ Arduino port ready: {ttyusb}{NC}\n")
    else:
        print(f"{RED}⚠ Warning: {ttyusb} not found${NC}")
        usb_ports = list(Path('/dev').glob('ttyUSB*')) + list(Path('/dev').glob('ttyACM*'))
        if usb_ports:
            print(f"{YELLOW}   Available ports: {', '.join(str(p) for p in usb_ports)}{NC}\n")
        else:
            print(f"{RED}   ERROR: No USB serial ports found!${NC}\n")
    
    # ========== STEP 2: Launch Robot ==========
    print(f"{YELLOW}[STEP 2/3] Khởi động Robot Doosan A0509...${NC}")
    print(f"{BLUE}   Đang khởi động... (chờ ~10 giây)${NC}\n")
    
    robot_cmd = [
        'ros2', 'launch', 'dsr_bringup2', 'dsr_bringup2_rviz.launch.py',
        'model:=a0509', 'color:=blue'
    ]
    robot_proc = run_command(robot_cmd, 'Robot Launcher', background=True)
    
    if not robot_proc:
        print(f"{RED}✗ Failed to start robot${NC}")
        sys.exit(1)
    
    time.sleep(10)
    print(f"{GREEN}✓ Robot started (PID: {robot_proc.pid})${NC}\n")
    
    # ========== STEP 3: Launch Printer Node ==========
    print(f"{YELLOW}[STEP 3/3] Khởi động Printer Node với GUI...${NC}")
    print(f"{BLUE}   GUI sẽ hiển thị trong vài giây...${NC}\n")
    
    os.chdir(WORKSPACE)
    os.system(f'source {WORKSPACE}/install/setup.bash')
    os.environ['ENABLE_GUI'] = '1'
    
    printer_cmd = [
        'bash', '-c',
        f'source {WORKSPACE}/install/setup.bash && ros2 run doosan_printing_app doosan_printer_node'
    ]
    
    try:
        subprocess.run(printer_cmd, check=False)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user${NC}")
    finally:
        cleanup()

if __name__ == '__main__':
    main()
