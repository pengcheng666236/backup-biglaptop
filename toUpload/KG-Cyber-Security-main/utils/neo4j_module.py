from neo4j import GraphDatabase
from utils.log import logger
from tqdm import tqdm
from utils.nentity import Entity, Rentity
from itertools import zip_longest


class Neo4j:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_entity(self, entity: list or Entity):
        """调用函数，创建各种实体

        Args:
            entity (dict): [description]

        Returns:
            [type]: [description]
        """
        if type(entity) == list:
            for e in tqdm(entity):
                result = self.create_entity(e)
        else:
            with self.driver.session() as session:
                result = session.write_transaction(
                    self._create_entity, entity)
                # logger.debug(result)
            return result

    @staticmethod
    def _create_entity(tx, entity: Entity):
        """从json对象中创建实体及从属性中创建实体

        Args:
            tx ([type]): [description]
            entity (dict): [description]

        Returns:
            [type]: [description]
        """
        # 判断是否已存在
        # 例子
        # MATCH (object:Reference)
        # WHERE object.Url="https://www.bleepingcomputer.com/news/microsoft/microsoft-disables-dde-feature-in-word-to-prevent-further-malware-attacks/"
        # return object
        query = entity.neo4j_check_exist()
        check = execute_cql(tx, query)
        if check != False and entity.check_update(check[0]):
            query = entity.neo4j_update()
            # 用于debug使用
            # result = tx.run(query)
            result = execute_cql(tx, query)
            return result
        # 通过拼接字符串，设置攻击技术的属性
        # 例子
        # MERGE (object:AttackTechnique
        #     {
        #         Name  : "/etc/passwd and /etc/shadow",
        #         ID  : "T1003.008",
        #         Subtechnique  : "True",
        #         Version  : "1.0",
        #         Created_by  : "2020-02-11T18:46:56.263Z",
        #         Last_Modified  : "2021-04-29T14:49:39.188Z",
        #         Description  : "Adversaries may attempt to dump the contents ... ",
        #         Detection  : "The AuditD monitoring ... and arguments of such programs."
        #     })
        query = entity.neo4j_create()
        result = execute_cql(tx, query)
        return result

    def create_relationship(self, entity: list or Rentity):
        """调用函数，创建联系

        Args:
            entity (dict): [description]

        Returns:
            [type]: [description]
        """
        if type(entity) == list:
            for e in tqdm(entity):
                result = self.create_relationship(e)
        else:
            with self.driver.session() as session:
                result = session.write_transaction(
                    self._create_relationship, entity)
                # logger.debug(result)
            return result

    @staticmethod
    def _create_relationship(tx, entity: Rentity):
        """从json对象中创建实体及从属性中创建实体

        Args:
            tx ([type]): [description]
            entity (dict): [description]

        Returns:
            [type]: [description]
        """
        # 创建关系
        # 例子
        # MATCH (object:Technique),(subject:Group)
        # WHERE object.stix_id = "attack-pattern--f232fa7a-025c-4d43-abc7-318e81a73d65" and subject.stix_id = "intrusion-set--bef4c620-0787-42a8-a96d-b7eb6e85917c"
        # MERGE (object) - [r:used
        #  {
        #   Created_by  : "The MITRE Corporation",
        #   Version  : "1.0",
        #   Last_Modified  : "2021-07-26T17:53:02.254Z",
        #   Created  : "2021-07-26T17:53:02.254Z",
        #   Domain  : "['enterprise-attack']",
        #   Reference  : "[{'url': 'https://media.d ... gn July 2021)"
        #  }
        # ] -> (subject)
        query = entity.neo4j_create()
        # 用于debug使用
        result = tx.run(query)
        # result = execute_cql(tx, query)
        return result

    def create_entity_fast(self, entity: list, n: int):
        """调用函数，快速创建各种实体
        在一个事务中创建n个实体

        Args:
            entity (list): _description_
            n (int): 同一个事务中创建n个实体

        Returns:
            _type_: _description_
        """
        for e in tqdm([entity[i:i + n] for i in range(0, len(entity), n)]):
            with self.driver.session() as session:
                result = session.write_transaction(
                    self._create_entity_fast, e)
        return result

    @staticmethod
    def _create_entity_fast(tx, entity: list):
        for e in entity:
            query = e.neo4j_check_exist()
            if execute_cql(tx, query):
                continue
            query = e.neo4j_create()
            result = execute_cql(tx, query)
        return True

    def create_relationship_fast(self, entity: list, n: int):
        """调用函数，快速创建联系
        在一个事务中创建n个联系

        Args:
            entity (list): [description]
            n (int): 同一个事务中创建n个关系

        Returns:
            [type]: [description]
        """
        for e in tqdm([entity[i:i + n] for i in range(0, len(entity), n)]):
            with self.driver.session() as session:
                result = session.write_transaction(
                    self._create_relationship_fast, e)
        return result

    @staticmethod
    def _create_relationship_fast(tx, entity: Rentity):
        for e in entity:
            query = e.neo4j_create()
            result = execute_cql(tx, query)
            # 用于debug使用
            # result = tx.run(query)
        return result


def execute_cql(tx, query: str) -> bool:
    """执行cql语句

    Args:
        tx (_type_): _description_
        query (str): cql语句

    Returns:
        bool: 是否执行成功
    """
    logger.debug(query)
    result = tx.run(query)
    # out = result.single()
    out = result.value()
    if out:
        return out
    else:
        return False
