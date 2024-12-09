# Chassis esc

std_msgs/Header header

bool[4] valid # whenever a servo in connected to a port
int32[4] value # the angle of the servos (1024 corresponds to 180 degrees)
int32[4] speed # the speed of the servos (1024 corresponds to about 36 degrees per seconds)

robomaster_msgs/ServoSingleStatus servo_0
robomaster_msgs/ServoSingleStatus servo_1
robomaster_msgs/ServoSingleStatus servo_2
robomaster_msgs/ServoSingleStatus servo_3
