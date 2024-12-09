# XBOX 360 Controller

std_msgs/Header header

uint8[] buttons
float32[] axes
int8[] hats

string name

# BUTTON_NAME = ['A', 'B', 'X', "Y", 'LB', 'RB', 'BACK', 'START', 'POWER', 'LS', 'RS']
# AXIS_NAME = ['LS_X', 'LS_Y', 'LT', 'RS_X', 'RS_Y', 'RT']
# HAT_NAME = ['X', 'Y']

uint8 button_a
uint8 button_b
uint8 button_x
uint8 button_y
uint8 button_lb
uint8 button_rb
uint8 button_back
uint8 button_start
uint8 button_power
uint8 button_ls
uint8 button_rs

float32 axis_ls_x
float32 axis_ls_y
float32 axis_lt
float32 axis_rs_x
float32 axis_rs_y
float32 axis_rt

int8 hat_x
int8 hat_y
