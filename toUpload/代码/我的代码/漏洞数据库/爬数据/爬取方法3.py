# -*- coding = utf-8 -*-
# @Time : 2021/8/24 21:16
# @Author : DLT
# @File : 分类爬取.py
# @Software : PyCharm

from multiprocessing import Process
from collections import OrderedDict
import time
from selenium import webdriver
from lxml import etree
import requests
from selenium.webdriver import DesiredCapabilities


def verification(ip, port):
    # 检验ip是否有效
    ips = ip + ':' + port
    proxy = {
        'http': 'http://{}'.format(ips),
        'https': 'http://{}'.format(ips)
    }
    # '''head 信息'''
    head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/50.0.2661.102 Safari/537.36',
        'Connection': 'keep-alive'}
    # '''http://icanhazip.com会返回当前的IP地址'''
    try:
        p = requests.get('http://icanhazip.com', headers=head, proxies=proxy, timeout=10)
        if p.status_code == 200:
            # 我发现，返回200都不一定是能够用的，所以还得判断输出内容是否是所使用的代理ip
            if ip == str(p.text.strip()):
                return True
        return False
    except:
        return False


def ipconfig():
    chrome_options = webdriver.ChromeOptions()
    # 获取ip并验证是否有效
    while (1):
        try:

            ipcon = requests.get(
                "代理API").json()  # 从熊猫代理获取ip
            # 每个代理的返回方式不一样，自行修改
            ip = ipcon["obj"][0]["ip"]
            port = ipcon["obj"][0]["port"]
            # print(ip, port)
        except:
            continue
        if verification(ip, port):
            break
        else:
            print("ip无效，将再次请求")
            time.sleep(1)  # 因为熊猫代理的请求每秒最多一次，此处必须暂停1s
            pass
    ips = ip + ':' + port
    chrome_options.add_argument(
        ('--proxy-server=' + ips))  # 有的博客写的是'--proxy-server=http://'

    # 以下两行为无窗口模式，加上就不会出现谷歌窗口
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--no-sandbox')
    preferences = {"directory_upgrade": True,
                   "safebrowsing.enabled": True,
                   # 下载文件的位置：
                   'download.default_directory': 'C:\\Users\\8208191402\\Desktop\\国家信息安全'}
    chrome_options.add_experimental_option("prefs", preferences)
    try:
        driver = webdriver.Chrome(chrome_options=chrome_options)
    except:
        print("失败")

    return driver


def main(n, m):
    # f为每页有多少条数据，经过检测，因为ip有效时间仅为一分钟，且网站在连续请求20次后会因访问频率过高而禁止访问，所以20为最合适的数值
    f = 0

    '''
      此处更改url， 只需更改typeId后的数字
    '''
    while (n < m):
        driver = ipconfig()
        driver.set_page_load_timeout(15)
        driver.set_script_timeout(15)
        driver.implicitly_wait(15)
        # 加入以下代码跳过js验证,模拟移动设备，弱网设置
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                      Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                      })
                    """
        })

        # s为错误计算，如果在连续15次的情况下未请求到数据，那么将会判定未ip失效，将更换ip重新请求
        s = 0

        # 自行修改url
        url = "https://www.cnvd.org.cn/flaw/typeResult?typeId=33&max=20&offset=" + str(n * 20)
        try:
            driver.get(url)
            time.sleep(1)
            try:
                if f >= 20:
                    f = 0
                while f < 20:
                    try:
                        xmls = driver.find_elements_by_xpath("//td[@width='45%']/a")
                        xmls[f].click()
                        time.sleep(1)
                        # 检测是否存在文件
                        try:
                            error = driver.title
                            if error == "出错了....":
                                print("亲爱的用户：请检查您的操作是否正确！您访问的资源不存在或已被删除")
                                f = f + 1
                                driver.back()
                                continue
                        except Exception as e:
                            f = f + 1
                            driver.back()
                            s = s + 1
                            if s >= 15:
                                try:
                                    driver.quit()
                                except:
                                    pass
                                s = 0
                                break
                            time.sleep(1)
                            continue

                        # 测试是否请求频率过快
                        try:
                            pinlv = driver.title
                            if pinlv == "国家信息安全漏洞共享平台":
                                pass
                            else:
                                s = s + 1
                                if s >= 15:
                                    break
                                print("您访问频率太高，请稍候再试。")
                                driver.back()
                                time.sleep(1)
                                continue
                        except Exception as e:
                            pass

                        html = driver.page_source
                        item = parse_detail(html)
                        # 保存数据
                        if item["标题"] == 'Null':
                            driver.back()
                            time.sleep(1)
                            f = f + 1
                            continue
                        save(item)
                        driver.back()
                        time.sleep(1)
                        f = f + 1
                        # time.sleep(2)
                    except:
                        driver.close()
                        print("网络错误，即将重新请求")
                        break
                time.sleep(1)
                print("第", n, "页爬取完毕")
                try:
                    driver.quit()
                except:
                    pass
                f = 0
                n = n + 1
            except Exception as e:
                print(e)
                print("第", n, "页发生了错误，重新请求")
                time.sleep(1)
                continue
        except Exception as e:
            print(e)
            print("ip失效，即将更换ip")

            try:
                driver.quit()
            except:
                pass
            driver = ipconfig()
            driver.set_page_load_timeout(15)
            driver.set_script_timeout(15)
            driver.implicitly_wait(15)

            # 加入以下代码跳过js验证
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
              """
            })
    print("第", n, "步爬取完毕")


