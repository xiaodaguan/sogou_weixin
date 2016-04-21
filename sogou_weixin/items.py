# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SogouWeixinItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    site_id = scrapy.Field()
    pubtime = scrapy.Field()
    url = scrapy.Field()
    search_keyword = scrapy.Field()
    source = scrapy.Field()
    category_code = scrapy.Field()
    inserttime = scrapy.Field()
    md5 = scrapy.Field()
    content = scrapy.Field()
    brief = scrapy.Field()
    img_url = scrapy.Field()
    same_num = scrapy.Field()
    same_url = scrapy.Field()
    read_num = scrapy.Field()
    like_num = scrapy.Field()
    updated = scrapy.Field()
    avatar = scrapy.Field()
    img = scrapy.Field()
    img_brief = scrapy.Field()
    gongzhong_id = scrapy.Field() #
    read_num_24hours = scrapy.Field()
    like_num_24hours = scrapy.Field()
    update_time = scrapy.Field()
    create_time = scrapy.Field()
    category1 = scrapy.Field()
    category2 = scrapy.Field()
    category3 = scrapy.Field()
    city_id = scrapy.Field()
    content_html = scrapy.Field()
    weixin_name = scrapy.Field()
    page_source = scrapy.Field()
    pass
