<div align="center">
    <img src="resources\robomatrix-logo3.png" alt="logo" width="70%">
</div>

<div align="center">

[English](README.md) | 简体中文

</div>

# RoboMatrix: A Skill-centric Hierarchical Framework for Scalable Robot Task Planning and Execution in Open-World

### 📝[论文]() | 🌍[项目主页](https://robo-matrix.github.io/) | 🛢️[数据](https://huggingface.co/datasets/WayneMao/RoboMatrix)

![eight_skills](resources/eight_skills.gif)

<!-- ## 📰 新闻 -->

## 发布
- [2024/12/04] 🤗 发布RoboMatrix有监督微调数据集，该SFT数据集包含1,500条高质量人类标注的演示视频。 [[数据](https://huggingface.co/datasets/WayneMao/RoboMatrix)]

## Demo
### 动态对抗交互
<!-- <video src="https://robo-matrix.github.io/static/videos/crossing_obstacles_with_disturbance.mp4" controls="controls" style="max-width: 100%; height: auto;">
</video> -->
<!-- https://private-user-images.githubusercontent.com/35285052/392064253-ff1d7e2a-8650-430d-a60e-15bffcc237e2.mp4 -->
https://private-user-images.githubusercontent.com/35285052/392642975-b78e28aa-45c2-4bb0-9e70-b6a08c678f85.mp4

## 🛠️ 安装
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
- [x] 🤗 发布有监督微调数据集
- [ ] 优化VLA ROS通信
- [ ] 开源VLA Skill model代码
- [ ] 开放VLA Skill Model权重
- [ ] 开源Shooting代码

## Citation

If you find our work helpful, please cite us:

```bibtex
@article{mao2024robomatrix,
  title={Robomatrix: A skill-centric hierarchical framework for scalable robot task planning and execution in open-world},
  author={Mao, Weixin and Zhong, Weiheng and Jiang, Zhou and Fang, Dong and Zhang, Zhongyue and Lan, Zihan and Li, Haosheng and Jia, Fan and Wang, Tiancai and Fan, Haoqiang and others},
  journal={arXiv preprint arXiv:2412.00171},
  year={2024}
}
```

## 招聘
具身智能-具身大模型算法研究实习生
职位描述
1. 参与多模态理解与生成大模型、VLA大模型所需的数据清洗和自动标注系统开发，确保各类型/模态数据的质量与多样性；
2. 探索高效的数据增强和数据合成方法，例如图像/视频编辑；
3. 对机器人平台实现算法的部署和调试，提高机器人策略效率；
4. 对前沿具身算法进行研究探索，包括不限于VLA、RDT、Pi0等；
5. 我们提供有力的研究指导，进行论文发表；
职位要求
1、实习时间至少6个月，每周保证4天以上实习
2、硕士及以上学历在读，计算机、自动化等相关专业优先；
3、具备较强的软件工程能力，熟练使用Python、pytorch，熟悉Linux操作系统；
4、熟悉并行化编程，熟悉三维坐标变换、计算机视觉基础知识，了解机器人运动学；
5、有较好的英文科技文献阅读及算法复现的能力；
6、有实际的机器人开发经验优先，有大规模数据生成与处理经验优先；

工作地点：北京·中关村，逐际动力北京实验室  
申请方式：请将你的简历以及相关项目/研究的介绍发送至 waynemao@limxdynamics.com ，简历格式：实习_姓名_学校_方向.pdf  
PS. 同时也招收**物理仿真实习生，视频生成/世界模型实习生，运动控制实习生**， 还有少量全职HC。  
PPS. 请简历优先投递邮箱，走内推通道  
## 致谢
- 视觉-语言-动作 (VLA) 技能模型的实现基于 [LLaVA](https://github.com/haotian-liu/LLaVA/)。  
- RoboMatrix-ROS 基于 [RoboMaster-SDK](https://github.com/dji-sdk/RoboMaster-SDK) 和 [ROS2](https://github.com/ros2)。
- 其他一些库包括：[Grounding-DINO-1.5](https://github.com/IDEA-Research/Grounding-DINO-1.5-API)、[YOLO-World](https://github.com/AILab-CVC/YOLO-World)。


---
## 微信群
<img src="resources/WeChat/WechatIMG2.jpg" alt="weichat" width=200><img src="resources/WeChat/WechatIMG3.jpg" alt="weichat" width=200>
