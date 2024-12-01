<div align="center">
    <img src="resources\robomatrix-logo3.png" alt="logo" width="70%">
</div>

<div align="center">

English | [简体中文](README_zh-CN.md)  

</div>

# RoboMatrix: A Skill-centric Hierarchical Framework for Scalable Robot Task Planning and Execution in Open-World

### 📝[Paper]() | 🌍[Project Page](https://robo-matrix.github.io/) | 🛢️[Data]()
  
![eight_skills](resources/eight_skills.gif)

## 📰 News

## Installation
### 1. Install ROS 2

**Note: If ROS2 is already installed on your system, please skip this step.**

**ROS2 distro for your Ubuntu**
* Ubuntu 20.04 ---> ROS2 Foxy ---> [official installation guidance](https://docs.ros.org/en/foxy/Installation/Ubuntu-Install-Debians.html)
* Ubuntu 22.04 ---> ROS2 Humble ---> [official installation guidance](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html)

**Install colcon**
```bash
sudo apt install python3-colcon-common-extensions
```

### 2. Build workspace
```bash
mkdir -p ~/RoboMatrix/src && cd ~/RoboMatrix/src
git clone https://github.com/WayneMao/RoboMatrix.git
cd ~/RoboMatrix && colcon build
```

### 3. Install dependencies
```bash
sudo apt install libopus-dev python3-pip
python3 -m pip install -U numpy numpy-quaternion pyyaml

# Install RoboMaster-SDK
python3 -m pip install git+https://github.com/jeguzzi/RoboMaster-SDK.git
python3 -m pip install git+https://github.com/jeguzzi/RoboMaster-SDK.git#"egg=libmedia_codec&subdirectory=lib/libmedia_codec"

# install dependencies and torch
pip install -r requirements.txt
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
```
### 4. Third party
**Grounding-DINO-1.5-API**
```bash
cd src/robomatrix_client/robomatrix_client
git clone https://github.com/IDEA-Research/Grounding-DINO-1.5-API.git
cd Grounding-DINO-1.5-API
pip install -v -e .
```
## Deployment on Real-Robots

## TODO
- [ ] Package Docker
- [ ] Release fine-tuning dataset
- [ ] Optimize VLA ROS communication
- [ ] Open source VLA Skill model code
- [ ] Release VLA Skill model weights
- [ ] Open source Shooting code

## Citation

If you find our work helpful, please cite us:

```bibtex

```

## Acknowledgments
- Implementation of Vision-Language-Action (VLA) skill model is based on [LLaVA](https://github.com/haotian-liu/LLaVA/).  
- RoboMatrix-ROS is based on [RoboMaster-SDK](https://github.com/dji-sdk/RoboMaster-SDK) and [ROS2](https://github.com/ros2).
- Some additional libraries: [Grounding-DINO-1.5](https://github.com/IDEA-Research/Grounding-DINO-1.5-API), [YOLO-World](https://github.com/AILab-CVC/YOLO-World).
