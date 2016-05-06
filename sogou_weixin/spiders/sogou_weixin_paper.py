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


class sogouWeixinPaperSpider(sogou_weixin):
    name = 'sogou_weixin_paper'

    search_keywords = []  # see settings
    start_urls = []

    def start_requests(self):

        self.getWebDriver()
        self.search_keywords = self.settings['SEARCH_KEYWORDS']
        self.start_urls = [('http://weixin.sogou.com/weixin?query=%s&type=2&tsn=2' % keyword) for keyword in
                           self.search_keywords]

        for start_url in self.start_urls:
            url_to_get = start_url
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
                    try:
                        brief = self.driver.find_element_by_xpath("//div[@class='txt-box']/p[contains(@id,'summary_%d')]" % i).text
                        weixin_name = self.driver.find_element_by_xpath("//div[contains(@id,'box_%d')]/div[@class='txt-box']/div[@class='s-p']/a[@id='weixin_account']" % i).get_attribute("title")
                        str_pubtime = self.driver.find_element_by_xpath("//div[contains(@id,'box_%d')]/div[@class='txt-box']/div[@class='s-p']/span[@class='time']" % i).text.encode('utf-8')
                        pubtime = self.switch_time(str_pubtime)

                        item = items.SogouWeixinItem()
                        item['crawler'] = self.name

                        # item['page_source'] = html
                        item['brief'] = brief
                        item['weixin_name'] = weixin_name
                        item['pubtime'] = pubtime
                        item['search_keyword'] = re.search("query=.+?&", url_to_get).group(0).replace("query=", "").replace("&", "")
                        item['url'] = self.driver.find_element_by_xpath(
                            "//div[@class='txt-box']/h4/a[contains(@id,'title_%d')]" % i).get_attribute("href")
                        item['title'] = self.driver.find_element_by_xpath(
                            "//div[@class='txt-box']/h4/a[contains(@id,'title_%d')]" % i).text

                        meta = {'item': item}

                        yield scrapy.Request(url=item['url'], callback=self.parse_item, meta=meta)

                    except NoSuchElementException:
                        print("element not found while parsing detail page %d" % i)
                    except WebDriverException:
                        print("web driver exception %d" % i)

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
            self.logger.info("成功获得列表页.")
            return False

        if self.retry_time > int(self.settings['MAX_RETRY']):
            self.logger.info("超过最大重试次数 %s" % self.settings['MAX_RETRY'])
            self.retry_time = 0
            return False
        self.logger.info("未成功获得列表页,将重试...")

        text = raw_input("请前往浏览器查看原因，如被限制，请解禁后按回车继续...")

        return True