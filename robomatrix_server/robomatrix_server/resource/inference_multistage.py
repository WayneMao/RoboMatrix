import os
import time

from .utils import HOME_PATH, log_info, log_warn, save_video_v2
from .funcs import BaseRobotInference

LED = {
    0: (255, 0, 255),
    1: (0, 255, 255),
}


class RobotInference(BaseRobotInference):

    def __init__(self, node, dataset_dir, task_name, url="http://localhost:7893/process_frame", debug=True) -> None:
        super().__init__(node, task_name=task_name, dataset_dir=dataset_dir, url=url)
        self.debug = debug
        
    def exec_vla_task(self, task, prompt):
        frame_count, fail_count= 0, 0
        try:
            log_warn(f"Press ENTER to start.")
            input()

            current_stage = 1
            total = 0
            temp_init = 1.0
            temp_high = 1.1
            self._robot.led.set_led(comp="all", r=LED[current_stage%2][0], g=LED[current_stage%2][1], b=LED[current_stage%2][2], effect='on', freq=1)
            while self._robot_ok:
                image = self.get_image()

                if not image.any():
                    fail_count += 1
                    continue
                frame_count += 1
                print(f"Get a frame {frame_count}")
                
                print(f"Prompt: {prompt}")

                # temperature
                temp = temp_init if total < 5 else temp_high

                token = self.get_llava_output(image, prompt, temp=temp)
                print(f"LLaVa response: {token}")

                # decode
                tokens = token.split()
                flag = False
                if len(tokens) != 7: continue
                for token in tokens:
                    if not token.isdigit():
                        flag = True
                        break
                if flag: continue

                # stop
                stage_end = tokens[0]
                if stage_end == "1" \
                    or ("release" in prompt.lower() and total > 5) \
                        or (("grasp" in prompt.lower() or "position" in prompt.lower()) and total > 10) \
                            or ("move" in prompt.lower() and total > 15):
                    
                    log_info(f"Current stage {current_stage} is end.")
                    current_stage += 1
                    total = 0
                    self._robot.led.set_led(comp="all", r=LED[current_stage%2][0], g=LED[current_stage%2][1], b=LED[current_stage%2][2], effect='on', freq=1)
                    return True

                # chassis
                scale = 10
                
                d_x = self._chassis_position_x_decoder.decode(tokens[1])
                if abs(d_x) < 1: d_x = 0
                elif abs(d_x) < 10: d_x = d_x * scale / 1000
                else: d_x /= 1000
                
                d_y = self._chassis_position_y_decoder.decode(tokens[2])
                if abs(d_y) < 1: d_y = 0
                elif abs(d_y) < 10: d_y = d_y * scale / 1000
                else: d_y /= 1000
                
                d_yaw = self._chassis_position_yaw_decoder.decode(tokens[3])
                if abs(d_yaw) < 1: d_yaw = 0
                d_yaw = - d_yaw
                
                # arm
                x = self._arm_position_x_decoder.decode(tokens[4])
                y = self._arm_position_y_decoder.decode(tokens[5])

                arm_d_x, arm_d_y = x - self._arm_x, y - self._arm_y
                if "grasp" in prompt.lower() or "position" in prompt.lower():
                    if 2 < arm_d_y < 5: y = self._arm_y + 5
                    elif 5 <= arm_d_y < 8: y = self._arm_y + 8
                    elif arm_d_y >= 8: y = self._arm_y + 10

                # gripper
                if tokens[6] == "0": g = "release"
                elif tokens[6] == "1": g = "grab"
                else: g = "pause"
                
                # info
                log_info(f"Chassis: {round(d_x,2)}, {round(d_y,2)}, {round(d_yaw,2)}")
                # print(f"Arm: {x}, {y}")
                log_info(f"Arm: {round(arm_d_x,2)}, {round(arm_d_y,2)}")
                log_info(f"Gripper: {g}")

                log_warn(f"Wait: {total}, temp: {temp}")
                
                # action
                self.chassis_move(0, 0, float(d_yaw))
                self.chassis_move(float(d_x), float(d_y), 0)
                self.arm_moveto((int(x), int(y)))
                self.gripper(g, 20)

                if ("move" in prompt.lower() and d_x == 0 and d_y == 0 and d_yaw == 0) \
                    or ("release" in prompt.lower() and g == "release") \
                        or ("grasp" in prompt.lower() and abs(arm_d_x) < 2 and abs(arm_d_y) < 2):
                    last = True
                else:
                    last = False
                    total = 0
                if last:
                    if ("move" in prompt.lower() and d_x == 0 and d_y == 0 and d_yaw == 0) \
                        or ("release" in prompt.lower() and g == "release") \
                            or (("grasp" in prompt.lower() or "position" in prompt.lower()) and abs(arm_d_x) < 2 and abs(arm_d_y) < 2):
                        total += 1
        except KeyboardInterrupt: pass
        
    def exec_get_audio(self, file_path):
        print("Recording... ")
        res = self._vision.record_audio(save_file=file_path, seconds=5, sample_rate=16000)
        print("audio file save in: ", file_path)
        return res

