#!/usr/bin/env python


from scrapy.cmdline import execute
import os

execute(['scrapy', 'crawl', 'sogou_weixin_wxpublic'])
# execute(['scrapy', 'crawl', 'sogou_weixin_paper'])

# execute(['scrapy','genspider','sogou_weixin_wxpublic','sogou.com'])