from py2neo import Graph, Node, Relationship, NodeMatcher
import py2neo
import csv

graph = Graph('http://localhost:7474', user='neo4j', password='123456')
graph.run('match (n) detach delete n')
with open('relation_refined.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for item in reader:
        if reader.line_num == 1:
            continue
        print("当前行数：", reader.line_num, "当前内容", item)
        start_node = Node("Person", name=item[1])
        end_node = Node("Person", name=item[2])
        relation = Relationship(start_node, item[3], end_node)

        graph.merge(start_node, "Person", "name")
        graph.merge(end_node, "Person", "name")
        graph.merge(relation, "Person", "name")

graph.run('MATCH (p: Person {name:"贾宝玉"})-[k:丫环]-(r) return p,k,r')
# MATCH (p: Person {name:"贾宝玉"})-[k:丫环]-(r)
# return p,k,r


# MATCH (p1:Person {name:"贾宝玉"}),(p2:Person{name:"香菱"}),p=shortestpath((p1)-[*..10]-(p2))
# RETURN p
