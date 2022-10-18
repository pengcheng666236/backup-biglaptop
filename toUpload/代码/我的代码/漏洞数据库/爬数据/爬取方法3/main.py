import logging
from concurrent.futures import ThreadPoolExecutor
from cnvd import Cnvd
from save_data import SaveData

# 设置日志格式
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
# 设置时间格式
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
# 日志配置信息
logging.basicConfig(filename='cnvd_web.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)

def main():
    spider = Cnvd('29')
    # 获取列表页最大页码
    max_page = spider.get_max_page()
    logging.info("爬取typeID<{}>总页数<{}>".format(spider.type_id, str(max_page)))
    if max_page:
        for list_page_content in spider.get_list_page(max_page):
            href_list = spider.parse_list_page(list_page_content)
            with ThreadPoolExecutor(len(href_list)) as executor:
                executor.map(spider.get_detail_info, href_list)


if __name__ == "__main__":
    main()
