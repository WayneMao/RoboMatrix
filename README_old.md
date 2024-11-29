# RoboMatrix-ROS2

<div align="center">
    <img src="resources\robomatrix-logo3.png" alt="logo" width="70%">
</div>

<div align="center">

English | [简体中文](README_zh-CN.md)  

</div>

**目前请优先看中文文档**

## Setup

### Install ROS 2

**Note: If ROS2 is already installed on your system, please skip this step.**

**ROS2 distro for your Ubuntu**
* Ubuntu 20.04 ---> ROS2 Foxy ---> [official installation guidance](https://docs.ros.org/en/foxy/Installation/Ubuntu-Install-Debians.html)
* Ubuntu 22.04 ---> ROS2 Humble ---> [official installation guidance](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html)

**Genereral installation steps**

**1. Set UTF-8**

Open a terminal，check weather your system supports UTF-8.

```bash
locale
```

If not support (no output in terminal), please install.

```bash
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

**2. Set Ubuntu Universe**

Open a terminal，check weather your system supports Ubuntu Universe.

```bash
apt-cache policy | grep universe
```

If not support (no output in terminal), please install.

```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
```

**3. Add ROS2 software source and key**

```bash
sudo apt update && sudo apt install curl gnupg2 lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

**4. Get ROS 2**

Install the specified version of ROS 2, using Foxy as an example.

```bash
sudo apt update
sudo apt install ros-foxy-desktop
```

**5. Source bash**

```bash
echo "source /opt/ros/foxy/setup.bash" >> ~/.bashrc
source .bashrc
```

**6. Test demo**

```bash
ros2 run demo_nodes_cpp talker
ros2 run demo_nodes_cpp listener
```

**7. Install colcon**

```bash
sudo apt install python3-colcon-common-extensions
```

### Create conda environment

**Note: The Python version of the Conda environment created needs to be consistent with the Python version called by ROS2, that is, Ubuntu 20.04 uses Python 3.8, and Ubuntu 22.04 uses Python 3.10.**

**1. Ubuntu 20.04 (default Python 3.8.10)**

```bash
conda create -n robomatrix python=3.8 -y
conda activate robomatrix
```

**2. Ubuntu 22.04 (default Python 3.10.12)**

```bash
conda create -n robomatrix python=3.10 -y
conda activate robomatrix
```

### Install RoboMaster SDK

**Note: Please ensure that the environment created in the previous step is activated for safe installation in the virtual environment.**

**1. Install dependencies**
   
```bash
sudo apt install libopus-dev python3-pip
python3 -m pip install -U numpy numpy-quaternion pyyaml
```

**2. Install from source code**
   
```bash
python3 -m pip install git+https://github.com/jeguzzi/RoboMaster-SDK.git
python3 -m pip install git+https://github.com/jeguzzi/RoboMaster-SDK.git#"egg=libmedia_codec&subdirectory=lib/libmedia_codec"
```

### Create ROS 2 workspace

```bash
mkdir -p ~/robomatrix_ros2/src && cd ~/robomatrix_ros2/src
git clone https://git-core.megvii-inc.com/robotic/robomatrix-ros2.git
cd ~/robomatrix_ros2 && colcon build
```

### Install RoboMatrix dependencies

**Note: Please ensure that the environment created in the previous step is activated for safe installation in the virtual environment.**

```bash
cd ~/robomatrix_ros2
pip install -r requirements.txt
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
```

### Third party

**`Grounding-DINO-1.5-API`**: COMING SOON !

### Usage

### RoboMaster EP robotic arm data collection v1.0

**Function description: Use joystick to control the robotic arm, grab objects such as cans and blocks, save videos and annotations.**

```bash
cd ~/robomatrix_ros2
source install/setup.bash
ros2 launch robomaster_ros collect_data.launch.py name:=your_task_name idx:=your_episode_index dir:=your_save_directory
```

**NOTEs**

**For now, please refer to the Chinese README.**

## Development guidance

**Follow [guidance](http://transformer.pages-git-core.megvii-inc.com/Perceptron/tutorial/develop.html)**

## References

### Projects

* [Robomaster-ROS](https://github.com/jeguzzi/robomaster_ros)
* [Grounding DINO 1.5](https://github.com/IDEA-Research/Grounding-DINO-1.5-API)

### Papers

* TODO
