### Cách 1: Chạy Tự Động Toàn Bộ Bằng 1 Lệnh (Khuyên Dùng)
Chỉ với 1 dòng lệnh duy nhất, hệ thống sẽ tự động khởi động mọi thứ:
```bash
cd ~/ros2_ws/doosan_in3d_ws
bash src/doosan_printing_app/scripts/run_full_system.sh
```
*Lưu ý: Lệnh này sẽ yêu cầu bạn nhập mật khẩu Linux của máy để cấp quyền mở cổng USB cho Arduino. Sau đó hãy chờ khoảng 10-15 giây để Robot và Giao diện GUI khởi động lên.*

### Cách 2: Chạy Thủ Công Từng Bước (Dùng khi cần Gỡ lỗi / Debug)
Nếu hệ thống gặp lỗi hoặc bạn muốn kiểm tra xem lỗi ở phần mềm nào, hãy mở 3 cửa sổ Terminal (Ctrl + Alt + T) mới và chạy lần lượt:

**Terminal 1:** Cấp quyền cho cổng Arduino (Nếu không kết nối được cổng USB)
```bash
sudo chmod 666 /dev/ttyUSB0
```

**Terminal 2:** Khởi động Trình giả lập Robot Doosan và mô phỏng RViz
```bash
ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py model:=a0509 color:=blue
```

**Terminal 3:** Khởi động Giao diện điều khiển (GUI) của máy in 3D
```bash
cd ~/ros2_ws/doosan_in3d_ws
source install/setup.bash
ros2 run doosan_printing_app doosan_printer_node
```

---

## 🎮 Cách Sử Dụng Giao Diện Điều Khiển (GUI)
1. Bấm nút **"Choose G-code File"** để chọn file in (Tìm ở đường dẫn mặc định trong thư mục `Data_Gcode_files`).
2. Cài đặt nhiệt độ đầu đùn bằng thanh trượt hoặc nút (thường là 200°C cho nhựa PLA hoặc 250°C cho ABS/PETG).
3. Bạn phải đợi cho nhiệt độ đạt mức yêu cầu (Xem trên màn hình trạng thái hoặc trên Terminal).
4. Nhấn **START** để tiến hành quá trình in: Robot sẽ di chuyển về vị trí HOME, xả nhựa thừa (purge) và tiến hành chạy quỹ đạo in.
5. Bạn có thể thay đổi Tốc độ in (Print Speed) hoặc Tốc độ quạt (Cooling Fan) tuỳ ý trong lúc máy in đang chạy bằng thanh kéo trượt.
6. Khi muốn dừng, hãy ấn **STOP** (dừng hẳn) hoặc **PAUSE** (tạm dừng).

---
