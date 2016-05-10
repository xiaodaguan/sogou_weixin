# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import hashlib

import pymongo
from scrapy.exceptions import DropItem
import logging

logger = logging.getLogger('my_pipelines')

class SogouPipeline(object):
    def __init__(self, mongo_uri, mongo_db, spider_name):

        self.mongodb_url = mongo_uri
        self.mongodb_db_name = mongo_db
        self.mongodb_collection_name = '%s_info' % spider_name

        mongo_uri = "mongodb://%s" % mongo_uri
        connection = pymongo.MongoClient(mongo_uri)
        db = connection[mongo_db]

        # self.collection = db['wechat_article_info']
        self.collection = db[self.mongodb_collection_name]
        # item crawled before
        logger.info("loading crawled items before...")
        self.item_crawled = set()
        pipeline = [
            {
                "$group": {
                    "_id": "$md5", "count": {"$sum": 1}
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        for i, item in enumerate(result):
            self.item_crawled.add(item['_id'])
            if i % 1000 == 0: print(i)
        logger.info("pipline read %d crawled items" % len(result))

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGODB_ADDRESS'),
            mongo_db=crawler.settings.get('MONGODB_DB'),
            spider_name=crawler.spidercls.name
        )

    def process_item(self, item, spider):

        if not item['md5']:

            md5 = hashlib.md5("%s%s%s"%(item['title'].encode('utf-8'),item['pubtime'].encode('utf-8'),item['weixin_name'].encode('utf-8'))).hexdigest()
            item['md5'] = md5

        valid = True

        if item['md5'] in self.item_crawled:
            valid = False
            DropItem("item crawled before %s " % item['title'])
        else:
            valid = True

        if item['url'].find("mp.weixin.qq.com") > -1:
            valid = True
        else:
            valid = False

        if valid:
            self.collection.insert(dict(item))
            self.item_crawled.add(item['md5'])
            logger.info("item: %s (kw:%s) wrote to mongodb %s / %s" % ( item['title'],item['search_keyword'],self.mongodb_db_name, self.mongodb_collection_name,))
        else:
            logger.info("item droped %s " % item['title'])
        return item
