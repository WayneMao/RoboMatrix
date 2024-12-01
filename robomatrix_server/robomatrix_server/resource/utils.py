import os
import json
import yaml
import cv2
import re
from moviepy.editor import ImageSequenceClip
import shutil


HOME_PATH = os.path.expanduser("~")

RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RESET = '\033[0m'

def log_info(log):
    print(f"{GREEN}{log}{RESET}")

def log_warn(log):
    print(f"{YELLOW}{log}{RESET}")

def log_error(log):
    print(f"{RED}{log}{RESET}")

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_json(data, save_directory: str, file_name: str, log=True):
    if not os.path.exists(save_directory):
        os.mkdir(save_directory)
        if log: log_info(f"[Save Json] Create directory: {save_directory}")
    if not file_name.endswith('.json'):
        file_name += '.json'
        if log: log_warn(f"[Save Json] Change file name to: {file_name}")
    json_path = os.path.join(save_directory, file_name)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    if log: log_info(f"[Save Json] Save json file to: {json_path}")

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

def save_yaml(data, save_directory: str, file_name: str, log=True):
    if not os.path.exists(save_directory):
        os.mkdir(save_directory)
        if log: log_warn(f"[Save Yaml] Create directory: {save_directory}")
    if not file_name.endswith('.yaml'):
        file_name += '.yaml'
        if log: log_warn(f"[Save Yaml] Change file name to: {file_name}")
    yaml_path = os.path.join(save_directory, file_name)
    with open(yaml_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
    if log: log_info(f"[Save Yaml] Save yaml file to: {yaml_path}")

# 放弃
def save_video(images: list, fps: int, save_path: str):
    frame_count = len(images)
    if frame_count == 0:
        log_error(f"[Save video] Image list is empty")
        return None
    log_warn(f"[Save video] Saving video to {save_path}, don't close.")
    height, width, _ = images[0].shape
    out = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
    for t in range(frame_count):
        img = images[t]
        out.write(img)
    out.release()
    log_info(f"[Save video] Save video to {save_path}")

# 可用
def save_video_v2(images: list, fps: int, save_path: str):
    frame_count = len(images)
    if frame_count == 0:
        log_error(f"[Save video] Image list is empty")
        return None
    log_warn(f"[Save video] Saving video to {save_path}, don't close.")
    clip = ImageSequenceClip(images, fps=fps)
    clip.write_videofile(save_path, codec='libx264')
    log_info(f"[Save video] Save video to {save_path}")

def extract_last_number(string, suffix):
    '''
    用于sort的key
    '''
    # 使用正则表达式提取最后的数字
    match = re.search(r'_(\d+)' + re.escape(suffix) + r'$', string)
    if match: return int(match.group(1))
    return None

def find_ranges(nums):
    '''
    从有序正整数列表提取区间
    '''
    if not nums: return []

    ranges_str, ranges_list = [], []
    start = nums[0]

    for i in range(1, len(nums)):
        # 检查当前数字与前一个数字的差是否为 1
        if nums[i] != nums[i - 1] + 1:
            # 结束当前区间
            if start == nums[i - 1]:
                ranges_str.append(f"{start}")
                ranges_list.append([start])
            else:
                ranges_str.append(f"{start}~{nums[i - 1]}")
                ranges_list.append([start, nums[i - 1]])
            start = nums[i]

    # 添加最后一个区间
    if start == nums[-1]:
        ranges_str.append(f"{start}")
        ranges_list.append([start])
    else:
        ranges_str.append(f"{start}~{nums[-1]}")
        ranges_list.append([start, nums[-1]])

    return ranges_str, ranges_list

def compare_intervals(intervals_A, intervals_B):
    '''
    比较B区间是否被A区间包含
    '''
    def normalize_intervals(intervals):
        normalized = []
        for interval in intervals:
            if len(interval) == 1:  # 处理只有一个端点的情况
                normalized.append([interval[0], interval[0]])
            else:
                normalized.append(interval)
        return normalized
    
    # 先规范化 B 区间
    intervals_B = normalize_intervals(intervals_B)

    for interval_B in intervals_B:
        start_B, end_B = interval_B
        covered = False

        # 遍历 A 区间
        for start_A, end_A in intervals_A:
            # 检查 B 区间是否被 A 区间包含
            if start_A <= start_B and end_B <= end_A:
                covered = True
                break  # 找到一个包含的 A 区间，停止检查
        
        if not covered:
            return False  # 如果任何 B 区间不被 A 区间包含，返回 False
    
    return True  # 所有 B 区间均被 A 区间包含

def analyse_folder(folder_path, log=True):
    if not os.path.exists(folder_path):
        log_error(f"[Analyse Folder] Cannot find: {folder_path}")
        return None
    
    information = {}

    for file in os.listdir(folder_path):
        name, suffix = os.path.splitext(file) # 分割名称和后缀
        if suffix not in information: information[suffix] = {}
        match = re.match(r'^(.*)_(\d+)$', name) # 分割任务描述和数字
        if match:
            task_description = match.group(1)
            episode_index = match.group(2)
            if task_description not in information[suffix]: information[suffix][task_description] = []
            information[suffix][task_description].append(int(episode_index))
        else: log_warn(f"[Analyse Folder] Cannot match: {file}")
    
    for suffix in sorted(information.keys()):
        if log: log_info(f"[Analyse Folder] File type: {suffix}")
        group = information[suffix]
        for task_description in sorted(group.keys()):
            # log_info(f"Task description: {task_description}")
            if log: log_info(f"{task_description}")
            group[task_description].sort()
            ranges_str, ranges_list = find_ranges(group[task_description])
            # log_info(f"Episode index range: {''.join(ranges_str)}, count: {len(group[task_description])}")
            if log: log_info(f"Range: {' '.join(ranges_str)}, count: {len(group[task_description])}")
            group[task_description] = ranges_list
    
    return information

def compare_information(videos_information, annotations_information):
    if ".mp4" not in videos_information:
        log_error(f"[Compare] No MP4 in videos resource.")
        return False
    if ".json" not in annotations_information:
        log_error(f"[Compare] No JSON in annotations resource.")
        return False
    status = True
    for task_description in sorted(videos_information[".mp4"]):
        if task_description not in annotations_information[".json"]:
            log_error(f"[Compare] Task not in annotations: {task_description}")
        videos_index_ranges = videos_information[".mp4"][task_description]
        annotations_index_ranges = annotations_information[".json"][task_description]
        if videos_index_ranges == annotations_index_ranges:
            log_info(f"[Compare] OK: {task_description}")
        else:
            status = False
            log_error(f"[Compare] Wrong: {task_description}")
    return status

def check_dataset(videos_resource=os.path.join(HOME_PATH, "RoboMatrixDatasetsALL", "videos"),
                  annotations_resource=os.path.join(HOME_PATH, "RoboMatrixDatasetsALL", "annotations")):
    videos_info = analyse_folder(videos_resource)
    save_json(videos_info, os.path.join(HOME_PATH, "RoboMatrixDatasetsALL"), "videos_information.json")
    annos_info = analyse_folder(annotations_resource)
    save_json(annos_info, os.path.join(HOME_PATH, "RoboMatrixDatasetsALL"), "annotations_information.json")
    return compare_information(videos_info, annos_info)

def rename_dataset(videos_folder, annos_folder, *chosen_group):
    analyse_folder(videos_folder)
    analyse_folder(annos_folder)

    old_names, new_names = [], []
    for old_name, new_name in chosen_group:
        old_names.append(old_name)
        new_names.append(new_name)
        log_info(f"[Rename] Your change: {old_name} -> {new_name}")
    
    group = set()
    file_names = {}
    for file_name in os.listdir(videos_folder):
        name, suffix = os.path.splitext(file_name)
        if suffix == ".mp4":
            match = re.match(r'^(.*)_(\d+)$', name)
            if match:
                task = match.group(1)
                index = match.group(2)
                if task not in group:
                    file_names[task] = []
                group.add(task)
                file_names[task].append(int(index))
            else: log_warn(f"[Rename] {file_name} cannot match")
        else: log_warn(f"[Rename] Skip non-mp4 file: {file_name}")
    for key in file_names:
        try: file_names[key].sort()
        except:
            log_error(f"[Rename] Sort failed: {key}")
            if key in old_names: return
        range, _ = find_ranges(file_names[key])
        log_info(f"[Rename] {key} count: {len(file_names[key])} range: {' '.join(range)}")
    
    for s in old_names:
        if s not in group:
            log_error(f"[Rename] Not in group: {s}")
            return

    log_warn(f"[Rename] Press ENTER to continue")
    input()

    for i, s in enumerate(old_names):
        indexs = file_names[s]
        names = [f"{s}_{num}" for num in indexs]
        task_name = new_names[i]
        for j, name in enumerate(names):
            new_name = f'{task_name}_{j + 1}'
            new_json_name = f'{new_name}.json'
            new_video_name = f'{new_name}.mp4'

            # 对json处理
            old_json_name = f"{name}.json"
            old_json_path = os.path.join(annos_folder, old_json_name)
            data = load_json(old_json_path)
            for frame in data:
                frame["stream"] = new_video_name # 改stream
            save_json(data, annos_folder, new_json_name)
            log_info(f"[Rename] New annotation: {annos_folder} -> {new_json_name}")
            if old_json_name != new_json_name:
                os.remove(old_json_path)

            # 对video处理
            old_video_name = f"{name}.mp4"
            old_video_file = os.path.join(videos_folder, old_video_name)
            new_video_file = os.path.join(videos_folder, new_video_name)
            os.rename(old_video_file, new_video_file)
            log_info(f"[Rename] New video: {new_video_file}")

def create_dataset(dataset_folder,
                   *groups,
                   videos_resource=os.path.join(HOME_PATH, "RoboMatrixDatasetsALL", "videos"),
                   annotations_resource=os.path.join(HOME_PATH, "RoboMatrixDatasetsALL", "annotations")):
    '''
    *groups: (move_to_object, [[1, 10], [20], [30, 40]])
    '''
    # 检查是否已经存在
    if os.path.exists(dataset_folder):
        log_error(f"[Create Dataset] Already exist: {dataset_folder}")
        return
    
    # 检查原始数据集
    videos_info = analyse_folder(videos_resource)
    annos_info = analyse_folder(annotations_resource)
    if not compare_information(videos_info, annos_info):
        log_error(f"[Create Dataset] Dataset error")
        return
    
    # 检查任务描述和范围
    log_info(f"[Create Dataset] Your choice:")
    status = True
    for task_name, index_ranges in groups:
        log_info(f"Task: {task_name}")
        log_info(f"Range: {index_ranges}")

        if task_name not in videos_info[".mp4"] or task_name not in annos_info[".json"]:
            log_error(f"Invalid task description: {task_name}")
            status = False
            continue
        
        main_ranges = videos_info[".mp4"][task_name]
        if not compare_intervals(main_ranges, index_ranges):
            log_error(f"Invalid episode range: {index_ranges}")
            status = False
    if not status: return
        
    # 继续
    log_info(f"[Create Dataset] Press ENTER to continue")
    input()

    # 创建文件夹
    if not os.path.exists(dataset_folder):
        os.mkdir(dataset_folder)
        os.mkdir(os.path.join(dataset_folder, "videos"))
        os.mkdir(os.path.join(dataset_folder, "annotations"))
        log_info(f"[Create Dataset] Create dataset: {dataset_folder}")
    
    # 复制文件
    for task_name, index_ranges in groups:
        log_info(f"[Create Dataset] Copy: {task_name}")
        log_info(f"Range: {index_ranges}")
        indexs = []
        for r in index_ranges:
            if len(r) == 1: indexs.append(r[0])
            elif len(r) == 2:
                start, end = r
                for i in range(start, end+1): indexs.append(i)
        log_info(f"Count: {len(indexs)}")
        log_info(f"Press ENTER to continue")
        input()
        for index in indexs:
            name = f"{task_name}_{index}"
            resource_video = os.path.join(videos_resource, f"{name}.mp4")
            resource_anno = os.path.join(annotations_resource, f"{name}.json")
            destination_video = os.path.join(dataset_folder, "videos", f"{name}.mp4")
            destination_anno = os.path.join(dataset_folder, "annotations", f"{name}.json")
            shutil.copy(resource_video, destination_video)
            shutil.copy(resource_anno, destination_anno)
            log_info(f"OK: {name}")
        
