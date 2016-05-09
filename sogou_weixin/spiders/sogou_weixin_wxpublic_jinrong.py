# -*- coding: utf-8 -*-
from __future__ import absolute_import

import platform
import re

import pymongo
from pyvirtualdisplay import Display

from sogou_weixin.spiders.sogou_weixin_wxpublic import SogouWeixinWxpublicSpider
from scrapy.utils.project import get_project_settings


class SogouWeixinWxpublicJinrongSpider(SogouWeixinWxpublicSpider):
    name = "sogou_weixin_wxpublic_jinrong"

    search_keywords = None
    start_urls = []


    def __init__(self):
        settings = get_project_settings()

        self.create_display()

        self.load_proxy_list()

        self.get_item_seen(settings)

        self.monitor_accounts_file = "keywords_jinrong_bang.in"
