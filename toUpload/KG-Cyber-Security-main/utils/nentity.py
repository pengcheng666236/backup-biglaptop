from pkg_resources import UnknownExtra


class Entity:
    """实体
    """

    def __init__(self, entity_type: str, key: list, properties: dict) -> None:
        """实体json例子：
        {
            "Type":"Technique",
            "Key":[
                "stix_id"
            ],
            "Properties":{
                "Created":"2020-02-11T18:46:56.263Z",
                "Created_by":"The MITRE Corporation",
                "Description":"Adversaries may attempt to dump the contents of <code>/etc/passwd</code> and <code>/etc/shadow</code> to enable offline password cracking. Most modern Linux operating systems use a combination of <code>/etc/passwd</code> and <code>/etc/shadow</code> to store user account information including password hashes in <code>/etc/shadow</code>. By default, <code>/etc/shadow</code> is only readable by the root user.(Citation: Linux Password and Shadow File Formats)\n\nThe Linux utility, unshadow, can be used to combine the two files in a format suited for password cracking utilities such as John the Ripper:(Citation: nixCraft - John the Ripper) <code># /usr/bin/unshadow /etc/passwd /etc/shadow > /tmp/crack.password.db</code>\n",
                "Detection":"The AuditD monitoring tool, which ships stock in many Linux distributions, can be used to watch for hostile processes attempting to access <code>/etc/passwd</code> and <code>/etc/shadow</code>, alerting on the pid, process name, and arguments of such programs.",
                "Domain":[
                    "enterprise-attack"
                ],
                "ID":"T1003.008",
                "Last_Modified":"2021-04-29T14:49:39.188Z",
                "Name":"/etc/passwd and /etc/shadow",
                "Platform":[
                    "Linux"
                ],
                "Subtechnique":true,
                "Version":"1.0",
                "stix_id":"attack-pattern--d0b4fcdb-d67d-4ed2-99ce-788b12f8c0f4"
            }
        }

        Args:
            entity_type (str): 节点的类型
            key (list): 节点的关键属性，用于判断实体是否已经存在
            properties (dict): 节点的属性
        """
        self.type = entity_type
        self.key = key
        self.properties = properties

    def check_blank(self) -> bool:
        """用于判断该节点的关键属性是否为空
        为空则返回True
        不为空返回False

        Returns:
            bool: _description_
        """
        flag_exit = True
        for key in self.key:
            if self.properties[key] != '' and self.properties[key] != {}:  # 关键字均为空则跳过
                flag_exit = False
        return flag_exit

    def neo4j_where(self) -> str:
        """使用节点的关键属性生成用于neo4数据库约束条件的cql语句
        """
        where_str = ""
        # 做标识的值
        for key in self.key:
            where_str += f'''object.`{key}`="{self.properties[key]}" and '''
        return where_str[:-4]

    def neo4j_where_subject(self) -> str:
        """用来joint_where_str的后续拼接
        """
        where_str = " and "
        # 做标识的值
        for key in self.key:
            where_str += f'''subject.`{key}`="{self.properties[key]}" and '''
        return where_str[:-4]

    def neo4j_check_exist(self) -> str:
        """生成用于neo4j数据库判断实体是否存在的cql语句

        Returns:
            str: _description_
        """
        # 例子
        # MATCH (object:Reference)
        # WHERE object.Url="https://www.bleepingcomputer.com/news/microsoft/microsoft-disables-dde-feature-in-word-to-prevent-further-malware-attacks/"
        # RETURN object
        query = f'''MATCH (object:{self.type}) WHERE {self.neo4j_where()} RETURN object'''
        return query

    def check_update(self, check) -> bool:
        """通过返回值判断是否要更新参数
       通过返回值的属性值数量和版本号来判断

        Args:
            check (neo4j.graph.Node): _description_

        Returns:
            bool: True需要更新，False不需要更新
        """
        if len(check._properties) < len(self.properties):
            return True
        elif float(check._properties.get("Version", 0)) < float(self.properties.get("Version", 0)):
            return True
        else:
            return False

    def neo4j_update(self) -> str:
        """通过拼接字符串，设置实体的属性来更新实体的cql语句

        Returns:
            str: 可执行的cql语句
        """
        set_str = ""
        for property in self.properties:
            set_str += f'''object.`{property}` = "{self.properties[property]}",'''
        # 构造cql语句，创建技术节点
        query = f'''MATCH (object:{self.type}) WHERE {self.neo4j_where()} SET {set_str[:-1]}  RETURN object'''
        return query

    def neo4j_joint_property(self) -> str:
        """通过json拼接属性的cql语句
        例子
        Name: "/etc/passwd and /etc/shadow", ID: "T1003.008",Version  : "1.0"
        """
        property_str = ""
        # 构造cql语句
        # 取[:-1]去掉最后的逗号
        # 实体的属性
        for property in self.properties:
            property_str += f'''`{property}`  : "{self.properties[property]}",'''
        return property_str[:-1]

    def neo4j_create(self) -> str:
        """通过拼接字符串，设置实体的属性来构造实体的cql语句
        例子
        MERGE (object:AttackTechnique
            {
                Name  : "/etc/passwd and /etc/shadow",
                ID  : "T1003.008",
                Subtechnique  : "True",
                Version  : "1.0",
                Created_by  : "2020-02-11T18:46:56.263Z",
                Last_Modified  : "2021-04-29T14:49:39.188Z",
                Description  : "Adversaries may attempt to dump the contents ... ",
                Detection  : "The AuditD monitoring ... and arguments of such programs."
            })
        RETURN object

        Returns:
            str: 可执行的cql语句
        """
        property_str = self.neo4j_joint_property()
        # 构造cql语句，创建技术节点
        query = f'''MERGE (object:{self.type} {{ {property_str} }}) RETURN object'''
        return query


