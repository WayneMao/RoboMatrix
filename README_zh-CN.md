## RoboMatrix-ROS2
<!-- ![logo](assets/logo.png) -->

<!-- <img src="assets/logo.png" alt="logo" style="width:50%;"/> -->

<!-- <p align="center">
    <img src="assets/logo.png" alt="logo" style="width:50%;"/>
</p> -->

<div align="center">
    <img src="resources\robomatrix-logo3.png" alt="logo" width="50%">
</div>


<div align="center">
[English](README.md) | 简体中文
</div>


English | [简体中文](README_zh-CN.md)

## Introduction
RoboMatrix是一个具有层级化设计理念的具身智能项目。  
主分支代码目前支持 PyTorch 2.0、langchain 0.2.8及其以上的版本。


## Installation

### Install ROS2

**注意：如果你的系统里已经安装ROS2，跳过此步。**

**ROS2版本（附官方安装指南）**
* Ubuntu 20.04 ---> ROS2 Foxy ---> [官方安装步骤](https://docs.ros.org/en/foxy/Installation/Ubuntu-Install-Debians.html)
* Ubuntu 22.04 ---> ROS2 Humble ---> [官方安装步骤](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html)

**通用安装流程**

**1. 设置编码UTF-8**

终端输入，检查是否支持UTF-8

```bash
locale
```

如果不支持（终端输出没有UTF-8）

```bash
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

**2. 检查是否启用Ubuntu Universe存储库**

终端输入，查看是否有输出

```bash
apt-cache policy | grep universe
```

若没有启用（终端没有输出）

```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
```

**3. 添加ROS2的apt库**

```bash
sudo apt update && sudo apt install curl gnupg2 lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

**4. 安装ROS2**

安装指定的版本 ros-<distro>-desktop 以foxy为例

```bash
sudo apt update
sudo apt install ros-foxy-desktop
```

**5. 配置环境**

```bash
echo "source /opt/ros/foxy/setup.bash" >> ~/.bashrc
source .bashrc
```

**6. 测试demo**

```bash
ros2 run demo_nodes_cpp talker
ros2 run demo_nodes_cpp listener
```

**7. 安装编译工具**

```bash
sudo apt install python3-colcon-common-extensions
```

### Create conda env

**注意：创建的Conda环境的Python版本需要与ROS2调用的Python版本一致，即：Ubuntu 20.04 使用 Python 3.8，Ubuntu 22.04 使用 Python 3.10。**

**1. Ubuntu 20.04（默认 Python 3.8.10）**

```bash
conda create -n robomatrix python=3.8 -y
conda activate robomatrix
```

**2. Ubuntu 22.04（默认 Python 3.10.12）**

```bash
conda create -n robomatrix python=3.10 -y
conda activate robomatrix
```

### Install RoboMaster SDK

**注意：请确保上一步创建的环境已激活，以安全地安装在虚拟环境中。**

**1. 安装依赖**
   
```bash
sudo apt install libopus-dev python3-pip
python3 -m pip install -U numpy numpy-quaternion pyyaml
```

**2. 从源码安装**
   
```bash
python3 -m pip install git+https://github.com/jeguzzi/RoboMaster-SDK.git
python3 -m pip install git+https://github.com/jeguzzi/RoboMaster-SDK.git#"egg=libmedia_codec&subdirectory=lib/libmedia_codec"
```

### Create ROS2 workspace

```bash
mkdir -p ~/robomatrix_ros2/src && cd ~/robomatrix_ros2/src
git clone https://git-core.megvii-inc.com/zhongweiheng/robomatrix-ros2.git
cd ~/robomatrix_ros2 && colcon build
```

### Install RoboMatrix requirements （暂未使用，请跳过）

**注意：请确保上一步创建的环境已激活，以安全地安装在虚拟环境中。**

```bash
cd ~/robomatrix_ros2
pip install -r requirements.txt
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
```

### Third party （暂未使用，请跳过）

**本项目引入了 `Grounding-DINO-1.5-API`，用于2D检测。**

**安装方法**
clone到RoboMatrix文件夹下：
```bash
git clone https://github.com/IDEA-Research/Grounding-DINO-1.5-API.git
cd Grounding-DINO-1.5-API/
pip install -v -e .
```
run demo
```bash
python demo/demo.py --token <API_TOKEN>
```

## Datasets

### 数据采集

**1. 定点抓取**

**功能描述：使用Joystick遥操作控制机械臂运动，抓取易拉罐、方块等物体，保存video和annotation。**

```bash
cd ~/robomatrix_ros2
source install/setup.bash
ros2 launch robomaster_ros collect_data.launch.py name:=your_task_name idx:=your_episode_index dir:=your_save_directory
```

**注意事项**
1. `name`参数传入任务的名称，`idx`参数传入第几轮，`dir`参数传入视频和标签保存的目录。每一季采集，只需要不断更改`idx`即可，任务名和路径无需更改。
2. 启动launch文件前，将电脑连接至HUAWEI-Robot-WiFi5，上电EP机器人，等待连接（成功后会发出提示音），并插入手柄。
3. 启动后，终端提示成功检测手柄为XBOX，同时EP的机械臂运动至初始状态（肉眼可见一个震颤），手爪处于完全打开的状态，终端提示可以进行后续操作。若以上状态有任何一项没有达到，对终端进行`Ctrl+C`操作杀死进程，并重新启动launch文件。
4. 一切准备就绪后，按下手柄的`Start`按键，终端显示不断获取到Frame，即可开始操作手柄。若获取Frame的速度很慢，可以等待一会儿，若等待之后依旧很慢，杀死进程重新启动launch文件。
5. 手柄的`A`按键打开夹爪，`B`按键关闭夹爪，`Hat`键组控制机械臂在平面内移动。操作过程中切忌连续按，每一次按下可等待动作执行完成后再继续，确保数据安全地记录下来，防止丢帧。机械臂的工作空间受限，在极限位置会无法移动，避开即可。
6. 任务执行完后，按下`Back`按键保存视频和标签，等待终端提示，完成后`Ctrl+C`，开启下一轮任务。
7. 电池电量能支持1h多，相机过热后会出现明显丢帧，可更换相机解决。更换相机后，需重新对EP进行上电操作。

**2. 移动操作**

**功能描述：使用Joystick遥操作控制底盘和机械臂的运动，抓取易拉罐、方块等物体，放入指定框中，保存video和annotation。**

**操作步骤**
1. 将电脑的WiFi连接至`HUAWEI-Robot-WiFi5`，启动EP机器人，等待连接成功（发出提示音），插入手柄。
2. 启动launch文件，`name`参数传入任务的名称，`idx`参数传入第几轮，`dir`参数传入视频和标签保存的目录。每一季采集，只需要不断更改`idx`即可，任务名和路径无需更改。
```bash
cd ~/robomatrix_ros2
source install/setup.bash
ros2 launch robomaster_ros collect_data_new.launch.py name:=your_task_name dir:=your_save_directory idx:=your_episode_index
```
3. 成功检测手柄为XBOX，等待机械臂抬升，手爪完全打开。按下手柄的`START`开始控制，任务完成后按下`BACK`保存视频和标注，成功保存后按下`POWER`退出。
4. 右拨杆`RS`控制底盘移动，`RS`键加速，`LT`和`RT`控制底盘旋转。
5. `Hat`控制机械臂在平面内移动，`LB`键下降机械臂到抓取点，`RB`键抬升机械臂到放置点。
6. `A`键打开夹爪，`B`键关闭夹爪，`X`键停止夹爪。

### 数据集目录结构
RoboMatrixDatasets是任务导向的数据集结构，依据任务种类独立存储，每个任务的独立文件夹可以被视为一个“子数据集”，其中包含与该任务相关的数据采集。这样的结构便于管理和访问，清晰地将不同任务的数据分开，方便后续的分析和处理。

**1. 原始数据集目录**
```bash
RoboMatrixDatasets/
├── task_folder
│   ├── annotations
│   │   ├── episode_n.json
│   │   └── ... (other annotation files)
│   ├── videos
│   │   ├── episode_n.mp4
│   └── └── ... (other video files)
└── ... (other task folders)
```

**2. 后处理数据集目录**
```bash
RoboMatrixDatasets/
├── task_folder
│   ├── annotations
│   │   ├── episode_n.json
│   │   └── ... (other annotation files)
│   ├── annotations_preprocess
│   │   ├── episode_n.json
│   │   └── ... (other preprocessed annotation files)
│   ├── annotations_token
│   │   ├── episode_n.json
│   │   └── ... (other tokenized annotation files)
│   ├── videos
│   │   ├── episode_n.mp4
│   │   └── ... (other video files)
│   ├── videos_oss
│   │   ├── episode_n.mp4
│   │   └── ... (other converted videos)
│   ├── plots
│   │   ├── arm_position.png
│   │   ├── chassis_position_attitute.png
│   │   ├── gripper_action.png
│   │   └── ... (additional plots)
│   ├── data_distribution.json
│   ├── data_information.yaml
│   └── annotation.json
└── ... (other task folders)
```

**3. 目录结构说明**

对于RoboMatrixDatasets内的每个任务文件夹，内部包含该任务采集的独立的观测视频、独立的原始数据标注、独立的后处理的数据标注、独立的tokenized数据、数据分布、数据集详细信息、完整数据标注。

* annotations（文件夹）：存放数据采集过程中每一个episode的原始标注（JSON），每一个JSON里包含对应观测视频每一帧的机器人observations，例如移动底盘位置、机械臂末端位置、夹爪状态等。
* videos（文件夹）：存放数据采集过程中每一个episode的观测视频（MP4）。
* annotations_preprocess（文件夹）：存放对原始标注处理后的标注，从每一个JSON文件中的observations中提取观测视频的actions并保存。
* annotations_token（文件夹）：对所有的标注进行tokenization，计算每一个JSON文件中每一帧的action value并保存。
* videos_oss（文件夹）：将原始观测视频转码，以供在OSS上直接点开。
* plots（文件夹）：分bin后的数据分布图。
* data_distribution.json：分bin后的数据分布。
* data_information.yaml：数据集的详细信息。
* annotation.json：将所有tokenized标注合并成一个JSON以供训练。

### 数据处理

**通用流程**

1. 预处理标注：使用函数[preprocess_annotation](https://git-core.megvii-inc.com/zhongweiheng/robomatrix-ros2/-/blob/master/robomatrix/robomatrix/funcs.py#L63)，给定原始标注的文件夹路径，给定存放后处理的文件夹名称，给定任务名称，从每一个原始标注的observation中提取出action。
2. 分析数据集：使用函数[get_dataset_info](https://git-core.megvii-inc.com/zhongweiheng/robomatrix-ros2/-/blob/master/robomatrix/robomatrix/funcs.py#L123)，给定数据集文件夹路径，给定存放标注的文件夹名称，给定存放视频的文件夹名称，获取数据集的详细信息，保存为YAML文件。
3. 计算数据分布：使用函数[get_data_distribution](https://git-core.megvii-inc.com/zhongweiheng/robomatrix-ros2/-/blob/master/robomatrix/robomatrix/funcs.py#L168)，给定标注的文件夹路径，给定action中需要处理的多个label，计算每一个label所有维度的数据范围，保存为JSON文件。
4. 分bin：在[TokenizeDataset](https://git-core.megvii-inc.com/zhongweiheng/robomatrix-ros2/-/blob/master/robomatrix/robomatrix/get_llava_data_mobile_manipulation_v3.2.py#L13)中，根据求得的数据分布，对每一个episode的每一帧进行tokenization，保存为最终的标注JSON文件。
5. 视频转码：使用函数[transfer_video](https://git-core.megvii-inc.com/zhongweiheng/robomatrix-ros2/-/blob/master/robomatrix/robomatrix/funcs.py#L251)，对每一个原始视频进行转码，保存在新的文件夹中。

具体操作方法，详见[完整流程](https://git-core.megvii-inc.com/zhongweiheng/robomatrix-ros2/-/blob/master/robomatrix/robomatrix/get_llava_data_mobile_manipulation_v3.2.py#L130)。

**pick_place任务**

**描述**：机械臂抓起平地的可乐瓶，采集员将篮子放在机器人面前，机械臂将可乐瓶放入篮子。

**数据处理的目标**
1. 剔除采集员放篮子的动作，将任务分为2个stage，第1个stage是抓起可乐瓶，第2个stage是放入篮子，每个stage保存相应的prompt。
2. 将机器人的action分成256个bin，计算bin值并保存。

**思路与方法**
1. 计算数据分布：统计机器人的action每一个维度的最大值和最小值。
2. 分bin：计算机器人的action落在第几个bin。
3. 用YOLO-World检测采集员的手和手表，最先出现的时刻作为前一个stage的结束，最后出现的时刻作为后一个stage的开始。前一个stage的prompt是`pick`，后一个stage的prompt是`place`。
4. 检测每个视频里出现花屏现象的帧id。
5. 保存每个视频中，图像正常的帧的bin值和prompt，到json文件。

**程序入口**
```bash
cd ~/robomatrix_ros2/src/robomatrix/robomatrix
python get_llava_data_manipulation.py
```

## 开发流程指南
请 Follow [开发教程](http://transformer.pages-git-core.megvii-inc.com/Perceptron/tutorial/develop.html)

## 参考资料

### Repo

* [Robomaster-ROS](https://github.com/jeguzzi/robomaster_ros)
* [Grounding DINO 1.5](https://github.com/IDEA-Research/Grounding-DINO-1.5-API)

### Paper

* TODO
  
