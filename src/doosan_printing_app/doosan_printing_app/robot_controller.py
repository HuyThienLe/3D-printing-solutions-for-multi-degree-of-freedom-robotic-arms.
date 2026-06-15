#!/usr/bin/env python3

import time
import math
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration

from dsr_msgs2.srv import MoveLine, MoveJoint
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point

from . import config
from .gcode_parser import PrintPoint

class DoosanRobotController:

    def __init__(self, node: Node):
        self.node = node
        self.path_points: list[Point] = []
        
        # --- LƯU VỊ TRÍ ĐỂ TÍNH QUÃNG ĐƯỜNG ---
        self.last_x = None
        self.last_y = None
        self.last_z = None
        
        # --- BIẾN GOM THỜI GIAN (GIẢI QUYẾT LỖI RUNG) ---
        self.accumulated_time = 0.0

        self.cli_line = self.node.create_client(MoveLine, config.TOPIC_MOVE_LINE)
        self.cli_joint = self.node.create_client(MoveJoint, config.TOPIC_MOVE_JOINT)
        self.marker_pub = self.node.create_publisher(Marker, config.TOPIC_RVIZ, 10)

    def wait_cho_robot_ket_noi(self, timeout_sec: float = 1.0) -> bool:
        self.node.get_logger().info(f"Bần tăng đang tìm kiếm Robot tại {config.TOPIC_MOVE_LINE}...")
        while not self.cli_line.wait_for_service(timeout_sec=timeout_sec):
            self.node.get_logger().info("Vẫn đang tìm Robot...")
            if not rclpy.ok():
                return False
        self.node.get_logger().info("KẾT NỐI ROBOT THÀNH CÔNG!")
        return True

    def ve_rviz(self, x: float, y: float, z: float, step: int):
        marker = Marker()
        marker.header.frame_id = "world"
        marker.ns = "print_path"
        marker.header.stamp = self.node.get_clock().now().to_msg()
        marker.lifetime = Duration(seconds=0).to_msg()
        marker.id = 0
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        marker.scale.x = 0.003
        
        marker.color.a = 1.0
        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        
        p = Point()
        p.x = x / 1000.0
        p.y = y / 1000.0
        p.z = z / 1000.0
        self.path_points.append(p)
        marker.points = self.path_points
        
        if step % 50 == 0:
            self.marker_pub.publish(marker)

    def gui_lenh_move_line(self, pt: PrintPoint, step: int):
        self.ve_rviz(pt.x, pt.y, pt.z, step)
        
        req = MoveLine.Request()
        req.pos = [pt.x, pt.y, pt.z, pt.rx, pt.ry, pt.rz]
        
        speed_scale = getattr(self.node, 'speed_scale_pct', 100.0) / 100.0
        scaled_speed = pt.speed * speed_scale
        accel = config.MAX_ACCEL
        
        req.vel = [scaled_speed, scaled_speed]
        req.acc = [accel, accel]
        req.radius = config.RADIUS
        req.blend_type = 0
        req.sync_type = 0  
        
        future = self.cli_line.call_async(req)
        
        # 1. NẾU LÀ LỆNH CHẠY KHÔNG TẢI
        if pt.e <= 0.0001:
            start_wait = time.time()
            while rclpy.ok() and not future.done():
                if time.time() - start_wait > 60.0:
                    break
                time.sleep(0.002)
                
        # 2. NẾU LÀ LỆNH ĐANG IN
        else:
            if self.last_x is not None:
                dist = math.sqrt((pt.x - self.last_x)**2 + (pt.y - self.last_y)**2 + (pt.z - self.last_z)**2)
                t = dist / (scaled_speed if scaled_speed > 0 else 1.0)
                
                # FIX LỖI RUNG TOÀN THÂN (GOM THỜI GIAN)
                self.accumulated_time += t
                
                # Chỉ khi thời gian tích lũy >= 0.1 giây
                # Giúp xả 1 cụm 10-20 lệnh vào thẳng Doosan Buffer!
                if self.accumulated_time >= 0.1:
                    time.sleep(self.accumulated_time * 0.95)
                    self.accumulated_time = 0.0  # Reset lại sau khi ngủ
            else:
                time.sleep(0.005)
        
        self.last_x = pt.x
        self.last_y = pt.y
        self.last_z = pt.z
        
        return True

    def di_chuyen_home(self) -> bool:
        req = MoveJoint.Request()
        req.pos = config.HOME_JOINTS
        req.vel = config.HOME_VEL
        req.acc = config.HOME_ACC
        
        self.node.get_logger().info("Bần tăng đang đưa robot về HOME an toàn..")
        future = self.cli_joint.call_async(req)
        start_wait = time.time()
        
        while rclpy.ok() and not future.done():
            if time.time() - start_wait > 120.0:
                self.node.get_logger().error("Timeout: Lệnh di_chuyen_home không phản hồi.")
                return False
            time.sleep(0.001)
            
        if future.done():
            res = future.result()
            if hasattr(res, 'success') and not res.success:
                self.node.get_logger().error("Lỗi: Robot từ chối lệnh di_chuyen_home!")
                return False
                
        # Reset lại các biến khi về Home
        self.last_x = None
        self.last_y = None
        self.last_z = None
        self.accumulated_time = 0.0
        
        return True