class Rentity:
    """关系
    """

    def __init__(self, r_type: str, s_type: str, s_constraint: dict, t_type: str, t_constraint: dict, properties: dict) -> None:
        """关系
        关系例子：
        {
            "Relationship":"used",
            "Source_Type":"Technique",
            "Source_Constraint" : {"stix_id":"attack-pattern--970a3432-3237-47ad-bcca-7d8cbb217736"}
            "Target_Type":"Group",
            "Target_Constraint" : {"stix_id":"intrusion-set--fed4f0a2-4347-4530-b0f5-6dfd49b29172"}
            "Properties":{
                "Created":"2021-10-13T22:04:28.608Z",
                "Created_by":"The MITRE Corporation",
                "Description":"[Nomadic Octopus](https://attack.mitre.org/groups/G0133) has used PowerShell for execution.(Citation: ESET Nomadic Octopus 2018) ",
                "Domain":"['enterprise-attack']",
                "Last_Modified":"2021-10-14T14:09:00.754Z",
                "Reference":"[{'url': 'https://www.virusbulletin.com/uploads/pdf/conference_slides/2018/Cherepanov-VB2018-Octopus.pdf', 'description': 'Cherepanov, A. (2018, October 4). Nomadic Octopus Cyber espionage in Central Asia. Retrieved October 13, 2021.', 'source_name': 'ESET Nomadic Octopus 2018'}]",
                "Version":"1.0"
            },
        }


        Args:
            r_type (str): 关系类型
            s_type (str): 源节点类型
            s_constraint (dict): 源节点的限制条件or源节点的属性
            t_type (str): 目标节点类型
            t_constraint (dict): 目标节点的限制条件or目标节点的属性
            properties (dict): 关系的属性
        """
        if r_type == '':
            self.r_type = "unknown"
        else:
            self.r_type = r_type
        self.s_type = s_type
        self.s_constraint = s_constraint
        self.t_type = t_type
        self.t_constraint = t_constraint
        self.properties = properties

    def check_point_itself(self) -> bool:
        """判断关系是否自己指向自己
        """
        if self.s_type == self.t_type:
            source = set(self.s_constraint.items())
            target = set(self.t_constraint.items())
            if source.issubset(target) or target.issubset(source):
                return True
            return False
        else:
            return False

    def reverse_relationship(self) -> None:
        """调转关系relationship的方向
        """
        self.s_type, self.t_type = self.t_type, self.s_type
        self.s_constraint, self.t_constraint = self.t_constraint, self.s_constraint

    def neo4j_create(self) -> str:
        """使用关系生成用于neo4j数据库的cql语句

        例子
        MATCH (object:Technique),(subject:Group)
        WHERE object.stix_id = "attack-pattern--f232fa7a-025c-4d43-abc7-318e81a73d65" and subject.stix_id = "intrusion-set--bef4c620-0787-42a8-a96d-b7eb6e85917c"
        MERGE (object) - [r:used 
            {
                Created_by  : "The MITRE Corporation",
                Version  : "1.0",
                Last_Modified  : "2021-07-26T17:53:02.254Z",
                Created  : "2021-07-26T17:53:02.254Z",
                Domain  : "['enterprise-attack']"
            }
        ] -> (subject)
        RETURN object, subject

        Returns:
            str: 可执行的cql语句
        """
        # 创建关系
        query = f'''MATCH (object:{self.s_type}),(subject:{self.t_type}) WHERE {self.neo4j_where()} 
        MERGE (object) - [r:`{self.r_type}` {{ {self.neo4j_joint_property()} }} ] -> (subject) RETURN object, subject'''
        return query

    def neo4j_where(self) -> str:
        """使用关系的约束条件生成用于neo4j数据库约束条件的cql语句
        例子
        WHERE object.stix_id = "attack-pattern--f232fa7a-025c-4d43-abc7-318e81a73d65" and subject.stix_id = "intrusion-set--bef4c620-0787-42a8-a96d-b7eb6e85917c"
        """
        # 约束条件
        constraint_str = []
        for k, v in self.s_constraint.items():
            constraint_str.append(
                f'object.`{k}` = "{v}"')
        for k, v in self.t_constraint.items():
            constraint_str.append(
                f'subject.`{k}` = "{v}"')
        where_str = ""
        for s in constraint_str:
            where_str += s + " and "
        return where_str[:-5]

    def neo4j_joint_property(self) -> str:
        """通过json拼接属性的cql语句
        例子
        Name: "/etc/passwd and /etc/shadow", ID: "T1003.008",Version  : "1.0"
        """
        property_str = ""
        # 构造cql语句
        # 取[:-1]去掉最后的逗号
        # 实体的属性
        for property in self.properties:
            property_str += f'''`{property}`  : "{self.properties[property]}",'''
        return property_str[:-1]