# 解析每个漏洞的具体信息
def parse_detail(html):
    html = etree.HTML(html)
    item = OrderedDict()  # 如果要存入csv文档，建议用有序字典，此处未使用有序字典

    # 1、获取漏洞标题
    item["标题"] = html.xpath(
        "//div[@class='blkContainerPblk']/div[@class='blkContainerSblk']/h1/text()")
    if item["标题"]:
        item["标题"] = html.xpath("//div[@class='blkContainerPblk']/div[@class='blkContainerSblk']/h1/text()")[
            0].strip()
    else:
        item["标题"] = 'Null'

    # 2、 获取cnvd id
    item["CNVD-ID"] = html.xpath(
        "//td[text()='CNVD-ID']/following-sibling::td[1]/text()")
    if item["CNVD-ID"]:
        item["CNVD-ID"] = "".join(
            [i.strip() for i in item["CNVD-ID"]])
    else:
        item["CNVD-ID"] = 'Null'

    # 3、 获取漏洞公开日期
    item["公开日期"] = html.xpath(
        "//div[@class='tableDiv']/table[@class='gg_detail']//tr[2]/td[2]/text()")
    if item["公开日期"]:
        item["公开日期"] = "".join(
            [i.strip() for i in item["公开日期"]])
        # item["pub_date"] = self.convertstringtodate(item["pub_date"])
    else:
        item["公开日期"] = '2000-01-01'
        # item["pub_date"] = self.convertstringtodate(item["pub_date"])

    # 4、 获取漏洞危害级别
    item["危害级别"] = html.xpath(
        "//td[text()='危害级别']/following-sibling::td[1]/text()")
    if item["危害级别"]:
        item["危害级别"] = "".join(
            [i.replace("(", "").replace(")", "").strip() for i in item["危害级别"]])
    else:
        item["危害级别"] = 'Null'

    # 5、 获取漏洞影响的产品
    item["影响产品"] = html.xpath(
        "//td[text()='影响产品']/following-sibling::td[1]/text()")
    if item["影响产品"]:
        item["影响产品"] = " ; ".join(
            [i.strip() for i in item["影响产品"]])
    else:
        item["影响产品"] = 'Null'

    # 6、 获取漏洞描述
    item["漏洞描述"] = html.xpath(
        "//td[text()='漏洞描述']/following-sibling::td[1]//text()")
    if item["漏洞描述"]:
        item["漏洞描述"] = "".join(
            [i.strip() for i in item["漏洞描述"]]).replace('\\t', '').replace('\\n', '')  # replace("\u200b", "")
    else:
        item["漏洞描述"] = 'Null'

    # 7、 获取漏洞的参考链接
    item["参考链接"] = html.xpath(
        "//td[text()='参考链接']/following-sibling::td[1]/a/@href")
    if item["参考链接"]:
        item["参考链接"] = item["参考链接"][0].replace('\r', '').replace('\n', '')
    else:
        item["参考链接"] = 'Null'

    # 8、获取漏洞类型
    item["漏洞类型"] = html.xpath(
        "//td[text()='漏洞类型']/following-sibling::td[1]//text()")
    if item["漏洞类型"]:
        item["漏洞类型"] = "".join(
            [i.strip() for i in item["漏洞类型"]])
    else:
        item["漏洞类型"] = 'Null'

    # 9 、获取漏洞解决方案
    item["漏洞解决方案"] = html.xpath(
        "//td[text()='漏洞解决方案']/following-sibling::td[1]//text()")
    if item["漏洞解决方案"]:
        item["漏洞解决方案"] = "".join(
            [i.strip() for i in item["漏洞解决方案"]])
    else:
        item["漏洞解决方案"] = 'Null'

    # 10、 获取厂商补丁
    item["厂商补丁"] = html.xpath(
        "//td[text()='厂商补丁']/following-sibling::td[1]/a")
    if item["厂商补丁"]:
        for i in item["厂商补丁"]:
            list = []
            try:
                list.append(i.xpath("./text()")[0])
                list.append("https://www.cnvd.org.cn" + i.xpath("./@href")[0])
                item["厂商补丁"] = list[0] + ':' + list[1]
            except IndexError:
                pass
    else:
        item["厂商补丁"] = 'Null'

    # 11、获取验证信息
    item["验证信息"] = html.xpath(
        "//td[text()='验证信息']/following-sibling::td[1]//text()")
    if item["验证信息"]:
        item["验证信息"] = "".join(
            [i.strip() for i in item["验证信息"]])
    else:
        item["验证信息"] = 'Null'

    # 12、 获取漏洞报送时间
    item["报送时间"] = html.xpath(
        "//td[text()='报送时间']/following-sibling::td[1]/text()")
    if item["报送时间"]:
        item["报送时间"] = "".join(
            [i.strip() for i in item["报送时间"]])
    else:
        item["报送时间"] = '2000-01-01'

    # 13、  获取漏洞收录时间
    item["收录时间"] = html.xpath(
        "//td[text()='收录时间']/following-sibling::td[1]/text()")
    if item["收录时间"]:
        item["收录时间"] = "".join(
            [i.strip() for i in item["收录时间"]])
    else:
        item["收录时间"] = '2000-01-01'

    # 14、  获取漏洞更新时间
    item["更新时间"] = html.xpath(
        "//td[text()='更新时间']/following-sibling::td[1]/text()")
    if item["更新时间"]:
        item["更新时间"] = "".join(
            [i.strip() for i in item["更新时间"]])
    else:
        item["更新时间"] = '2000-01-01'

    return item


