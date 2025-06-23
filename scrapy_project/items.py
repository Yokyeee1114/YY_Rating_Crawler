# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose
from w3lib.html import remove_tags

class StockDataItem(scrapy.Item):
    # 基础信息
    symbol = scrapy.Field()      # 股票代码
    name = scrapy.Field()        # 股票名称
    price = scrapy.Field()       # 当前价格
    change = scrapy.Field()      # 涨跌额
    change_percent = scrapy.Field()  # 涨跌幅
    volume = scrapy.Field()      # 成交量
    source_url = scrapy.Field()  # 数据来源
    crawl_time = scrapy.Field()  # 爬取时间

class ResearchReportItem(scrapy.Item):
    # 报告基础信息
    title = scrapy.Field()       # 报告标题
    author = scrapy.Field()      # 分析师
    institution = scrapy.Field() # 机构名称
    publish_date = scrapy.Field() # 发布日期
    report_type = scrapy.Field() # 报告类型
    rating = scrapy.Field()      # 评级
    target_price = scrapy.Field() # 目标价
    summary = scrapy.Field()     # 摘要
    source_url = scrapy.Field()  # 来源链接
    crawl_time = scrapy.Field()  # 爬取时间

class FinancialNewsItem(scrapy.Item):
    # 新闻基础信息
    title = scrapy.Field()       # 新闻标题
    content = scrapy.Field()     # 新闻内容
    author = scrapy.Field()      # 作者
    publish_time = scrapy.Field() # 发布时间
    source = scrapy.Field()      # 新闻来源
    category = scrapy.Field()    # 新闻分类
    keywords = scrapy.Field()    # 关键词
    source_url = scrapy.Field()  # 原文链接
    crawl_time = scrapy.Field()  # 爬取时间