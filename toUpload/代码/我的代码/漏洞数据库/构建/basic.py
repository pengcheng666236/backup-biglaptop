import py2neo
from py2neo import Graph, Node, Relationship, NodeMatcher
import csv

graph = Graph('http://localhost:7474', user='neo4j', password='123456')  # 连接图数据库
graph.run('match (n) detach delete n')  # 清空原来的节点
probable_classes = {}  # 建立类别名和图内节点的映射字典
# 建立类别节点
with open('可能的关系.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for item in reader:
        # 跳过首行的标签行
        if reader.line_num == 1:
            continue
        print("当前行数：", reader.line_num, "当前内容", item)

        probable_class = Node("Class", name=item[0])
        probable_classes[item[0]] = probable_class  # 加入字典
        graph.merge(probable_class, "Class", "name")  # 有则跳过，无则加入

# 建立实例节点；根据类别节点，建立关系
with open('../数据/ics_cnvd.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    matcher = NodeMatcher(graph)
    # nodes_data = ['特征类别', 'SQL注入', '越界读取', '越界写入', '身份验证绕过', '设备拒绝服务', '跨站脚本',
    #               'CPU拒绝服务', '路径遍历', '代码执行', '栈缓冲区溢出', '权限访问控制', '整数溢出', '保护机制失效',
    #               '远程代码执行', '内存错误引用', '信息泄露', '弱口令', '输入验证', '逻辑设计', '未授权操作', '命令',
    #               '路径遍历', '权限']
    # print(nodes_data)
    # ： Node('Class', name='越界读取')

    for item in reader:
        if reader.line_num == 1:
            continue
        print("当前行数：", reader.line_num, "当前内容", item)
        start_node = Node("Instance", name=item[1])
        for subStr in probable_classes.keys():
            # print(subStr)
            if len(set(subStr) & set(item[1])) > 1:  # 匹配达到一定程度才会聚类
                # print(subStr)
                # print(item[1])
                end_node = probable_classes[subStr]
                relation = Relationship(start_node, "包含", end_node)
                graph.merge(relation, "Instance", "name")
                print("当前特征", subStr)
                break
        graph.merge(start_node, "Instance", "name")

# match (n) return n
