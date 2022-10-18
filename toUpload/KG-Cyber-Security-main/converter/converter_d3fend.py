import os
import json
from collections import defaultdict
from converter.converter import Converter
from pathlib import Path


class ConverterD3fendToJson(Converter):
    """转换器
    将Json格式的D3fend数据集转换成便于
    提取器Extractor处理的格式

    文件来源于https://github.com/mitre/d3fend
    https://github.com/mitre/d3fend/blob/gh-pages/ontologies/d3fend.json
    的d3fend.json
    """

    def __init__(self) -> None:
        """初始化函数，为空
        """
        self.special_type = []
        pass

    def preprocess(self, objects: list):
        """因为数据文件的格式太混乱，里面列表，字符串混杂，所以先统一

        Args:
            objects (_type_): _description_
        """
        # 手动添加的属性
        property_type = {"d3f:may-create": list,
                         "d3f:adds": list, "d3f:creates": list}
        # 先扫描一次，但凡出现过列表的类型，就都变成列表
        for object in objects:
            for key in object:
                if key not in property_type:
                    property_type[key] = type(object[key])
                else:
                    if type(object[key]) == list:
                        property_type[key] = list
                        continue
        # 转换成列表，统一操作
        for object in objects:
            for key in object:
                if property_type[key] == list and type(object[key]) != list:
                    object[key] = [object[key]]
        return objects

    def classify(self, objects):
        objects_dict = defaultdict(list)
        object_list = []
        # 'owl:Class', 'owl:NamedIndividual' 这两个类别没有用
        useless_type = ['owl:Class', 'owl:NamedIndividual']
        # 第一次循环先找到战术，并过滤没用的对象
        for object in objects:
            object_type = object.get("@type", "")
            # 去除没有用的类别
            object["type"] = [o for o in object_type if o not in useless_type]
            # 'owl:Restriction' 感觉没有用，过滤
            if "owl:Restriction" in object["type"]:
                continue
            # 认为type里面包含"d3f:DefensiveTactic"则是防御的战术
            # 但是有个scan也符合，通过scan没有d3f:definition排除
            elif "d3f:DefensiveTactic" in object["type"]:
                if object.get("d3f:definition", "") != "":
                    object["type"] = "DefensiveTarget"
                    objects_dict["DefensiveTarget"].append(object)
            # 认为type里面包含"d3f:ATTACKMitigation"则是缓解措施
            elif "d3f:ATTACKMitigation" in object["type"]:
                object["type"] = "ATTACKMitigation"
                objects_dict["ATTACKMitigation"].append(object)
            # 关系
            elif len(list(filter(lambda x: "ObjectProperty" in x, object["type"]))) != 0:
                object["type"] = "ObjectProperty"
                objects_dict["ObjectProperty"].append(object)
                self.special_type.append(object["@id"])
            # 不知道是啥，感觉像是属性相关的
            elif len(list(filter(lambda x: "Property" in x, object["type"]))) != 0:
                object["type"] = "Property"
                objects_dict["Property"].append(object)
            # 参考文献
            elif len(list(filter(lambda x: "Reference" in x, object["type"]))) != 0 or \
                    "d3f:ExternalKnowledgeBase" in object["type"]:
                object["type"] = "Reference"
                objects_dict["Reference"].append(object)
            # 如果包含"d3f:attack-id"，则是攻击技术
            elif object.get("d3f:attack-id", "") != "":
                object["type"] = "Technique"
                # object["ID"] = object["@id"].split("d3f:")[1]
                objects_dict["Technique"].append(object)
            else:
                object_list.append(object)
        # 第二次循环，从中搜索技术
        # 如果@type中包含战术的id，则是防御的技术
        technique_id = []
        second_list = []
        for object in object_list:
            if "d3f:DefensiveTechnique" in object["type"]:
                object["type"] = "DefensiveTactic"
                objects_dict["DefensiveTactic"].append(object)
                technique_id.append(object["@id"])
            else:
                second_list.append(object)
        # 第三次循环，从中搜索防御的基础技术
        # 如果@type中包含基础技术的id，则是防御的基础技术
        third_list = []
        t_id = []
        technique_id = set(technique_id)
        for object in second_list:
            if set(object["type"]) & technique_id != set():
                object["type"] = "DefensiveTechnique"
                objects_dict["DefensiveTechnique"].append(object)
                t_id.append(object["@id"])
            else:
                third_list.append(object)
        # 第四次循环，从中搜索防御的基础技术的子技术
        # 如果@type中包含基础技术的id，则是防御的基础技术
        last_list = []
        t_id = set(t_id)
        for object in third_list:
            if set(object["type"]) & t_id != set():
                object["type"] = "DefensiveTechnique"
                objects_dict["DefensiveTechnique"].append(object)
            else:
                last_list.append(object)
        # 最后一次循环，将type只有一种的单独分类
        test = []
        for object in last_list:
            if object.get("rdfs:comment", "") != "":
                object["type"] = "Artifact"
                objects_dict["Artifact"].append(object)
            elif len(object["type"]) == 1:
                object["type"] = object["type"][0]
                objects_dict[object["type"]].append(object)
            else:
                test.append(object)
        return objects_dict

    def add_type(self):
        relationship = ["rdfs:subClassOf",
                        "d3f:kb-reference"] + self.special_type
        # 转换成列表，统一操作
        for key in self.objects_dict:
            for object in self.objects_dict[key]:
                for key in self.special_type:
                    if key in object and type(object[key]) != list:
                        object[key] = [object[key]]
        for key in self.objects_dict:
            for object in self.objects_dict[key]:
                for k in relationship:
                    # for k in object:
                    if k in object and len(object[k]) > 0 and type(object[k][0]) == dict:
                        new_list = []
                        for o in object[k]:
                            t_id = o.get("@id", "")
                            if t_id != "":
                                t_type = self.get_type(t_id)
                                if t_type != '':
                                    o["type"] = t_type
                                    o["relationship"] = k.replace(
                                        "d3f:", "").replace("rdfs:", "")
                                    new_list.append(o)
                        object[k] = new_list
                        for o in object[k]:
                            r_name = "r_" + o["type"]
                            if r_name not in object:
                                object[r_name] = []
                            object[r_name].append(o)
        pass

    def get_type(self, target_id):
        for key in self.objects_dict:
            for object in self.objects_dict[key]:
                if object["@id"] == target_id:
                    return key
        return ""

    def convert(self, file_path: str) -> json:
        """加载数据集文件，并转换成提取器所需的JSON格式

        Args:
            file_path (str): 数据集文件路径

        Returns:
            json: 提取器所需的JSON格式
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data_file = json.loads(f.read())
        objects = data_file["@graph"]
        objects = self.preprocess(objects)
        self.objects_dict = self.classify(objects)
        self.add_type()
        return self.objects_dict
