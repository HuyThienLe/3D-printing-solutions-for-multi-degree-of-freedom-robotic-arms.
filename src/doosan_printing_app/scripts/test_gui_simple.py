#!/usr/bin/env python3
"""
Test Tkinter GUI riêng biệt (không cần ROS2 hoặc Robot)
"""
import tkinter as tk
import os
import sys
import time

print(f"Python: {sys.version}")
print(f"DISPLAY: {os.environ.get('DISPLAY', 'NOT SET')}")

try:
    print("\n[Test 1] Tạo root window...")
    root = tk.Tk()
    print("✓ root = tk.Tk() - OK")
    
    print("[Test 2] Set title...")
    root.title("Tkinter Test")
    print("✓ root.title() - OK")
    
    print("[Test 3] Set geometry...")
    root.geometry("600x400")
    print("✓ root.geometry() - OK")
    
    print("[Test 4] Add widget...")
    label = tk.Label(root, text="🎉 GUI Works!", font=("Arial", 20, "bold"), fg="green")
    label.pack(pady=20)
    print("✓ widget added - OK")
    
    print("[Test 5] Force to front...")
    root.attributes('-topmost', True)
    print("✓ attributes - OK")
    
    print("[Test 6] Update window...")
    root.update_idletasks()
    print("✓ update_idletasks() - OK")
    
    print("\n[✓] All tests passed! Window should appear...")
    print("[INFO] Window will auto-close in 5 seconds...")
    
    # Auto close after 5 seconds
    root.after(5000, root.quit)
    
    print("[Test 7] Running mainloop...")
    root.mainloop()
    print("✓ mainloop() - OK")
    
    print("\n✓✓✓ SUCCESS ✓✓✓")
    print("Tkinter GUI works perfectly!")
    
except Exception as e:
    print(f"\n✗✗✗ ERROR ✗✗✗")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
