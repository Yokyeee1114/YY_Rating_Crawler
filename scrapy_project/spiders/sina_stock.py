import scrapy
import json
import re
from scrapy_project.items import StockDataItem


class SinaStockSpider(scrapy.Spider):
    name = 'sina_stock'
    allowed_domains = ['finance.sina.com.cn', 'hq.sinajs.cn']

    # 新浪财经的股票数据相对开放，适合学习
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'ROBOTSTXT_OBEY': True,  # 遵守robots.txt
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://finance.sina.com.cn/',
        }
    }

    def start_requests(self):
        """使用新浪财经的股票数据接口"""

        # 新浪财经的股票数据API（常用股票代码）
        stock_codes = [
            'sh000001',  # 上证指数
            'sz399001',  # 深证成指
            'sh600036',  # 招商银行
            'sh600519',  # 贵州茅台
            'sh600000',  # 浦发银行
            'sz000002',  # 万科A
            'sz000001',  # 平安银行
            'sh600276',  # 恒瑞医药
            'sh600887',  # 伊利股份
            'sz002415',  # 海康威视
        ]

        # 新浪股票数据API格式
        codes_param = ','.join(stock_codes)
        api_url = f"https://hq.sinajs.cn/list={codes_param}"

        self.logger.info(f"请求新浪财经API: {api_url}")

        yield scrapy.Request(
            url=api_url,
            callback=self.parse_sina_response,
            headers=self.custom_settings['DEFAULT_REQUEST_HEADERS']
        )

    def parse_sina_response(self, response):
        """解析新浪财经API响应"""
        try:
            self.logger.info(f"新浪API响应状态: {response.status}")
            self.logger.info(f"响应内容前500字符: {response.text[:500]}")

            # 新浪返回的是JavaScript变量赋值格式
            lines = response.text.strip().split('\n')

            for line in lines:
                if 'var hq_str_' in line:
                    stock_item = self.parse_sina_stock_line(line, response)
                    if stock_item:
                        yield stock_item

        except Exception as e:
            self.logger.error(f"解析新浪响应失败: {e}")

    def parse_sina_stock_line(self, line, response):
        """解析单行新浪股票数据"""
        try:
            # 解析格式: var hq_str_sh600036="招商银行,37.34,37.38,37.71,38.00,37.30,37.71,37.72,..."

            # 提取股票代码
            code_match = re.search(r'hq_str_(\w+)', line)
            if not code_match:
                return None

            stock_code = code_match.group(1)

            # 提取数据部分
            data_match = re.search(r'"([^"]+)"', line)
            if not data_match:
                return None

            data_str = data_match.group(1)
            data_parts = data_str.split(',')

            if len(data_parts) < 6:
                self.logger.warning(f"数据不完整: {stock_code}")
                return None

            # 创建股票数据项
            stock_item = StockDataItem()

            stock_item['symbol'] = stock_code
            stock_item['name'] = data_parts[0]  # 股票名称
            stock_item['price'] = data_parts[3]  # 当前价

            # 计算涨跌额和涨跌幅
            try:
                current_price = float(data_parts[3])  # 当前价
                prev_close = float(data_parts[2])  # 昨收价

                change = current_price - prev_close  # 涨跌额
                change_percent = (change / prev_close) * 100 if prev_close > 0 else 0  # 涨跌幅

                stock_item['change'] = f"{change:+.2f}"  # 带正负号
                stock_item['change_percent'] = f"{change_percent:+.2f}%"

            except (ValueError, IndexError):
                stock_item['change'] = "0.00"
                stock_item['change_percent'] = "0.00%"

            # 成交量（如果有的话）
            stock_item['volume'] = data_parts[8] if len(data_parts) > 8 else "0"
            stock_item['source_url'] = response.url

            self.logger.info(f"解析股票成功: {stock_item['symbol']} - {stock_item['name']} - {stock_item['price']}")
            return stock_item

        except Exception as e:
            self.logger.error(f"解析股票行失败: {e} - {line[:100]}")
            return None


# 网易财经爬虫 - 另一个选择
class NeteaseStockSpider(scrapy.Spider):
    name = 'netease_stock'
    allowed_domains = ['money.163.com']

    start_urls = [
        'https://money.163.com/stock/gszl/',  # 网易财经股市资料
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'ROBOTSTXT_OBEY': True,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://money.163.com/',
        }
    }

    def parse(self, response):
        """解析网易财经股票页面"""
        self.logger.info(f"开始解析网易财经页面: {response.url}")

        # 查找股票表格
        stock_tables = response.css('table')
        self.logger.info(f"找到 {len(stock_tables)} 个表格")

        for table in stock_tables:
            rows = table.css('tr')

            for row in rows[1:]:  # 跳过表头
                cells = row.css('td')

                if len(cells) >= 4:
                    try:
                        stock_item = StockDataItem()

                        stock_item['name'] = cells[0].css('::text').get()
                        stock_item['symbol'] = cells[1].css('::text').get()
                        stock_item['price'] = cells[2].css('::text').get()
                        stock_item['change_percent'] = cells[3].css('::text').get()
                        stock_item['source_url'] = response.url

                        if stock_item['name'] and stock_item['symbol']:
                            yield stock_item

                    except Exception as e:
                        self.logger.error(f"解析网易股票行失败: {e}")


# 雪球股票爬虫 - 第三个选择
class XueqiuStockSpider(scrapy.Spider):
    name = 'xueqiu_stock'
    allowed_domains = ['xueqiu.com']

    start_urls = [
        'https://xueqiu.com/hq/screener',
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'ROBOTSTXT_OBEY': True,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://xueqiu.com/',
        }
    }

    def parse(self, response):
        """解析雪球股票筛选页面"""
        self.logger.info(f"开始解析雪球页面: {response.url}")

        # 雪球通常使用动态加载，这里主要是测试页面访问
        self.logger.info(f"页面标题: {response.css('title::text').get()}")

        # 查找可能的股票数据
        stock_elements = response.css('div[class*="stock"], tr[class*="table"]')
        self.logger.info(f"找到可能的股票元素: {len(stock_elements)}")

        return {"analysis": "雪球页面分析完成"}