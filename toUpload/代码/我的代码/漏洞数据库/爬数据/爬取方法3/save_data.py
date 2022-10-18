from pymysqlpool import ConnectionPool

class SaveData(object):
    def __init__(self):
        self.config = {
            'pool_name': 'local',
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'mq1989',
            'database': 'cnvd',
            'max_pool_size': 50
        }

    def connection_pool(self):
        pool = ConnectionPool(**self.config)
        return pool

    def find_one(self, table, column, data):
        _sql = "select 1 from " + table + " where " + column + "=(%s) limit 1"
        with self.connection_pool().cursor() as cursor:
            result = cursor.execute(_sql, (data, ))
        return result

    def insert(self, table, _sql, item):
        if item.get("cnvd_id"):
            result = self.find_one(table, "cnvd_id", item["cnvd_id"])
        if result != 1:
            with self.connection_pool().cursor() as cursor:
                cursor.execute(_sql, tuple(item.values()))

    def save(self, item):
        table = 'web'
        column_str = ''
        value_str = ''
        for key in item.keys():
            column_str = column_str + " " + key + ","
            value_str = value_str + " %s,"
        _sql = "INSERT INTO {}({}) VALUES({})".format(table, column_str[1:-1], value_str[1:-1])
        self.insert(table, _sql, item)


if __name__ == "__main__":
    # 测试
    pool = SaveData()
    item = {
        'title': 'Joomla! com_regionalm Icta Regional Museum SQL注入漏洞', 'cnvd_id': 'CNVD-2018-11969',
        'pub_date': '2018-06-25', 'harm_level': '高',
        'bug_desc': 'Joomla!是美国OpenSourceMatters团队开发的一套开源的内容管理系统(CMS)。Joomla!com_regionalmIctaRegionalMuseum存在SQL注入漏洞，攻击者可利用漏洞获得数据库敏感信息。',
        'ref_link': '', 'solve_method': '目前没有详细的解决方案提供：https://www.exploitalert.com/view-details.html?id=30141',
        'firm_patch': '(无补丁信息)', 'verify_info': '已验证', 'report_date': '2018-06-25', 'record_date': '2018-06-25',
        'update_date': '2018-06-25', 'attachment': '(无附件)'}
    pool.save(item)
