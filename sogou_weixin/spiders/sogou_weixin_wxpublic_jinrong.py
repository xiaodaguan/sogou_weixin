# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sogou_weixin.spiders.sogou_weixin_wxpublic import SogouWeixinWxpublicSpider


class SogouWeixinWxpublicJinrongSpider(SogouWeixinWxpublicSpider):
    name = "sogou_weixin_wxpublic_jinrong"

    search_keywords = None
    start_urls = []

    def __init__(self):
        self.monitor_accounts_file = "keywords_jinrong_bang.in"
