
import json
from pathlib import Path
from typing import Tuple

from converter.converter import Converter
from converter.converter_attack import ConverterAttackToJson
from converter.converter_capec import ConverterCapecToJson
from converter.converter_cve import ConverterCveToJson
from converter.converter_cwe import ConverterCweToJson
from converter.converter_d3fend import ConverterD3fendToJson
from converter.converter_engage import ConverterEngageToJson
from converter.converter_car import ConverterCarToJson
from utils.extractor import Extractor
from utils.log import logger
from utils.neo4j_module import Neo4j
from utils.timer import timer


def load_json(file_path: str) -> json:
    """加载json文件

    Args:
        file_path (str): json文件路径

    Returns:
        json: _description_
    """
    if file_path == "":
        logger.info("未设置文件加载")
        data = {}
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
    return data


@timer
def store_dataset(entities: list, relationships: list) -> bool:
    """将关系和实体存入数据库

    Args:
        entities (list): 实体的列表
        relationships (list): 关系的列表

    Returns:
        bool: 是否执行成功
    """
    # 本地使用
    neo = Neo4j(
        'bolt://localhost:7687/', "neo4j", "bike2000")

    # # 计算机楼115使用
    # # http://202.197.66.170:7474/browser/
    # neo = Neo4j(
    #     'bolt://202.197.66.170:7687/', "neo4j", "1kcsy2C7Vrn9JHuh")

    # http://192.168.146.150:7474/browser/
    # AttackEntity = Neo4j(
    #     'bolt://192.168.146.150:7687/', "neo4j", "1kcsy2C7Vrn9JHuh")

    # 创建本体
    neo.create_entity(entities)
    # 创建关系
    neo.create_relationship(relationships)
    # # 快速版，但貌似会出问题，导致neo4j出现问题
    # # 同一个事务执行多少条命令
    # fast_num = 30
    # # 快速创建本体
    # neo.create_entity_fast(entities, fast_num)
    # # 快速创建关系
    # neo.create_relationship_fast(relationships, fast_num)
    neo.close()
    return True


@timer
def extra_data(data_path: str, entity_conf_path: str, converter: Converter) -> Tuple[list, list]:
    """_summary_

    Args:
        data_path (str): 数据集文件的路径
        entity_conf_path (str): 实体关系文件的路径
        converter (Converter): 转换器

    Returns:
        Tuple[list,list]: _description_
    """
    # 使用转换器的convert函数将数据集转换为对应的Json格式
    data_set = converter.convert(data_path)
    # 加载配置文件
    entity_conf = load_json(entity_conf_path)
    # 按照配置文件从数据集中提取关系和实体
    extractor = Extractor()
    entities, relationships = extractor.extract(
        data_set, entity_conf)
    return entities, relationships


if __name__ == "__main__":
    # 初始化关系和实体的列表，读取了全部的关系和实体后，再将关系和实体存入数据库
    entities_all = []
    relationships_all = []
    # # 每个网站各写一个
    # ATT&CK数据集文件的路径
    data_path = Path("data/enterprise-attack-10.1.json")    # 需要修改为各自数据集文件的路径
    # 实体配置文件的路径
    # 需要修改为各自实体配置文件的路径
    # "conf/entity_conf_all.json"
    entity_conf_path = Path(f"conf/entity_conf_attack.json")
    # 对应的转换器
    converter = ConverterAttackToJson()              # 需要修改为各自的转换器类型
    entities, relationships = extra_data(
        data_path, entity_conf_path, converter)
    entities_all += entities
    relationships_all += relationships

    # Capec数据集文件的路径
    data_path = Path("data/capec.csv")  # 需要修改为各自数据集文件的路径
    # 实体配置文件的路径
    entity_conf_path = Path("conf/entity_conf_capec.json")  # 需要修改为各自实体配置文件的路径
    # 对应的转换器
    converter = ConverterCapecToJson()  # 需要修改为各自的转换器类型
    entities, relationships = extra_data(
        data_path, entity_conf_path, converter)
    entities_all += entities
    relationships_all += relationships

    # Cwe数据集文件的路径
    data_path = Path("data/cwe.csv")  # 需要修改为各自数据集文件的路径
    # 实体配置文件的路径
    entity_conf_path = Path("conf/entity_conf_cwe.json")  # 需要修改为各自实体配置文件的路径
    # 对应的转换器
    converter = ConverterCweToJson()  # 需要修改为各自的转换器类型
    entities, relationships = extra_data(
        data_path, entity_conf_path, converter)
    entities_all += entities
    relationships_all += relationships

    # Cve数据集文件的路径
    data_path = Path("data/cve-mini.csv")  # 需要修改为各自数据集文件的路径
    # 实体配置文件的路径
    entity_conf_path = Path("conf/entity_conf_cve.json")  # 需要修改为各自实体配置文件的路径
    # 对应的转换器
    converter = ConverterCveToJson()  # 需要修改为各自的转换器类型
    entities, relationships = extra_data(
        data_path, entity_conf_path, converter)
    entities_all += entities
    relationships_all += relationships

    # Engage数据集文件的路径
    data_path = Path("data/engage")  # 需要修改为各自数据集文件的路径
    # 实体配置文件的路径
    entity_conf_path = Path("conf/entity_conf_engage.json")  # 需要修改为各自实体配置文件的路径
    # 对应的转换器
    converter = ConverterEngageToJson()  # 需要修改为各自的转换器类型
    entities, relationships = extra_data(
        data_path, entity_conf_path, converter)
    entities_all += entities
    relationships_all += relationships

    # D3fend数据集文件的路径
    data_path = Path("data/d3fend.json")  # 需要修改为各自数据集文件的路径
    # 实体配置文件的路径
    entity_conf_path = Path("conf/entity_conf_d3fend.json")  # 需要修改为各自实体配置文件的路径
    # 对应的转换器
    converter = ConverterD3fendToJson()  # 需要修改为各自的转换器类型
    entities, relationships = extra_data(
        data_path, entity_conf_path, converter)
    entities_all += entities
    relationships_all += relationships

    # car数据集文件的路径
    data_path = Path("data/car")  # 需要修改为各自数据集文件的路径
    # 实体配置文件的路径
    entity_conf_path = Path("conf/entity_conf_car.json")  # 需要修改为各自实体配置文件的路径
    # 对应的转换器
    converter = ConverterCarToJson()  # 需要修改为各自的转换器类型
    entities, relationships = extra_data(
        data_path, entity_conf_path, converter)
    entities_all += entities
    relationships_all += relationships

    # 将关系和实体存入数据库
    store_dataset(entities_all, relationships_all)
