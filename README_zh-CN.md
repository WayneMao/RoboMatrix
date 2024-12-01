<div align="center">
    <img src="resources\robomatrix-logo3.png" alt="logo" width="70%">
</div>

<div align="center">

[English](README.md) | 简体中文

</div>

# RoboMatrix: A Skill-centric Hierarchical Framework for Scalable Robot Task Planning and Execution in Open-World

### 📝[论文]() | 🌍[项目主页](https://robo-matrix.github.io/) | 🛢️[数据]()

![eight_skills](resources/eight_skills.gif)

## 📰 新闻

## 安装
### 1. 安装 ROS2

**注意：如果您的系统上已安装 ROS2，请跳过此步骤。**

**适配您 Ubuntu 系统的 ROS2 版本**
* Ubuntu 20.04 ---> ROS2 Foxy ---> [官方安装指南](https://docs.ros.org/en/foxy/Installation/Ubuntu-Install-Debians.html)
* Ubuntu 22.04 ---> ROS2 Humble ---> [官方安装指南](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html)

**安装 colcon**
```bash
sudo apt install python3-colcon-common-extensions
```

### 2. 构建工作空间
```bash
mkdir -p ~/RoboMatrix/src && cd ~/RoboMatrix/src
git clone https://github.com/WayneMao/RoboMatrix.git
cd ~/RoboMatrix && colcon build
```

### 3. 安装依赖
```bash
sudo apt install libopus-dev python3-pip
python3 -m pip install -U numpy numpy-quaternion pyyaml

# 安装 RoboMaster-SDK
python3 -m pip install git+https://github.com/jeguzzi/RoboMaster-SDK.git
python3 -m pip install git+https://github.com/jeguzzi/RoboMaster-SDK.git#"egg=libmedia_codec&subdirectory=lib/libmedia_codec"

# 安装依赖和 PyTorch
pip install -r requirements.txt
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
```
### 4. 第三方依赖
**Grounding-DINO-1.5-API**
```bash
cd src/robomatrix_client/robomatrix_client
git clone https://github.com/IDEA-Research/Grounding-DINO-1.5-API.git
cd Grounding-DINO-1.5-API
pip install -v -e .
```

## 真机部署

## TODO
- [ ] 打包Docker
- [ ] 开放微调数据集
- [ ] 优化VLA ROS通信
- [ ] 开源VLA Skill model代码
- [ ] 开放VLA Skill Model权重
- [ ] 开源Shooting代码

## Citation

If you find our work helpful, please cite us:

```bibtex

```

## 致谢
- 视觉-语言-动作 (VLA) 技能模型的实现基于 [LLaVA](https://github.com/haotian-liu/LLaVA/)。  
- RoboMatrix-ROS 基于 [RoboMaster-SDK](https://github.com/dji-sdk/RoboMaster-SDK) 和 [ROS2](https://github.com/ros2)。
- 其他一些库包括：[Grounding-DINO-1.5](https://github.com/IDEA-Research/Grounding-DINO-1.5-API)、[YOLO-World](https://github.com/AILab-CVC/YOLO-World)。