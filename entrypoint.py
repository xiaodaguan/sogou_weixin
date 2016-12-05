#!/usr/bin/env python


from scrapy.cmdline import execute
import os


# execute(['scrapy', 'crawl', 'testaaa'])
execute(['scrapy', 'crawl', 'wechat_article'])

# execute(['scrapy','genspider','sogou_weixin_wxpublic','sogou.com'])