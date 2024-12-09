import rclpy
from rclpy.node import Node

import pygame

import time
import threading

from joystick_msgs.msg import XBox360Controller


class XBoxDriver(Node):

    BUTTON_NAME = ['A', 'B', 'X', "Y", 'LB', 'RB', 'BACK', 'START', 'POWER', 'LS', 'RS']
    AXIS_NAME = ['LS_X', 'LS_Y', 'LT', 'RS_X', 'RS_Y', 'RT']
    HAT_NAME = ['X', 'Y']

    def __init__(self) -> None:
        super().__init__('xbox_360_controller')

        pygame.init()
        pygame.joystick.init()
        self._device = None

        self._rate = 30

        self._joystick_publisher = self.create_publisher(XBox360Controller, '/joystick', 3)

        self._is_activate = False

        self._joystick_thread = threading.Thread(target=self._joystick_loop)
        self._joystick_thread.start()

        self.shutdown = False
    
    def _get_joystick(self):
        if self._device: return self._device

        if pygame.joystick.get_count() == 0:
            self.get_logger().error("No joystick detected")
            return False
        elif pygame.joystick.get_count() > 1:
            self.get_logger().error("Multi joystick detected")
            return False
        else:
            self._device = pygame.joystick.Joystick(0)
            self._device.init()

            self._name = self._device.get_name()
            self.get_logger().info(f"{self._name} is connected")
            self._button_num = self._device.get_numbuttons()
            self._axis_num = self._device.get_numaxes()
            self._hat_num = self._device.get_numhats()

            return self._device
        
    def _joystick_loop(self):
        try:
            while not self._get_joystick(): time.sleep(1)
            self._is_activate = True
            
            while rclpy.ok():
                if self.shutdown: break

                events = pygame.event.get()

                if not self._is_activate:
                    if self._device.get_button(self.BUTTON_NAME.index('POWER')) == 1:
                        self._is_activate = True
                        self.get_logger().info("Joystick activated, press POWER button to deactivate")
                        time.sleep(0.2)
                else: self.get_logger().info("Joystick activated, press POWER button to deactivate")

                while self._is_activate:
                    events = pygame.event.get()

                    # if self._device.get_button(self.BUTTON_NAME.index('POWER')) == 1:
                    #     self._is_activate = False
                    #     self.get_logger().info("Joystick deactivated, press POWER button to activate")
                    #     time.sleep(0.2)
                    #     continue
                    if self._device.get_button(self.BUTTON_NAME.index('POWER')) == 1:
                        self._is_activate = False
                        self.get_logger().info("Joystick shutdown")
                        self.shutdown = True
                        time.sleep(0.2)
                        break
                    
                    button_list, axis_list, hat_list = [], [], []
                    for i in range(self._button_num):
                        button_list.append(int(self._device.get_button(i)))
                    for i in range(self._axis_num):
                        axis_list.append(float(self._device.get_axis(i)))
                    for i in range(self._hat_num):
                        x, y = self._device.get_hat(i)
                        hat_list.append(int(x))
                        hat_list.append(int(y))
                    
                    msg = XBox360Controller()
                    msg.header.stamp = self.get_clock().now().to_msg()
                    msg.header.frame_id = "joystick_data"
                    msg.name = self._name
                    msg.buttons = button_list
                    msg.axes = axis_list
                    msg.hats = hat_list
                    try:
                        msg.button_a = button_list[self.BUTTON_NAME.index('A')]
                        msg.button_b = button_list[self.BUTTON_NAME.index('B')]
                        msg.button_x = button_list[self.BUTTON_NAME.index('X')]
                        msg.button_y = button_list[self.BUTTON_NAME.index('Y')]
                        msg.button_lb = button_list[self.BUTTON_NAME.index('LB')]
                        msg.button_rb = button_list[self.BUTTON_NAME.index('RB')]
                        msg.button_back = button_list[self.BUTTON_NAME.index('BACK')]
                        msg.button_start = button_list[self.BUTTON_NAME.index('START')]
                        msg.button_power = button_list[self.BUTTON_NAME.index('POWER')]
                        msg.button_ls = button_list[self.BUTTON_NAME.index('LS')]
                        msg.button_rs = button_list[self.BUTTON_NAME.index('RS')]
                    except: pass
                    try:
                        msg.axis_ls_x = axis_list[self.AXIS_NAME.index('LS_X')]
                        msg.axis_ls_y = axis_list[self.AXIS_NAME.index('LS_Y')]
                        msg.axis_lt = axis_list[self.AXIS_NAME.index('LT')]
                        msg.axis_rs_x = axis_list[self.AXIS_NAME.index('RS_X')]
                        msg.axis_rs_y = axis_list[self.AXIS_NAME.index('RS_Y')]
                        msg.axis_rt = axis_list[self.AXIS_NAME.index('RT')]
                    except: pass
                    try:
                        msg.hat_x = hat_list[self.HAT_NAME.index('X')]
                        msg.hat_y = hat_list[self.HAT_NAME.index('Y')]
                    except: pass
                    
                    self._joystick_publisher.publish(msg)
                    time.sleep(1 / self._rate)
        except KeyboardInterrupt:
            self.get_logger().warn("Keyboard Interrupt")
        finally:
            self._device.quit()
            pygame.joystick.quit()
            pygame.quit()
            self.get_logger().info("Node end")


def main(args=None):
    rclpy.init(args=args)

    node = XBoxDriver()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=1)
            if node.shutdown: break
            
    except KeyboardInterrupt: print("Keyboard Interrupt")
    finally:
        node.destroy_node()
        rclpy.shutdown()
