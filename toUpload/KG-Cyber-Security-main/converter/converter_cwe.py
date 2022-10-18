import json
import pandas as pd
from converter.converter import Converter


class ConverterCweToJson(Converter):
    """转换器
    将CWE格式的CWE数据集转换成便于
    提取器Extractor处理的格式
    """

    def __init__(self) -> None:
        """初始化函数，为空
        """
        pass

    def preprocess(self, df_capec):
        # 用""填充空值
        df_capec = df_capec.fillna(value='')
        # 将字符串拆分成列表
        for key in df_capec:
            df_capec[key] = df_capec[key].apply(split_list)
        return df_capec

    def split_property(self, objects: list) -> list:
        for object in objects:
            # # 原格式例子：['ChildOf:CAPEC-122', 'CanPrecede:CAPEC-17']
            # # 将其作为属性,用于关系链接
            object["Common Consequences"] = self.split_consequences(
                object.get("Common Consequences", []))
            for name in ["Related Weaknesses", "Weakness Ordinalities",
                         "Alternate Terms", "Modes Of Introduction", "Common Consequences",
                         "Detection Methods", "Potential Mitigations", "Observed Examples",
                         "Taxonomy Mappings", "Notes"]:
                object[name] = self.split_colon(
                    object.get(name, []))
        pass

    def split_consequences(self, object_list: list) -> list:
        # ":"同时作为字段分隔符和段落
        # 原格式 ["TAXONOMY NAME:ATTACK:ENTRY ID:1574.010:ENTRY NAME:Hijack Execution Flow: ServicesFile Permissions Weakness::"]
        # 修改为 [{"TAXONOMY NAME:": "ATTACK","ENTRY ID": "1574.010","ENTRY NAME": "Hijack Execution Flow: ServicesFile Permissions Weakness"}]
        o_list = []
        for line in object_list:
            position = line.find("IMPACT:")
            a_str = ":" + line[position:]
            for part in line[:position].split(":SCOPE"):
                o_list.append(part+a_str)
        return o_list

    def split_colon(self, object_list: list) -> list:
        # ":"同时作为字段分隔符和段落
        # 原格式 ["TAXONOMY NAME:ATTACK:ENTRY ID:1574.010:ENTRY NAME:Hijack Execution Flow: ServicesFile Permissions Weakness::"]
        # 修改为 [{"TAXONOMY NAME:": "ATTACK","ENTRY ID": "1574.010","ENTRY NAME": "Hijack Execution Flow: ServicesFile Permissions Weakness"}]
        o_list = []
        for line in object_list:
            t = line.count(":")
            if t == 0:
                o_list.append(line)
                continue
            # t % 2说明ENTRY NAME包含':'
            l = line.split(':', t-1) if t % 2 == 0 else line.split(':')
            o = {}
            for i in range(0, len(l), 2):
                o[l[i]] = l[i+1]
            o_list.append(o)
        return o_list

    def convert(self, file_path: str) -> json:
        """加载数据集文件，并转换成提取器所需的JSON格式

        Args:
            file_path (str): 数据集文件路径

        Returns:
            json: 提取器所需的JSON格式
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            dataf = pd.read_csv(f, index_col=False)

        objects_dict = {}
        objects_dict['cwe'] = self.preprocess(dataf).to_dict('records')
        self.split_property(objects_dict['cwe'])

        return objects_dict


def split_list(s: any) -> list or str:
    """按照capec文件csv格式的特点
    将开头是::的字段拆成列表

    Args:
        s (str): _description_

    Returns:
        list: _description_
        str: _description_
    """
    # 开头或结尾是::代表是列表
    if type(s) == str and ("::" == s[:2] or "::" == s[-2:]):
        return [x for x in s.strip('::').split('::') if x != '']
    else:
        return s
