import scrapy
import json
from scrapy_project.items import StockDataItem


class EastmoneySpider(scrapy.Spider):
    name = 'eastmoney'
    allowed_domains = ['quote.eastmoney.com']

    # 使用基础URL，避免fragments问题
    start_urls = [
        'https://quote.eastmoney.com/center/gridlist.html'
    ]

    # 设置自定义headers，模拟真实浏览器
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 1,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.eastmoney.com/',
        }
    }

    def parse(self, response):
        self.logger.info(f"开始解析页面: {response.url}")

        # 方法1: 尝试表格结构（常见的股票列表格式）
        stock_rows = response.css('table tr')
        self.logger.info(f"找到表格行数: {len(stock_rows)}")

        if len(stock_rows) > 1:  # 如果有表格数据
            for row in stock_rows[1:]:  # 跳过表头
                yield from self.parse_table_row(row, response)

        # 方法2: 尝试div结构
        stock_divs = response.css('div[class*="stock"], div[class*="item"]')
        self.logger.info(f"找到股票div数: {len(stock_divs)}")

        for div in stock_divs:
            yield from self.parse_div_item(div, response)

        # 方法3: 如果是动态加载，查找Ajax接口
        self.logger.info("正在检查是否有Ajax数据加载...")
        scripts = response.css('script::text').getall()
        for script in scripts:
            if 'ajax' in script.lower() or 'json' in script.lower():
                self.logger.info("发现可能的Ajax调用")
                # 这里可以提取Ajax URL进行进一步请求

    def parse_table_row(self, row, response):
        """解析表格行中的股票数据"""
        cells = row.css('td')

        if len(cells) >= 6:  # 确保有足够的列
            try:
                stock_item = StockDataItem()

                # 根据常见的东方财富表格结构调整
                stock_item['symbol'] = self.extract_text(cells[0])  # 股票代码
                stock_item['name'] = self.extract_text(cells[1])  # 股票名称
                stock_item['price'] = self.extract_text(cells[2])  # 当前价
                stock_item['change'] = self.extract_text(cells[3])  # 涨跌额
                stock_item['change_percent'] = self.extract_text(cells[4])  # 涨跌幅
                stock_item['volume'] = self.extract_text(cells[5])  # 成交量
                stock_item['source_url'] = response.url

                # 只有当有效数据时才yield
                if stock_item['symbol'] and stock_item['name']:
                    yield stock_item

            except Exception as e:
                self.logger.error(f"解析表格行失败: {e}")

    def parse_div_item(self, div, response):
        """解析div结构中的股票数据"""
        try:
            stock_item = StockDataItem()

            # 根据实际的div结构调整选择器
            stock_item['symbol'] = div.css('.symbol, .code::text').get()
            stock_item['name'] = div.css('.name, .stock-name::text').get()
            stock_item['price'] = div.css('.price, .current-price::text').get()
            stock_item['change'] = div.css('.change::text').get()
            stock_item['change_percent'] = div.css('.change-percent, .percent::text').get()
            stock_item['volume'] = div.css('.volume::text').get()
            stock_item['source_url'] = response.url

            # 只有当有效数据时才yield
            if stock_item['symbol'] and stock_item['name']:
                yield stock_item

        except Exception as e:
            self.logger.error(f"解析div项失败: {e}")

    def extract_text(self, cell):
        """安全地提取单元格文本"""
        if cell:
            text = cell.css('::text').get()
            if text:
                return text.strip()
        return None


# 调试专用爬虫 - 用于分析页面结构
class EastmoneyDebugSpider(scrapy.Spider):
    name = 'eastmoney_debug'
    allowed_domains = ['quote.eastmoney.com']
    start_urls = ['https://quote.eastmoney.com/center/gridlist.html']

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }

    def parse(self, response):
        """专门用于调试和分析页面结构"""

        # 保存页面HTML用于分析
        with open('eastmoney_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)

        self.logger.info("=== 页面结构分析 ===")

        # 分析表格结构
        tables = response.css('table')
        self.logger.info(f"发现 {len(tables)} 个表格")

        for i, table in enumerate(tables):
            rows = table.css('tr')
            self.logger.info(f"表格 {i + 1}: {len(rows)} 行")

            if len(rows) > 0:
                first_row = rows[0]
                columns = first_row.css('td, th')
                self.logger.info(f"表格 {i + 1} 第一行有 {len(columns)} 列")

                # 显示前几列的内容
                for j, col in enumerate(columns[:8]):
                    text = col.css('::text').get()
                    self.logger.info(f"  列 {j + 1}: {text}")

        # 分析其他可能的结构
        divs_with_class = response.css('div[class]')
        self.logger.info(f"带class的div数量: {len(divs_with_class)}")

        # 查找包含数字的元素（可能是价格）
        price_like = response.css('*:contains(".")::text').re(r'\d+\.\d+')
        self.logger.info(f"发现疑似价格数据: {price_like[:10]}")  # 只显示前10个

        return {"analysis": "页面结构分析完成，请查看日志"}