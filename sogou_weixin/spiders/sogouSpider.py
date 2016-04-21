# coding=utf-8
import scrapy
from scrapy import log
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from sogou_weixin.items import SogouWeixinItem
import time
import datetime
import hashlib
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import re
import random
from scrapy.settings import Settings
import json


class sogouSpider(scrapy.Spider):
    name = 'sogou_weixin'

    search_keywords = []  # see settings
    start_urls = []

    def __init__(self, **kwargs):

        # proxies
        super(sogouSpider, self).__init__(**kwargs)

        self.proxy_list = "proxys.txt"
        fin = open(self.proxy_list)

        self.proxies = {}
        for line in fin.readlines():
            parts = re.match('(\w+://)(\w+:\w+@)?(.+)', line)

            # Cut trailing @
            if parts.group(2):
                user_pass = parts.group(2)[:-1]
            else:
                user_pass = ''

            self.proxies[parts.group(1) + parts.group(3)] = user_pass

        fin.close()

    def start_requests(self):

        if self.settings['WEBDRIVER_USE_PROXY']:
            self.getProxyDriver()
        else:
            self.getDriver()
        self.search_keywords = self.settings['SEARCH_KEYWORDS']
        self.start_urls = [('http://weixin.sogou.com/weixin?query=%s&type=2&tsn=2' % keyword) for keyword in
                           self.search_keywords]

        for start_url in self.start_urls:
            url_to_get = start_url
            while url_to_get:
                # print os.getcwd()
                # random proxy



                # # test
                # self.driver.get("http://guanxiaoda.cn")
                # print(self.driver.page_source)
                # #
                log.msg("selenium webdriver visiting list page: [%s]" % url_to_get)

                try:
                    self.driver_get_or_retry(url_to_get)
                    # self.close_unuse_wnds()
                    self.wnds_visited = set()
                    list_page_wnd = self.driver.current_window_handle
                except Exception:

                    log.msg("err while selenium requesting: %s" % url_to_get, _level=log.ERROR)
                    log.msg(Exception.__str__())
                    raw_input("waiting for manual conti...")
                    continue

                for i in range(0, 10):
                    try:
                        brief = self.driver.find_element_by_xpath(
                            "//div[@class='txt-box']/p[contains(@id,'summary_%d')]" % i).text
                        weixin_name = self.driver.find_element_by_xpath(
                            "//div[contains(@id,'box_%d')]/div[@class='txt-box']/div[@class='s-p']/a[@id='weixin_account']" % i).get_attribute(
                            "title")
                        str_pubtime = self.driver.find_element_by_xpath(
                            "//div[contains(@id,'box_%d')]/div[@class='txt-box']/div[@class='s-p']/span[@class='time']" % i).text.encode(
                            'utf-8')
                        pubtime = self.switch_time(str_pubtime)

                        item = SogouWeixinItem()

                        # item['page_source'] = html
                        item['brief'] = brief
                        item['weixin_name'] = weixin_name
                        item['pubtime'] = pubtime
                        item['search_keyword'] = re.search("query=.+?&", url_to_get).group(0).replace("query=",
                                                                                                      "").replace("&",
                                                                                                                  "")

                        # 以下是scrapy版抽取详情页
                        item['url'] = self.driver.find_element_by_xpath(
                            "//div[@class='txt-box']/h4/a[contains(@id,'title_%d')]" % i).get_attribute("href")
                        item['title'] = self.driver.find_element_by_xpath(
                            "//div[@class='txt-box']/h4/a[contains(@id,'title_%d')]" % i).text
                        # html = self.driver.page_source

                        meta = {'item': item}

                        yield scrapy.Request(url=item['url'], callback=self.parse_item, meta=meta)

                        # 以下是selenium webdriver版抽取详情页
                        # wait = self.get_sleep_time()
                        # log.msg("wait %d seconds to get detail page..." % wait)
                        # time.sleep(wait)

                        # x = "//div[@class='txt-box']/h4/a[contains(@id,'title_%d')]" % i
                        # self.driver.find_element_by_xpath(x).click()
                        # time.sleep(3)  # wait page load
                        #
                        # wnds = self.driver.window_handles
                        # for wnd in wnds:
                        #     # skip visited windows
                        #     if list_page_wnd == wnd:
                        #         continue
                        #     elif wnd in self.wnds_visited:
                        #         continue
                        #     else:
                        #         self.driver.switch_to.window(wnd)  # switch to detail page window
                        #         self.wnds_visited.add(wnd)
                        #         print("visiting... [%d] [%s]" % (i, self.driver.title))
                        #         # visiting detail page
                        #
                        #
                        #         url = self.driver.current_url
                        #         title = self.driver.title
                        #         # html = self.driver.page_source
                        #         item['url'] = url
                        #         item['title'] = title
                        #
                        #         meta = {'item': item}
                        #
                        #         yield scrapy.Request(url=url, callback=self.parse_item, meta=meta)
                        # self.driver.close()
                        # self.driver.switch_to.window(list_page_wnd)
                        # break # debug
                    except NoSuchElementException:
                        print("element not found while parsing detail page %d" % i)
                    except WebDriverException:
                        print("web driver exception %d" % i)

                # log.msg("list page %s parsed." % url_to_get)

                wait = 15 + 2 * self.get_sleep_time()
                log.msg("wait %d seconds to get next list page..." % wait)
                time.sleep(wait)
                try:
                    if self.driver.find_element_by_xpath("//a[@id='sogou_next']"):

                        url_to_get = self.get_next_url(url_to_get)
                    else:
                        log.msg("no next page.")
                        url_to_get = None
                except NoSuchElementException:
                    log.msg("no next page.")
                    url_to_get = None

    def close_unuse_wnds(self):
        '''
        clear unuse window handles, release memory
        :return: none
        '''
        if not self.driver:
            return
        curr_wnd = self.driver.current_window_handle
        for wnd in self.driver.window_handles:
            if wnd == curr_wnd:
                continue
            self.driver.switch_to.window(wnd)
            self.driver.close()
            self.driver.switch_to.window(curr_wnd)
        self.driver.switch_to.window(curr_wnd)

    def need_retry_list(self):
        '''
        判断是否需要retry
        :return: false 不需要重试; true 需要重试
        '''
        page_source = self.driver.page_source
        if page_source.find(u"的相关微信公众号文章") > -1:
            log.msg("成功获得列表页.")
            return False

        if self.retry_time > int(self.settings['MAX_RETRY']):
            log.msg("超过最大重试次数 %s" % self.settings['MAX_RETRY'])
            self.retry_time = 0
            return False
        log.msg("未成功获得列表页,将重试...")
        log.msg()

        text = raw_input("请前往浏览器查看原因，如被限制，请解禁后按回车继续...")

        return True

    def need_retry_detail(self):
        '''
        判断是否需要retry
        :return: false 不需要重试; true 需要重试
        '''
        # 详情页不做判断,允许遗漏
        return False

    def get_next_url(self, curr_url):


        page_num = re.search("&page=\d+", curr_url)
        nextUrl = None
        if page_num:
            int_page_num = int(page_num.group(0).replace("&page=", ""))
            if int_page_num >= int(self.settings['MAX_PAGE']):
                log.msg(
                    "reach max page count: [curr: %d|max: %s], will stop." % (int_page_num, self.settings['MAX_PAGE']))
                return None
            nextUrl = re.sub("&page=\d+", "&page=%d" % (int_page_num + 1), curr_url)
        else:
            nextUrl = curr_url + "&page=2"
        return nextUrl

    def parse_item(self, response):
        if response.body.find("当前请求已过期") > -1:
            log.msg("当前请求已过期 %s " % response.url)
            return
        item = response.meta['item']
        # print("parsing detail page %s ... " % item['title'])

        content = response.xpath("//div[@id='page-content']//text()").extract()
        img_url = response.xpath("//div[@id='page-content']//img/@src").extract()
        # nQrcode = response.xpath("//img[@id='js_pc_qr_code_img]/@src").extract()
        # if nQrcode:
        #     qrcode = "http://mp.weixin.qq.com%s" % response.xpath("//img[@id='js_pc_qr_code_img']/@src").extract()[0].encode('utf-8')
        md5 = hashlib.md5(item['url']).hexdigest()
        inserttime = time.strftime("%Y-%m-%d %H%M%S")

        item['url'] = response.url
        item['content'] = content
        item['img_url'] = img_url
        item['md5'] = md5
        item['inserttime'] = inserttime

        yield scrapy.Request(url=item['url'].encode('utf-8').replace("/s?", "/mp/getcomment?"),
                             callback=self.parse_read_like, meta={'item': item})

    def parse_read_like(self, response):
        item = response.meta['item']
        # print("parsing read&like nums of %s" % item['title'])
        json_body = json.loads(response.body)
        read_num = json_body['read_num']
        like_num = json_body['like_num']

        item['read_num'] = read_num
        item['like_num'] = like_num
        log.msg("%s {'read':%d, 'like':%d} %s, %s" % (
        item['title'], item['read_num'], item['like_num'], item['pubtime'], item['inserttime']))
        yield item

    def switch_time(self, time_str):
        '''
        :param time_str: 时间字符串: n天前,n小时前,n分钟前,n秒前
        :return: str formated time
        '''
        m = re.match("\d+天前", time_str)
        if m:
            t = m.group()[0]
            return (datetime.datetime.now() - datetime.timedelta(days=int(t))).strftime("%Y-%m-%d")

        m = re.match("\d+[小]*时前", time_str)
        if m:
            t = m.group()[0]
            return (datetime.datetime.now() - datetime.timedelta(hours=int(t))).strftime("%Y-%m-%d %H:%M:%S")

        m = re.match("\d+分[钟]*前", time_str)
        if m:
            t = m.group()[0]
            return (datetime.datetime.now() - datetime.timedelta(minutes=int(t))).strftime("%Y-%m-%d %H:%M:%S")

        m = re.match("\d+秒前", time_str)
        if m:
            t = m.group()[0]
            return (datetime.datetime.now() - datetime.timedelta(seconds=int(t))).strftime("%Y-%m-%d %H:%M:%S")

        return None

    def getDriver(self):
        self.driver = webdriver.Firefox()
        self.driver.maximize_window()

    def getProxyDriver(self):

        PROXY_ADDRESS = random.choice(self.proxies.keys())

        address = PROXY_ADDRESS.replace("http://", "").replace("https://", "")

        host = address.split(':')[0]
        port = int(address.split(':')[1])
        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.proxy.type", 1)
        profile.set_preference("network.proxy.http", host)
        profile.set_preference("network.proxy.http_port", port)
        profile.update_preferences()

        self.driver = webdriver.Firefox(firefox_profile=profile)
        log.msg("creating driver: [%s] using proxy [%s]" % (self.driver.name, PROXY_ADDRESS))
        self.driver.maximize_window()

    def get_sleep_time(self):
        WEBDRIVER_DELAY = self.settings['WEBDRIVER_DELAY']
        m = re.match("\d+\-\d+$", WEBDRIVER_DELAY)

        if m:
            base = WEBDRIVER_DELAY.split('-')[0]
            ran = WEBDRIVER_DELAY.split('-')[1]
            return random.randrange(int(base), int(ran))
        m = re.match("\d+$", WEBDRIVER_DELAY)
        if m:
            return int(WEBDRIVER_DELAY)
        print("check settings:WEBDRIVER_DELAY, current conf: %s" % WEBDRIVER_DELAY)

    def driver_get_or_retry(self, url_to_get):

        self.driver.get(url_to_get)

        time.sleep(3)  # wait page load

        self.retry_time = 0
        while self.need_retry_list():
            log.msg("retrying... [%d]" % self.retry_time)
            self.retry_time += 1

            self.driver.get(url_to_get)
            time.sleep(3)  # wait page load
