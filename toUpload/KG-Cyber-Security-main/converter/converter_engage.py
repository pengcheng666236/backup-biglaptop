import os
import json
from collections import defaultdict
from converter.converter import Converter
from pathlib import Path


class ConverterEngageToJson(Converter):
    """转换器
    将Json格式的Engage数据集转换成便于
    提取器Extractor处理的格式

    发现activity_details.json包含了activities.json的内容，甚至包含了approach_activity_mappings.json
    同理可得，需要读取的文件为：
    activity_details.json
    approach_details.json
    goal_details.json

    但是*_details.json文件是key：value的格式，而不是列表的格式，故将key作为属性转换成列表
    """

    def __init__(self) -> None:
        """初始化函数，为空
        """
        pass

    def preprocess_activity(self, objects_dict):
        for object in objects_dict["activity_details"]:
            object["exposed"] = []
            vuln_dict = {}
            for o in object["vulnerabilities"]:
                vuln_dict[o["id"]] = o["eav"]
            for key in object:
                if key[:3] == "EAV":
                    for o in object[key]:
                        o["key"] = key
                        o["eav"] = vuln_dict[key]
                        object["exposed"].append(o)
        return objects_dict

    def convert(self, file_path: str) -> json:
        """加载数据集文件，并转换成提取器所需的JSON格式

        Args:
            file_path (str): 数据集文件路径

        Returns:
            json: 提取器所需的JSON格式
        """
        files = os.listdir(file_path)  # 获取目录下的文件名
        objects_dict = defaultdict(list)
        for file_name in files:
            file = os.path.splitext(file_name)
            entity_name = file[0]
            with open(file_path / file_name, "r", encoding='utf-8') as f:
                data_file = json.load(f)
                objects_dict[entity_name] = []
                if type(data_file) == dict:
                    for key in data_file:
                        data_file[key]["id"] = key
                        objects_dict[entity_name].append(data_file[key])
                elif type(data_file) == list:
                    objects_dict[entity_name] += data_file
        objects_dict = self.preprocess_activity(objects_dict)
        return objects_dict
