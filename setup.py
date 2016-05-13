from setuptools import setup, find_packages

setup(
	name='sogou_weixin_wxpublic',
	version='1.0',
	packages=find_packages(),
	entry_points={'scrapy':['settings = sogou_weixin.settings']},
)
