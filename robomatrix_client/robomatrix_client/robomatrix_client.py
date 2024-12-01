import os
import yaml
import re
import json
import sys
import threading
import requests
import ast
import logging
from rich.logging import RichHandler
from time import time
from typing import List, Dict, Any

from PIL import Image

import openai
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from gdino import GroundingDINOAPIWrapper, visualize

from .agent_propmts import RULE_PROMPT
from .agent_skills import SKILLS, META_SKILLS, TASK
from .audio2text import AudioProcessor
import ipdb  # noqa

# import ros2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from robomatrix_interface.srv import Vla, Audio
import requests
import subprocess
import cv2
timeout_duration = 10 * 60  # 10 minutes in seconds

# # 设置基本配置
# logging.basicConfig(
#     level=logging.DEBUG,  # 设置日志级别
#     format="%(asctime)s - %(levelname)s - %(message)s",  # 日志输出格式
#     datefmt="%Y-%m-%d %H:%M:%S"
# )

def check_network():
    """Check if the network is accessible by trying to access Google and Baidu"""
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        try:
            response = requests.get("https://www.baidu.com", timeout=5)
            return response.status_code == 200
        except requests.ConnectionError:
            return False

def run_proxy_command():
    """Run the proxy command to set up the network proxy"""
    command = f"eval $(curl -s http://deploy.i.brainpp.cn/httpproxy)"
    try:
        subprocess.call(command, shell=True, check=True)
        print("Proxy command executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute proxy command: {e}")

# 配置日志记录器
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[RichHandler()]
)

logger = logging.getLogger("rich_logger")

root_path= os.getcwd()
cfg_path = os.path.join(root_path, "src", "config.yaml")

with open(cfg_path, 'r') as f:
    OPENAI_CONFIG = yaml.load(f, Loader=yaml.FullLoader)

Grounding_DINO_15_API = OPENAI_CONFIG['Grounding_DINO_1.5_API']

