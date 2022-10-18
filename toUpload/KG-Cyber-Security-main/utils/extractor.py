from collections import defaultdict
import json
from typing import List, Tuple
from utils.log import logger
from utils.nentity import Entity, Rentity
from itertools import repeat


class Extractor(object):
    """提取器，用于按照*配置文件*从
    *Json格式的数据*中提取实体对象和关系对象
    """

    def __init__(self) -> None:
        pass

    def extract(self, data_set: json, entity_conf: json) -> Tuple[list, list]:
        """按照配置文件从数据集中提取关系和实体

        Args:
            data_set (json): 所需JSON格式的数据集
            entity_conf (json): JSON格式的实体配置信息

        Returns:
            Tuple[list, list]: _description_
        """
        # 加载提取对象的配置文件
        entities = []
        relationships = []
        for conf_object in entity_conf:
            entity, relationship = extra_object_by_conf(
                data_set, conf_object)
            # 去重
            # for e in entity:
            #     if e not in entities:
            #         entities.append(e)
            # 不去重
            entities += entity
            relationships += relationship
        return entities, relationships


def load_relationship(object: dict, conf_object: dict) -> dict:
    """通过配置文件从stix中加载关系
    """
    r_type = conf_object["Relationship"]
    s_type = conf_object.get("Source_Type", "")
    t_type = conf_object.get("Target_Type", "")
    s_constraint = {}
    t_constraint = {}
    r_properties = {}
    for k, v in conf_object["Source_Constraint"].items():
        s_constraint[k] = end_escape(load_property(object, v))
    for k, v in conf_object["Target_Constraint"].items():
        t_constraint[k] = end_escape(load_property(object, v))
    # properties: 提取本体的属性作为属性
    # 键为本体的属性名
    # 值为文件的键或是需要调用的函数
    properties = conf_object.get("Properties", {})
    for property in properties:
        value = properties[property]
        r_properties[property] = end_escape(
            load_property(object, value))  # 使用str先转换成字符串再转义，防止字典出问题
    relationship = Rentity(
        r_type, s_type, s_constraint, t_type, t_constraint, r_properties)
    if conf_object.get("Reverse", False):
        relationship.reverse_relationship()
    return relationship


def extra_object_by_conf(objects_dict: dict, conf_object: dict) -> Tuple[list, list]:
    """通过配置文件从dict中提取本体

    Args:
        objects_dict (dict): [description]
        conf_object (dict): [description]
    """
    entities = []
    relationships = []
    # 本体来自哪些类别
    for type in conf_object["Json_type"]:
        for object in objects_dict[type]:
            # 初始化对象
            entity, relationship = load_object(object, conf_object)
            entities += entity
            relationships += relationship
    return entities, relationships


def load_object(object: dict, conf_object: dict) -> Tuple[list, list]:
    """实际加载本体数据的函数
    """
    entity_type = conf_object.get("Type")
    key = conf_object.get("Key")
    entity_property = {}
    # properties: 提取本体的属性作为属性
    # 键为本体的属性名
    # 值为文件的键或是需要调用的函数
    properties = conf_object.get("Properties", {})
    for property in properties:
        value = properties[property]
        entity_property[property] = end_escape(load_property(object, value))
    entity = Entity(entity_type, key, entity_property)
    entities = [entity]
    relationships = []
    # propertyEntity: 提取本体的属性作为新的本体
    propertyEntities = conf_object.get("PropertyEntity", [])
    for conf_entity in propertyEntities:
        property_entities, relationship = load_property_entity(
            object, conf_entity)
        # 构建属性实体和实体之间的联系
        relationships += create_relationship_entity_property(
            entity, relationship, property_entities, conf_entity)
        entities += property_entities
    return entities, relationships


def find_special_property(object: dict, property: str):
    # 特殊的属性
    # 开头是{}代表不是字符串，而是需要获取的参数，调用load_property获取
    # 开头不是{}，代表是纯粹的字符串，直接返回
    if len(property) > 2 and "{}" == property[:2]:
        return load_property(object, property[2:])
    else:
        return property


def create_relationship_entity_property(entity: dict, relationship: list or str, property_entities: list, conf: dict) -> List:
    """构建属性实体和实体之间的联系
    """
    relationships = []
    for property_entity, r_type in zip(property_entities, relationship):
        s_type = entity.type
        t_type = property_entity.type
        s_constraint = {}
        t_constraint = {}
        properties = {}
        for key in entity.key:
            s_constraint[key] = entity.properties[key]
        for key in property_entity.key:
            t_constraint[key] = property_entity.properties[key]
        relationship = Rentity(
            r_type, s_type, s_constraint, t_type, t_constraint, properties)
        if relationship.check_point_itself():
            continue
        if conf.get("Reverse", False):
            relationship.reverse_relationship()
        relationships.append(relationship)
    return relationships


