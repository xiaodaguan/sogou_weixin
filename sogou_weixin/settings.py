# -*- coding: utf-8 -*-

# Scrapy settings for sogou project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#
LOG_LEVEL = 'INFO'
DOWNLOAD_DELAY = 15
RETRY_TIMES = 3
BOT_NAME = 'sogou_weixin'

SPIDER_MODULES = ['sogou_weixin.spiders']
NEWSPIDER_MODULE = 'sogou_weixin.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'sogou (+http://www.yourdomain.com)'

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    # customize
    # 'sogou_weixin.middlewares.RandomProxy': 100,
    # 'scrapy.contrib.downloadermiddleware.httpproxy.HttpProxyMiddleware': 110,
}

ITEM_PIPELINES = {
    'sogou_weixin.pipelines.SogouPipeline': 123,
}

PROXY_LIST = 'proxys.txt'
UA_LIST = 'uas.txt'
COOKIE_LIST = 'cookies.txt'

WEBDRIVER_USE_PROXY = False

REDIS_ADDRESS = "172.18.79.31:6379" # unused temporarily
MONGODB_ADDRESS = "172.18.79.31:27017"
MONGODB_DB = "wechatdb"

WEBDRIVER_DELAY = "3-15" # seconds
MAX_PAGE = 2
MAX_RETRY = 3




SEARCH_KEYWORDS_FILE = 'keywords.in'