from utils.log import logger
import json
from collections import defaultdict
from converter.converter import Converter


class ConverterAttackToJson(Converter):
    """转换器
    将Json格式的Attack数据集转换成便于
    提取器Extractor处理的格式
    """

    def __init__(self) -> None:
        """初始化函数，为空
        """
        self.objects_dict = defaultdict(list)

    def bind_relationship(self) -> None:
        for r in self.objects_dict["relationship"]:
            Source_Type = r.get("source_ref", "").split("--")[0]
            Target_Type = r.get("target_ref", "").split("--")[0]
            for o in self.objects_dict.get(Source_Type, []):
                if o.get("id", "") == r.get("source_ref", ""):
                    name = f"r_{Target_Type}"
                    if name not in o:
                        o[name] = []
                    o[name].append(r)
                    break
        pass

    def convert(self, file_path: str) -> json:
        """加载数据集文件，并转换成提取器所需的JSON格式

        Args:
            file_path (str): 数据集文件路径

        Returns:
            json: 提取器所需的JSON格式
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data_file = json.loads(f.read())

        # attack-pattern: 攻击模式，在ATT&CK中作为攻击技术Technique
        # course-of-action: 缓解措施
        # identity: 只有一个对象
        # intrusion-set: 事件，入侵集
        # malware: 统一为软件，software
        # tool: 统一为软件，software
        # x-mitre-tactic: 攻击战术
        # x-mitre-matrix: 只有一个对象
        # x-mitre-data-source: DataSource
        # x-mitre-data-component: DataComponent
        # x-mitre-collection: 总的介绍？只有一个对象，暂时忽略，里面有modified时间，可以通过该时间来判断是否有更新
        # marking-definition: 下定义？只有一个对象，暂时忽略
        # relationship:
        no_id_list = ["x-mitre-collection", "relationship",
                      "x-mitre-data-component", "x-mitre-data-source", "identity", "marking-definition"]
        for object in data_file["objects"]:
            #  判断是否废弃
            if object.get("revoked", False) or object.get("x_mitre_deprecated", False):
                continue
            # object["create_by"] = get_create_by(object)
            if object["type"] not in no_id_list:
                object["ID"] = get_ID(object)
            self.objects_dict[object["type"]].append(object)
        self.bind_relationship()
        return self.objects_dict


def get_create_by(object: dict) -> str:
    """从json对象中提取created_by_ref属性

    Args:
        object (dict): [description]
    """
    # 当前创建者基本都是MITRE，为以后修改留下位置
    if object.get("created_by_ref", "") == "identity--c78cb6e5-0c4b-4611-8297-d1b8b55e40b5":
        return "The MITRE Corporation"
    else:
        # 需要修改来合并不同的实体
        logger.info("出现created_by不一致的，待完善")
        return "Unknown"


def get_ID(object: dict) -> str:
    """从json对象中提取ID属性
    因为ID没有直接出现在属性中，而是出现在external_references中，所以特殊

    Args:
        object (dict): [description]
    """
    # 因为ID没有直接出现在属性中，而是出现在external_references中，所以特殊
    try:
        return [x for x in object.get(
            "external_references") if "external_id" in x][0]["external_id"]
    except:
        logger.info("找不到ID")
        logger.debug(object)
        return "Unknown"
