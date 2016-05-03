# -*- coding: utf-8 -*-
from __future__ import absolute_import
import hashlib
from urllib import unquote

import scrapy
from scrapy import log
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import json
from sogou_weixin.items import SogouWeixinItem
from sogou_weixin.spiders.sogou_weixin import sogou_weixin
import re
import time


class wxpublic_info:
    oracle_id = 0
    name = None
    weixin_name = None
    category_code = 0

    def __init__(self, oracle_id, name, weixin_name, category_code):
        self.oracle_id = oracle_id
        self.name = name
        self.weixin_name = weixin_name
        self.category_code = category_code

    def get_wxpublic_info(self):
        return "%s, %s, %d" % (self.name, self.weixin_name, self.category_code)


class SogouWeixinWxpublicSpider(sogou_weixin):
    name = "sogou_weixin_wxpublic"

    search_keywords = None
    start_urls = []

    def start_requests(self):
        '''

        依旧使用webdriver发送搜索公众号请求
        目的是找到名称和微信号匹配的条目,获取到url之后交给scrapy.request,调用parse_list作为callback
        :return:
        '''
        self.getWebDriver()
        self.wxpublic_info_list = []
        with open("keywords.in", "r") as f:
            self.search_keywords = f.readlines()
        for search_key in self.search_keywords:
            if search_key.startswith("#") or not len(search_key): continue
            search_key = search_key.replace("\n", "")
            assert len(search_key.split(",")) == 4, "err in keywords.in"

            oracle_id = int(search_key.split(",")[0])
            name = search_key.split(",")[1]
            weixin_name = search_key.split(",")[2]
            category_code = int(search_key.split(",")[3]) if len(search_key.split(",")[3]) else 0

            info = wxpublic_info(oracle_id, name, weixin_name, category_code)
            self.wxpublic_info_list.append(info)
            pass

        # set searchkey, category_code/1/2/3... for item
        for info in self.wxpublic_info_list:
            # webdriver get start url
            # 搜狗搜索结果页处理
            # 寻找匹配公众号
            start_url = "http://weixin.sogou.com/weixin?type=1&query=%s" % info.weixin_name

            self.driver_get_or_retry(start_url)
            # time.sleep(5)  # wait for page load
            try:
                x = "//div[contains(@id,'sogou_vr') and contains(@id,'box_') and contains(.,'%s') and contains(.,'%s')]" % (info.weixin_name, info.name)
                url = self.driver.find_element_by_xpath(x).get_attribute("href")
            except NoSuchElementException:
                url = None
            except WebDriverException:
                url = None
            if not url:
                log.msg("weixin public account not found %s:%s" % (info.weixin_name, info.name))
                continue
            log.msg("yield request: %s" % url)
            yield scrapy.Request(url=url, callback=self.parse_list, meta={'account_info': {'oracle_id': info.oracle_id, 'name': info.name, 'weixin_name': info.weixin_name, 'category_code': info.category_code}})

    def parse_list(self, response):
        '''

        解析公众号列表页,得到文章列表(改版后只显示10条)
        :param response:
        :return:
        '''
        log.msg("parsing list: %s" % response.url)
        account_info = response.meta['account_info']

        m = re.search(r"var msgList = '{.*}';", response.body)
        json_list_str = m.group(0).replace("var msgList = '{", "{").replace("}';", "}").replace("&quot;", '"')
        paper_list = json.loads(json_list_str)['list']

        assert paper_list != None, "check json!!!"
        for paper in paper_list:
            # parse them
            assert paper['app_msg_ext_info'] != None, "paper info not found!"
            assert paper['comm_msg_info'] != None, "comm info not found!"
            item = SogouWeixinItem()
            item['crawler'] = self.name
            item['gongzhong_id'] = account_info['oracle_id']
            item['title'] = paper['app_msg_ext_info']['title']
            item['url'] = "http://mp.weixin.qq.com%s" % paper['app_msg_ext_info']['content_url'].encode("utf-8").replace("\\", "").replace("&amp;", "&").replace("&amp;", "&")
            pubtimeStamp = paper['comm_msg_info']['datetime']
            item['pubtime'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(pubtimeStamp))
            item['author'] = account_info['name']
            item['weixin_name'] = account_info['weixin_name']
            item['category_code'] = account_info['category_code']

            log.msg("yield request: %s" % item['url'])
            yield scrapy.Request(url=item['url'], callback=self.parse_item, meta={'item': item})

    def parse_item(self, response):



        item = response.meta['item']
        log.msg("parsing item: %s" % item['title'])
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

    def need_retry_list(self):
        '''
        判断是否需要retry
        :return: false 不需要重试; true 需要重试
        '''
        page_source = self.driver.page_source
        if page_source.find(u"的相关微信") > -1:
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
