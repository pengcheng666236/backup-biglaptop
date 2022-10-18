import requests
import logging
from lxml import etree
from save_data import SaveData


class Cnvd(object):
    def __init__(self, type_id):
        self.type_id = type_id
        self.host_url = "http://www.cnvd.org.cn"
        self.start_url = "http://www.cnvd.org.cn/flaw/typeResult?typeId=" + self.type_id
        self.base_url = "http://www.cnvd.org.cn/flaw/typeResult?typeId={}&max={}&offset={}"
        self.headers = {
            "Host": "www.cnvd.org.cn",
            "Origin": "http://www.cnvd.org.cn",
            "Referer": "http://www.cnvd.org.cn/flaw/typelist?typeId=" + self.type_id,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"
        }
        self.pool = SaveData()

    def get_max_page(self):
        """通过列表页第一页获取最大分页页码
        Returns:
            [type] -- [最大分页页码，整数]
        """
        respons = requests.get(url=self.start_url, headers=self.headers)
        content = respons.content.decode()
        html = etree.HTML(content)
        max_page = html.xpath("//div[@class='pages clearfix']//a[last()-1]/text()")[0]
        if max_page:
            max_page = int(max_page)
            return max_page

    def get_list_page(self, max_page):
        """获取列表页html内容
        Arguments:
            max_page {[int]} -- [最大分页页码]
        """
        _max = 20
        for page in range(max_page):
            logging.info("正在爬取列表页第<%s>页" % str(page))
            offset = page * _max
            url = self.base_url.format(self.type_id, _max, offset)
            respons = requests.get(url=url, headers=self.headers)
            content = respons.content.decode()
            yield content

    def parse_list_page(self, content):
        """获取列表页中的详情页href，返回href列表
        Arguments:
            content {[str]} -- [列表页html内容]
        Returns:
            [list] -- [详情页href列表]
        """
        html = etree.HTML(content)
        href_list = html.xpath("//tbody/tr/td//a/@href")
        return href_list

    def get_detail_info(self, href):
        """通过详情页href，获取详情页html内容
        Arguments:
            href {[str]} -- [详情页href]
        Returns:
            [调用详情页解析函数] -- [提取信息]
        """
        url = self.host_url + href
        logging.info("正在爬取详情页<%s>" % url)
        headers = {
            "Host": "www.cnvd.org.cn",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"
        }
        respons = requests.get(url=url, headers=headers)
        return self.parse_detail_page(respons.content.decode())

    def parse_detail_page(self, content):
        """从详情页中提取信息
        Arguments:
            content {[str]} -- [详情页html内容]
        Returns:
            [dict] -- [提取信息字典]
        """
        # print("="*50)
        html = etree.HTML(content)
        item = {}
        item['title'] = html.xpath("//div[@class='blkContainer']//div[@class='blkContainerSblk']/h1/text()")[0]
        tr_list = html.xpath("//div[@class='blkContainer']//div[@class='blkContainerSblk']//tbody/tr")
        for tr in tr_list:
            td_list = tr.xpath("./td/text()")
            # print(td_list)
            if len(td_list) >= 2:
                if 'CNVD-ID' in td_list[0]:
                    item['cnvd_id'] = self.handle_str(td_list)
                elif '公开日期' in td_list[0]:
                    item['pub_date'] = self.handle_str(td_list)
                elif '危害级别' in td_list[0]:
                    item['harm_level'] = self.handle_str(td_list)
                elif '产品影响' in td_list[0]:
                    item['pro_influence'] = self.handle_str(td_list)
                elif '漏洞描述' in td_list[0]:
                    item['bug_desc'] = self.handle_str(td_list)
                elif '参考链接' in td_list[0]:
                    item['ref_link'] = self.handle_str(td_list)
                elif '漏洞解决方案' in td_list[0]:
                    item['solve_method'] = self.handle_str(td_list)
                elif '厂商补丁' in td_list[0]:
                    item['firm_patch'] = self.handle_str(td_list)
                elif '验证信息' in td_list[0]:
                    item['verify_info'] = self.handle_str(td_list)
                elif '报送时间' in td_list[0]:
                    item['report_date'] = self.handle_str(td_list)
                elif '收录时间' in td_list[0]:
                    item['record_date'] = self.handle_str(td_list)
                elif '更新时间' in td_list[0]:
                    item['update_date'] = self.handle_str(td_list)
                elif '漏洞附件' in td_list[0]:
                    item['attachment'] = self.handle_str(td_list)
        if item:
            self.pool.save(item)
        return item


    def handle_str(self, td_list):
        """字符串去除空格\r\n\xa0等字符
        Arguments:
            td_list {[list]} -- [获取文本的列表]
        Returns:
            [type] -- [返回处理后的合并文本]
        """
        result = ''
        for td_str in td_list[1:]:
            result += td_str.strip()
        result = "".join(result.split())
        # 去除“危害级别”中的括号
        if result.endswith("()"):
            result = result[:-2]
        return result


if __name__ == "__main__":
    # 测试
    cnvd = Cnvd('29')
    max_page = cnvd.get_max_page()
    if max_page:
        content_generator = cnvd.get_list_page(max_page)
        for content in content_generator:
            href_list = cnvd.parse_list_page(content)
            for href in href_list:
                item = cnvd.get_detail_info(href)
                print(item)
