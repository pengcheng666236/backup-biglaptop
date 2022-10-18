import yaml
import os
import json
from collections import defaultdict
from converter.converter import Converter


class ConverterCarToJson(Converter):
    """转换器
    将Json格式的Attack数据集转换成便于
    提取器Extractor处理的格式
    """

    def __init__(self) -> None:
        """初始化函数，为空
        """
        pass

    def preprocess(self) -> None:
        new_field = defaultdict(list)
        new_action = defaultdict(list)
        # 修改data_model_references使其符合DataModel的label属性
        for object in self.objects_dict["analytics"]:
            object["data_model_references_actions"] = []
            object["data_model_references_fields"] = []
            for o in object.get("data_model_references", []):
                if o.count("/") == 2:
                    model, action, field = o.split("/", 2)
                    label = f'{model}/{field}'.lower()
                    object["data_model_references_fields"].append(label)
                    new_d = {"label": label, "name": field}
                    if new_d not in new_field[model]:
                        new_field[model].append(new_d)
                elif o.count("/") == 1:
                    model, action = o.split("/", 1)
                label = f'{model}/{action}'.lower()
                object["data_model_references_actions"].append(label)
                new_d = {"label": label, "name": field}
                if new_d not in new_action[model]:
                    new_action[model].append(new_d)
        # 防止不同DataModel出现冲突，给予一个label的属性作为唯一标识符
        for object in self.objects_dict["data_model"]:
            actions_list = []
            fields_list = []
            name = object["name"].lower()
            for o in object["actions"]:
                label = f'{name}/{o["name"]}'.lower()
                o["label"] = label
                actions_list.append(label)
            for o in object["fields"]:
                label = f'{name}/{o["name"]}'.lower()
                o["label"] = label
                fields_list.append(label)
            for o in new_action[name]:
                if o["label"] not in actions_list:
                    new_o = {"label": o["label"], "name": o["name"]}
                    object["actions"].append(new_o)
            for o in new_field[name]:
                if o["label"] not in fields_list:
                    new_o = {"label": o["label"], "name": o["name"]}
                    object["fields"].append(new_o)
        # sensors处理
        for object in self.objects_dict["sensors"]:
            object["other_coverage_id"] = []
            for s in object["other_coverage"]:
                if ": " in s:
                    id, name = s.split(": ", 1)
                    object["other_coverage_id"].append(id)
            for o in object.get("mappings", {}):
                object["mappings_new"] = []
                for field in o.get("fields", []):
                    object["mappings_new"].append({
                        "name": f'{o["object"]}/{field}'.lower(),
                        "action": o["action"],
                        "notes": o["notes"]
                    })
        pass

    def convert(self, file_path: str) -> json:
        """加载数据集文件，并转换成提取器所需的JSON格式

        Args:
            file_path (str): 数据集文件路径

        Returns:
            json: 提取器所需的JSON格式
        """
        self.objects_dict = defaultdict(list)
        folders = os.listdir(file_path)  # 获取目录下的文件名
        for folder in folders:
            files = os.listdir(file_path / folder)
            for file_name in files:
                with open(file_path / folder / file_name, 'r', encoding='utf-8') as f:
                    # 先将yaml转换为json格式
                    generate_json = yaml.load(f, Loader=yaml.FullLoader)
                    self.objects_dict[folder].append(generate_json)
        self.preprocess()
        return self.objects_dict
