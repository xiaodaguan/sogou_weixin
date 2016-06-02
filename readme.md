#Readme  

## Quick Start   

(ubuntu为例)  

### 安装Scrapy  

- 安装python, pip(略)  

- 安装scrapy依赖  
`sudo apt-get install python-dev libxml2-dev libxslt1-dev`  
> 如果不安装会出现gcc编译错误   
> windows可能需要安装openssl, pywin32    

- 安装scrapy    
`sudo pip install scrapy`  
- 安装selenium  
`sudo pip install selenium`
- 安装pymongo  
`sudo pip install pymongo`  

### 无界面系统   
- 安装xvfb  
`sudo apt-get install xvfb`  

- 安装pyvirtualdisplay    
`sudo pip install pyvirtualdisplay`  
  
### 安装浏览器  
`sudo apt-get install firefox`  

### 下载  
`git clone https://github.com/xiaodaguan/sogou_weixin`  

### 配置&运行 
> 编辑spiders/sogou_weixin_paper or sogou_weixin_wxpublic,修改name,程序会以此作为mongodb的collection名字  
> 编辑settings.py, 修改SEARCH_KEYWORDS_FILE  

### 使用代理
添加到proxys.txt，每行一个  
编辑setting.py，修改：  
```
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    # customize
    # 'sogou_weixin.middlewares.RandomProxy': 100,
    # 'scrapy.contrib.downloadermiddleware.httpproxy.HttpProxyMiddleware': 110,
}
```
取消后两行的注释  

执行命令:  
`scrapy crawl {{上面spider中的name}}`  
or 运行python文件:  
`python entrypoint.py`(编辑其中命令同上)  






## todo  

分布式  

## 存在的问题  

~[x]程序正常退出后,浏览器不会自动关闭,如果长期运行会累积很多浏览器进程~