class RoboMatrix(Node):

    def __init__(self, api_type='ChatOpenAI'):
        super().__init__('rmm')
        # get image from ros2 img_topic
        self._sub_image = self.create_subscription(Image, "/camera/raw/image", self._image_cb, 1000)
        self._cv_bridge = CvBridge()
        self.cur_image = None
        
        # create client
        self.vla_client = self.create_client(Vla, 'vla_service')
        self.audio_client = self.create_client(Audio, 'audio_service')
        while not self.vla_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('VLA Service not available, waiting again...')
        while not self.audio_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Audio Service not available, waiting again...')
        self.vla_req = Vla.Request()
        self.audio_req = Audio.Request()

        self.audio_path = "src/robomatrix_client/robomatrix_client/audios/task.wav"  # Replace with your audio file path
        api_key = OPENAI_CONFIG['AssemblyAI_API']

        self.processor = AudioProcessor(audio_file=self.audio_path, api_key=api_key)

        # Init config
        self.api_type = api_type
        if api_type == 'OpenAI':
            openai.api_key = os.environ["OPENAI_API_KEY"]
            openai.base_url = os.environ["OPENAI_API_BASE"]
            model = OpenAI(model_name="text-davinci-003", max_tokens=1024)
        elif api_type == 'ChatOpenAI':
            print('LLM: ChatOpenAI')
            os.environ["OPENAI_API_KEY"] = OPENAI_CONFIG['OPENAI_KEY']
            os.environ["OPENAI_API_BASE"] = OPENAI_CONFIG['OPENAI_API_BASE']
            model = ChatOpenAI(
                temperature=0,
                model_name='gpt-4o-mini',
                # model_name='gpt-4o',
                # model_name='o1-mini',
                max_tokens=1024,
                # request_timeout=30
                timeout=30
            )
        elif api_type == 'STEP1':
            print('LLM: STEP1')
            os.environ["OPENAI_API_KEY"] = OPENAI_CONFIG['STEP1_API_KEY']
            os.environ["OPENAI_API_BASE"] = OPENAI_CONFIG['STEP1_API_BASE']
            model = ChatOpenAI(model_name="open_prod_model")

        # Task system template
        system_template = f"""You are an intelligent mobile robot, The skills you have are {SKILLS}. \
                            {RULE_PROMPT} \
                            The current environment is an office setting. \
                            Based on the tasks I provide, help me break down the tasks into multiple actionable steps. \
                            Let's think step by step. Here is an example. "Place the red cola can in the trash bin." Once you made a final result, output it in the following format:\n
                    ```
                        "steps_1":"<VLA>: Move to the red cola can",
                        "steps_2":"<VLA>: Grasp the red cola can",
                        "steps_3":"<VLA>: Move to the trash bin",
                        "steps_4":"<VLA>: Position the red cola can over the trash bin",
                        "steps_5":"<VLA>: Release the red cola can"
                    ```\n
                    """
        system_template_obj = "Extract the object in the sentence. Example: 'Grasp the red cola can', output the 'cola can' without any other word."

        print(system_template)
        prompt_template = ChatPromptTemplate.from_messages([
            ('system', system_template),
            ('user', '{text}')
        ])

        prompt_obj = ChatPromptTemplate.from_messages([
            ('system', system_template_obj),
            ('user', '{text}')
        ])
        # 3. Create parser
        parser = StrOutputParser()
        # 4. Create chain  
        self.chain = prompt_template | model | parser # task planning
        self.chain_obj = prompt_obj | model | parser  # split obj for gdino detection
    
    
    def _image_cb(self, msg: Image):

        self.cur_image = self._cv_bridge.imgmsg_to_cv2(msg, 'passthrough')

    def split_task(self, text):
        print("Start split task")
        action = self.chain.invoke({"text": text})
        print(action)
        return action

    def get_gdino(self, text=''):
        gdino = GroundingDINOAPIWrapper(Grounding_DINO_15_API)
        if self.cur_image is None:
            print('Can not get img!')
            return None
        prompts = dict(image=self.cur_image, prompt=text)
        results = gdino.inference(prompts)

        return results

    def vis_gdino(self, img_path, results, save_path):
        # now visualize the results
        image_pil = Image.open(img_path)
        image_pil = visualize(image_pil, results)
        # dump the image to the disk
        if save_path is None:
            save_path = img_path.replace('.jpg', '_output.jpg')
        image_pil.save(save_path)
        print(f'The output image has been saved to {save_path}')



    def format_output(self, result, type='json'):
        # ipdb.set_trace()
        if type == 'json':
            try:
                if "`" in result:
                    # result = result.replace("`", "")
                    result = re.findall(r'```(.*?)```', result, re.DOTALL)
                    json_str = "{" + result[0] + "}"
                    result = json.loads(json_str)
                # ipdb.set_trace()
                return result
            except ValueError:
                # ipdb.set_trace()
                logging.error("This is an incorrect json format.")
                return {}
    
    def core_loop(self):
        
        while True:
            # ---- call sever ---- #
            self.audio_req.path = self.audio_path
            res = self.audio_client.call_async(self.audio_req)
            rclpy.spin_until_future_complete(self, res)
            # Transcribe the audio
            self.processor.process_audio()
            input_text = self.processor.transcribe_audio()
            print("Identify task: ", input_text)

            # print("User: ",  end="")
            # input_text = input()
            # if input_text == '':
            #     # input_text = "Place the red cola can into the white box."
            #     input_text = "Put the red coke can in the open drawer and then close the drawer"
            #     print(input_text)

            timer = threading.Timer(timeout_duration, exit_program)
            timer.start()

            task_steps = self.split_task(input_text)
            print("Task steps: \n", task_steps)
            task_steps_dict = self.format_output(task_steps)
            print("Task steps dict: \n", task_steps_dict)

            # import pdb;pdb.set_trace()
            _, obj_prompt = task_steps_dict['steps_1'].split(':')
            obj = self.chain_obj.invoke({"text": obj_prompt.strip()})
            print(obj)
            info = self.get_gdino(obj)
            confidence = any([score > 0.5 for score in info['scores']])
            if not confidence:
                print(f"Did not observe the {obj}! Task reset!")
                continue

            for i,item in enumerate(task_steps_dict.values()):
                task, prompt = item.split(':')
                print(f"Step {i+1}: {item}")
                print(f"task: {task}", f"prompt: {prompt.strip()}")

                self.vla_req.task = TASK[task]
                self.vla_req.msg = prompt.strip()

                # ---- call sever ---- #
                self.future = self.vla_client.call_async(self.vla_req)
                rclpy.spin_until_future_complete(self, self.future)
                #         -----         #
            print("Processed input and reset timer.")
              


# if no input for 10 minutes, exit the program
def exit_program():
    print(f"No new input for {timeout_duration} seconds. Exiting...")
    sys.exit(0)
    # os._exit(0)

def main():
    rclpy.init(args=None)
    # Check if the network is accessible
    if check_network():
        print("Network is working")
    else:
        print("Network connection failed")
        run_proxy_command()

    logging.info("Init RoboMatrix...")
    robot_matrix = RoboMatrix()
    
    # setting up the timer
    timer = threading.Timer(timeout_duration, exit_program)

    # start timer
    timer.start()
    loop = threading.Thread(target=robot_matrix.core_loop)
    loop.start()

if __name__=="__main__":
    main()