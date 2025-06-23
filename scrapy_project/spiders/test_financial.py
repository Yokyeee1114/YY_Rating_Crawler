import scrapy
from scrapy_project.items import StockDataItem, ResearchReportItem, FinancialNewsItem


class TestFinancialSpider(scrapy.Spider):
    name = 'test_financial'
    start_urls = ['http://quotes.toscrape.com/']

    def parse(self, response):
        # 测试股票数据
        stock_item = StockDataItem()
        stock_item['symbol'] = 'AAPL'
        stock_item['name'] = '苹果公司'
        stock_item['price'] = '150.25'
        stock_item['change'] = '+2.15'
        stock_item['change_percent'] = '+1.45%'
        stock_item['volume'] = '1000000'
        stock_item['source_url'] = response.url
        yield stock_item

        # 测试研究报告
        report_item = ResearchReportItem()
        report_item['title'] = '苹果公司投资分析'
        report_item['author'] = '分析师张三'
        report_item['institution'] = '测试证券'
        report_item['publish_date'] = '2024-06-20'
        report_item['report_type'] = '买入'
        report_item['source_url'] = response.url
        yield report_item

        # 测试财经新闻
        news_item = FinancialNewsItem()
        news_item['title'] = '科技股上涨'
        news_item['content'] = '今日科技股表现强劲...'
        news_item['author'] = '财经记者'
        news_item['source'] = '测试财经'
        news_item['category'] = '股市'
        news_item['source_url'] = response.url
        yield news_item

        self.logger.info('已生成3条测试数据')