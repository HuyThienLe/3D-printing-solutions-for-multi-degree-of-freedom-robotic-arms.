ros2 launch dsr_bringup2 dsr_bringup2_gazebo.launch.py model:=a0509
    source son_ws/install/setup.bash 
source doosan_ws/install/setup.bash 
ros2 run doosan_printing_app in_gcode 


ros2 launch dsr_bringup2 dsr_bringup2_robot.launch.py model:=a0509 host:=192.168.137.100 port:=12345

ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py mode:=virtual model:=a0509 host:=127.0.0.1 

rm -rf build/ install/ log/