def load_property(object: dict, value: any) -> any:
    """通过值中的字符串获取属性
    """
    # 如果是列表类型，说明有多个来源，使用递归的形式处理
    if type(value) == list:
        values = []
        for v in value:
            z = load_property(object, v)
            if z != "":
                values.append(z)
        return values
    # 如果值是字符串类型，那么应该是直接获取的属性or调用函数
    elif type(value) == str:
        # 调用函数
        # 例如 value = "get_ID(object)"，则值为调用函数get_ID(object)获取的值
        if "(object)" in value:
            return escape(save_eval(object, value))
        # 字符串中包含{}，则是对象的属性中的属性获取
        elif "{}" in value:
            values = value.split("{}")
            now_object = object.get(values[0], {})
            if now_object == {}:
                logger.info("找不到对应的属性")
                return {}
            return load_property_multilevel(now_object, values[1:])
        # 纯字符串直接获取的属性
        # 例如 value = "name"，则值为对象object的name属性
        else:
            try:
                return escape(object.get(value, ""))
            except AttributeError:
                logger.error("未发现对应属性，返回空")
                return ""
            except Exception as e:
                logger.debug("发现位置错误")
                raise
    else:
        logger.error("配置文件导入类型有问题")


def load_property_multilevel(object: dict, values: any):
    """从多个层级中获取属性，暂时只考虑2个层级
    """
    if type(object) == list and len(values) == 1:
        out = [load_property(o, values[0]) for o in object]
        return out
    elif type(object) == dict:
        now_object = object.get(values[0], {})
        return load_property_multilevel(now_object, values[1:])
    pass


def load_property_entity(object: dict, conf: dict):
    properties = {}
    for property in conf["Properties"]:
        value = load_property(
            object, conf["Properties"].get(property, ""))
        properties[property] = value if type(value) == list else [value]
    out = []
    key = conf["Key"][0]
    length = len(properties[key])
    new_properties = defaultdict(list)
    other_key = list(properties.keys())
    other_key.remove(key)
    for n in range(length):
        if type(properties[key][n]) == list:
            new_properties[key].extend(properties[key][n])
            for k in other_key:
                if type(properties[k][n]) == str:
                    new_properties[k].extend(
                        list(repeat(properties[k][n], len(properties[key][n]))))
                else:
                    new_properties[k].extend(properties[k][n])
        else:
            for k in properties.keys():
                new_properties[k].append(properties[k][n])
    properties = new_properties
    entity_type = find_special_property(object, conf.get("Type"))
    length = len(properties[key])
    entity_type = entity_type if type(
        entity_type) == list else list(repeat(entity_type, length))
    relationship = find_special_property(
        object, conf.get("Relationship"))
    relationship = relationship if type(
        relationship) == list else list(repeat(relationship, length))
    actual_relationship = []
    for n in range(length):
        entity_property = {}
        for property in properties:
            entity_property[property] = properties[property][n]
        actual_entity = Entity(entity_type[n], conf["Key"], entity_property)
        if not actual_entity.check_blank():
            out.append(actual_entity)
            actual_relationship.append(relationship[n])
    return out, actual_relationship


def save_eval(object: dict, function: str):
    """使用eval执行函数
    """
    out = ""
    if function == "get_ID(object)":
        out = eval("get_ID(object)")
    elif function == "get_create_by(object)":
        out = eval("get_create_by(object)")
    return out


def escape(s: any):
    """处理文本中的特殊字符：
    \转换为\\
    "转换为\"

    Args:
        s (any): [description]

    Returns:
        [type]: [description]
    """
    if type(s) == str:
        return str(s).replace("\\", "\\\\").replace('"', '\\"')
    elif type(s) == dict:
        for n in s:
            s[n] = escape(s[n])
    elif type(s) == list:
        for n in range(len(s)):
            s[n] = escape(s[n])
    return s


def end_escape(s: any):
    """不管啥类型都处理文本中的特殊字符：
    \转换为\\
    "转换为\"

    Args:
        s (any): [description]

    Returns:
        [type]: [description]
    """
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def extra_relationship_by_conf(objects_dict: dict, conf_object: dict) -> list:
    """通过配置文件从dict中提取关系

    Args:
        objects_dict (dict): [description]
        conf_object (dict): [description]
    """
    relationships = []
    # 关系来自哪些类别
    for type in conf_object["Json_type"]:
        for object in objects_dict[type]:
            # 判断是否废弃
            if object.get("revoked", False) or object.get("x_mitre_deprecated", False):
                continue
            # 判断是否符合Relationship_Type的类别
            # 为空则没有限制
            if conf_object.get("Relationship_Type", "") != '':
                if object.get("Relationship_Type", "") != conf_object.get("Relationship_Type", ""):
                    continue
            Source_Type = object.get("source_ref", "").split("--")[0]
            if Source_Type != conf_object.get("Source_Json_Type", ""):
                continue
            Target_Type = object.get("target_ref", "").split("--")[0]
            if Target_Type != conf_object.get("Target_Json_Type", ""):
                continue
            # 初始化对象
            relationship = load_relationship(object, conf_object)
            relationships.append(relationship)
    return relationships