def save(datlist):
    f = open("C:\\Users\\8208191402\\Desktop\\国家信息安全\\应用程序.csv", 'a+', encoding='gbk')
    dat = datlist
    try:
        # 存储数据时，可按照自己的方式进行存储
        data = dat["标题"] + ',' + dat["CNVD-ID"] + ',' + dat["公开日期"] + ',' + dat["危害级别"] + ',' + dat[
            "影响产品"].replace(',',
                                '，') + ',' + \
               dat["漏洞描述"].replace(',', '，') + ',' + dat["漏洞类型"] + ',' + dat["参考链接"].replace(',',
                                                                                                         '，') + ',' + \
               dat[
                   "漏洞解决方案"].replace(',', '，') + ',' + dat["厂商补丁"].replace(',', '，') + ',' + \
               dat["验证信息"] + ',' + dat["报送时间"] + ',' + dat["收录时间"] + ',' + dat["更新时间"] + '\n'
        f.write(data)
        # print(dat["标题"] + " " + "保存成功")
    except Exception as e:
        print("保存失败")
        print(e)


if __name__ == '__main__':
    desired_capabilities = DesiredCapabilities.CHROME
    desired_capabilities["pageLoadStrategy"] = "none"

    process_list = []

    # 每个进程爬取的页数
    yeshu = 50

    # 以为应用程序页页数太多，为防止出现特殊情况，分步爬取，所以加上了起始页数
    qishiweizhi = 2500
    # yeshu = yeshu * 1

    # 建议改为 POOL ，此处是因为修改参数方便所以未使用POOL

    p1 = Process(target=main, args=(0 + qishiweizhi, yeshu + qishiweizhi))
    p1.start()
    time.sleep(3)

    p2 = Process(target=main, args=(yeshu + qishiweizhi, yeshu * 2 + qishiweizhi))
    p2.start()
    time.sleep(3)

    p3 = Process(target=main, args=(yeshu * 2 + qishiweizhi, yeshu * 3 + qishiweizhi))
    p3.start()
    time.sleep(3)

    p4 = Process(target=main, args=(yeshu * 3 + qishiweizhi, yeshu * 4 + qishiweizhi))
    p4.start()
    time.sleep(3)

    p5 = Process(target=main, args=(yeshu * 4 + qishiweizhi, yeshu * 5 + qishiweizhi))
    p5.start()
    time.sleep(3)

    p6 = Process(target=main, args=(yeshu * 5 + qishiweizhi, yeshu * 6 + qishiweizhi))
    p6.start()
    time.sleep(3)

    p7 = Process(target=main, args=(yeshu * 6 + qishiweizhi, yeshu * 7 + qishiweizhi))
    p7.start()
    time.sleep(3)

    p8 = Process(target=main, args=(yeshu * 7 + qishiweizhi, yeshu * 8 + qishiweizhi))
    p8.start()
    time.sleep(3)

    p9 = Process(target=main, args=(yeshu * 8 + qishiweizhi, yeshu * 9 + qishiweizhi))
    p9.start()
    time.sleep(3)

    p10 = Process(target=main, args=(yeshu * 9 + qishiweizhi, yeshu * 10 + qishiweizhi))
    p10.start()
    time.sleep(3)

    process_list.append(p1)
    time.sleep(3)
    process_list.append(p2)
    time.sleep(3)
    process_list.append(p3)
    time.sleep(3)
    process_list.append(p4)
    time.sleep(3)
    process_list.append(p5)
    time.sleep(3)
    process_list.append(p6)
    time.sleep(3)
    process_list.append(p7)
    time.sleep(3)
    process_list.append(p8)
    time.sleep(3)
    process_list.append(p9)
    time.sleep(3)
    process_list.append(p10)
    time.sleep(3)

    for t in process_list:
        t.join()
        time.sleep(3)
