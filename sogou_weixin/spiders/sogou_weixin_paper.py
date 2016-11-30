# coding=utf-8
from __future__ import absolute_import

import hashlib
import json
import re
import time

import scrapy
from selenium.common.exceptions import NoSuchElementException, WebDriverException

from sogou_weixin import items
from sogou_weixin.spiders.sogou_weixin import sogou_weixin

class search_keyword_info:
    search_keyword = None
    category_code = 0

    def __init__(self, search_keyword, category_code):
        self.search_keyword = search_keyword
        self.category_code = category_code


    def get_wxpublic_info(self):
        return "%s, %d" % (self.search_keyword, self.category_code)


class sogouWeixinPaperSpider(sogou_weixin):
    name = 'wechat_article'

    search_keywords = []  # see settings
    start_urls = []

    def start_requests(self):

        self.getWebDriver()
        self.search_keyword_info_list = []
        with open(self.settings['SEARCH_KEYWORDS_FILE'], "r") as f:
            self.search_keywords = f.readlines()
        for search_key in self.search_keywords:
            if search_key.startswith("#") or not len(search_key): continue
            search_key = search_key.replace("\n", "")
            assert len(search_key.split(",")) == 2, "err in keywords.in"

            category_code = int(search_key.split(",")[0]) if search_key.split(",")[0] != '' else 0
            search_keyword = search_key.split(",")[1]

            info = search_keyword_info(search_keyword, category_code)
            self.search_keyword_info_list.append(info)
            pass

        # self.start_urls = [('http://weixin.sogou.com/weixin?query=%s&type=2&tsn=1' % keyword) for keyword in
        #                    self.search_keywords]

        for sk_info in self.search_keyword_info_list:

            url_to_get = 'http://weixin.sogou.com/weixin?query=%s&type=2&tsn=1' % sk_info.search_keyword
            while url_to_get:
                self.logger.info("selenium webdriver visiting list page: [%s]" % url_to_get)

                try:
                    self.driver_get_or_retry(url_to_get)
                    self.wnds_visited = set()
                    list_page_wnd = self.driver.current_window_handle
                except Exception:

                    self.logger.error("err while selenium requesting: %s" % url_to_get)
                    self.logger.info(Exception.__str__())
                    raw_input("waiting for manual conti...")
                    continue

                for i in range(0, 10):
                    brief=""
                    weixin_name=""
                    str_pubtime=""
                    pubtime=""

                    try:
                        brief = self.driver.find_element_by_xpath("//div[@class='txt-box']/p[contains(@id,'summary_%d')]" % i).text
                    except NoSuchElementException:
                        print("brief not found while parsing detail page %d" % i)
                    except WebDriverException:
                        print("web driver exception %d" % i)
                    try:
                        weixin_name = self.driver.find_element_by_xpath("//li[contains(@id,'box_%d')]/div[@class='txt-box']/div[@class='s-p']/a[@data-sourcename]" % i).get_attribute("data-sourcename")
                    except NoSuchElementException:
                        print("weixin_name not found while parsing detail page %d" % i)
                    except WebDriverException:
                        print("web driver exception %d" % i)
                    try:
                        str_pubtime = self.driver.find_element_by_xpath("//li[contains(@id,'box_%d')]/div[@class='txt-box']/div[@class='s-p']/span[@class='s2']" % i).text.encode('utf-8')
                        pubtime = self.switch_time(str_pubtime)
                    except NoSuchElementException:
                        print("str_pubtime not found while parsing detail page %d" % i)
                    except WebDriverException:
                        print("web driver exception %d" % i)



                    item = items.SogouWeixinItem()
                    item['crawler'] = self.name

                    # item['page_source'] = html
                    item['brief'] = brief
                    item['weixin_name'] = weixin_name
                    item['pubtime'] = pubtime
                    item['search_keyword'] = sk_info.search_keyword
                    item['category_code'] = sk_info.category_code

                    item['url'] = self.driver.find_element_by_xpath(
                        "//div[@class='txt-box']/h3/a[contains(@id,'title_%d')]" % i).get_attribute("href")
                    item['title'] = self.driver.find_element_by_xpath(
                        "//div[@class='txt-box']/h3/a[contains(@id,'title_%d')]" % i).text

                    meta = {'item': item}
                    if item['url']:
                        yield scrapy.Request(url=item['url'], callback=self.parse_item, meta=meta)


                # log.msg("list page %s parsed." % url_to_get)

                wait = 15 + 2 * self.get_sleep_time()
                self.logger.info("wait %d seconds to get next list page..." % wait)
                time.sleep(wait)
                try:
                    if self.driver.find_element_by_xpath("//a[@id='sogou_next']"):

                        url_to_get = self.get_next_url(url_to_get)
                    else:
                        self.logger.info("no next page.")
                        url_to_get = None
                except NoSuchElementException:
                    self.logger.info("no next page.")
                    url_to_get = None

    def get_next_url(self, curr_url):

        page_num = re.search("&page=\d+", curr_url)
        nextUrl = None
        if page_num:
            int_page_num = int(page_num.group(0).replace("&page=", ""))
            if int_page_num >= int(self.settings['MAX_PAGE']):
                self.logger.info(
                    "reach max page count: [curr: %d|max: %s], will stop." % (int_page_num, self.settings['MAX_PAGE']))
                return None
            nextUrl = re.sub("&page=\d+", "&page=%d" % (int_page_num + 1), curr_url)
        else:
            nextUrl = curr_url + "&page=2"
        return nextUrl

    def parse_item(self, response):
        if response.body.find("当前请求已过期") > -1:
            self.logger.info("当前请求已过期 %s " % response.url)
            return
        item = response.meta['item']
        # print("parsing detail page %s ... " % item['title'])

        content = response.xpath("//div[@id='page-content']//text()").extract()
        img_url = response.xpath("//div[@id='page-content']//img/@src").extract()
        # nQrcode = response.xpath("//img[@id='js_pc_qr_code_img]/@src").extract()
        # if nQrcode:
        #     qrcode = "http://mp.weixin.qq.com%s" % response.xpath("//img[@id='js_pc_qr_code_img']/@src").extract()[0].encode('utf-8')

        md5 = hashlib.md5("%s%s%s"%(item['title'].encode('utf-8'),item['pubtime'].encode('utf-8'),item['weixin_name'].encode('utf-8'))).hexdigest()
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
        self.logger.info("%s {'read':%d, 'like':%d} %s, %s" % (
            item['title'], item['read_num'], item['like_num'], item['pubtime'], item['inserttime']))
        yield item

    def need_retry_list(self):
        '''
        判断是否需要retry
        :return: false 不需要重试; true 需要重试
        '''
        page_source = self.driver.page_source
        if page_source.find(u"的相关微信公众号文章") > -1:
            self.logger.info("成功获得列表页.%s" % self.driver.title.encode('utf-8'))
            return False

        if self.retry_time > int(self.settings['MAX_RETRY']):
            self.logger.info("超过最大重试次数 %s" % self.settings['MAX_RETRY'])
            self.retry_time = 0
            return False
        self.logger.info("未成功获得列表页,将重试...")

        text = raw_input("请前往浏览器查看原因，如被限制，请解禁后按回车继续...")

        return True