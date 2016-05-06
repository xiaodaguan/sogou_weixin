# coding=utf-8
from __future__ import absolute_import
from pyvirtualdisplay import Display

import datetime
import random
import re
import time

from scrapy import Spider
from selenium import webdriver
import platform


class sogou_weixin(Spider):
    def __init__(self, **kwargs):

        self.client_sys_info = platform.platform().lower()
        if self.client_sys_info.find("windows") == -1 :
            self.display = Display(visible=0, size=(1280, 1024))
            self.display.start()
            self.logger.info("display started.")

        # proxies
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

    def close(spider, reason):
        if spider.client_sys_info.find("windows") == -1 :
            spider.display.stop()
            spider.logger.info("display stoped.")

    def getNormalDriver(self):
        # self.driver = webdriver.Remote(desired_capabilities=webdriver.DesiredCapabilities.HTMLUNIT)
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
        self.logger.info("creating driver: [%s] using proxy [%s]" % (self.driver.name, PROXY_ADDRESS))
        self.driver.maximize_window()

    def getWebDriver(self):
        '''
        get driver using proxy or not
        :return:
        '''
        if self.settings['WEBDRIVER_USE_PROXY']:
            self.getProxyDriver()
        else:
            self.getNormalDriver()

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

        return time_str

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
            self.logger.info("成功获得列表页.")
            return False

        if self.retry_time > int(self.settings['MAX_RETRY']):
            self.logger.info("超过最大重试次数 %s" % self.settings['MAX_RETRY'])
            self.retry_time = 0
            return False
        self.logger.info("未成功获得列表页,将重试...")
        self.logger.info()

        text = raw_input("请前往浏览器查看原因，如被限制，请解禁后按回车继续...")

        return True

    def driver_get_or_retry(self, url_to_get):

        self.driver.get(url_to_get)

        time.sleep(3)  # wait page load

        self.retry_time = 0
        while self.need_retry_list():
            self.logger.info("retrying... [%d]" % self.retry_time)
            self.retry_time += 1

            self.driver.get(url_to_get)
            time.sleep(3)  # wait page load
