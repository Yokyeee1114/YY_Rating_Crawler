import scrapy
import json
import re
from scrapy_project.items import StockDataItem


class EastmoneyApiSpider(scrapy.Spider):
    name = 'eastmoney_api'
    allowed_domains = ['push2.eastmoney.com', 'push2delay.eastmoney.com', 'quote.eastmoney.com']

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/center/gridlist.html',
            'X-Requested-With': 'XMLHttpRequest',
        }
    }

    def start_requests(self):
        """发起Ajax请求获取股票数据"""

        # 东方财富的股票列表API
        api_url = "https://push2.eastmoney.com/api/qt/clist/get"

        # API参数（基于网络分析得出）
        params = {
            'cb': f'jQuery{self.generate_callback_id()}',  # JSONP回调
            'pn': '1',  # 页码
            'pz': '50',  # 每页数量，先测试50条
            'po': '1',  # 排序
            'np': '1',  # 参数
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',  # 通用token
            'fltt': '2',  # 过滤类型
            'invt': '2',  # 投资类型
            'fid': 'f3',  # 排序字段(f3=涨跌幅)
            'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',  # 股票类型筛选
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
        }

        # 构造完整URL
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{api_url}?{param_str}"

        self.logger.info(f"请求API: {full_url}")

        yield scrapy.Request(
            url=full_url,
            callback=self.parse_api_response,
            headers=self.custom_settings['DEFAULT_REQUEST_HEADERS'],
            meta={'page': 1}
        )

    def generate_callback_id(self):
        """生成随机的JSONP回调ID"""
        import random
        import time
        timestamp = str(int(time.time() * 1000))
        random_num = str(random.randint(100000, 999999))
        return timestamp + '_' + random_num

    def parse_api_response(self, response):
        """解析API响应"""
        try:
            self.logger.info(f"API响应状态: {response.status}")
            self.logger.info(f"响应内容前200字符: {response.text[:200]}")

            # 处理JSONP响应，提取JSON部分
            json_text = response.text

            # 移除JSONP包装 jQuery123456789_1640000000000({...})
            if json_text.startswith('jQuery'):
                start = json_text.find('(') + 1
                end = json_text.rfind(')')
                json_text = json_text[start:end]

            # 解析JSON
            data = json.loads(json_text)
            self.logger.info(f"JSON解析成功，数据结构: {list(data.keys())}")

            # 检查数据结构
            if 'data' in data and data['data'] and 'diff' in data['data']:
                stock_list = data['data']['diff']
                self.logger.info(f"获取到 {len(stock_list)} 条股票数据")

                for stock_data in stock_list:
                    stock_item = self.parse_stock_data(stock_data, response)
                    if stock_item:
                        yield stock_item

                # 分页处理（如果需要更多数据）
                current_page = response.meta.get('page', 1)
                if len(stock_list) >= 50 and current_page < 3:  # 限制为前3页测试
                    yield from self.get_next_page(current_page + 1)

            else:
                self.logger.warning("API响应格式不符合预期")
                self.logger.info(f"响应数据: {data}")

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            self.logger.info(f"原始响应: {response.text[:500]}")
        except Exception as e:
            self.logger.error(f"解析API响应失败: {e}")

    def parse_stock_data(self, stock_data, response):
        """解析单个股票数据"""
        try:
            stock_item = StockDataItem()

            # 根据东方财富API字段映射（常见字段）
            stock_item['symbol'] = stock_data.get('f12', '')  # 股票代码
            stock_item['name'] = stock_data.get('f14', '')  # 股票名称
            stock_item['price'] = str(stock_data.get('f2', 0))  # 当前价
            stock_item['change'] = str(stock_data.get('f4', 0))  # 涨跌额
            stock_item['change_percent'] = str(stock_data.get('f3', 0))  # 涨跌幅
            stock_item['volume'] = str(stock_data.get('f5', 0))  # 成交量
            stock_item['source_url'] = response.url

            # 数据清洗和验证
            if stock_item['symbol'] and stock_item['name']:
                # 格式化涨跌幅（添加%符号）
                if stock_item['change_percent'] and stock_item['change_percent'] != '0':
                    try:
                        percent_val = float(stock_item['change_percent'])
                        stock_item['change_percent'] = f"{percent_val:.2f}%"
                    except:
                        pass

                # 格式化价格（保留两位小数）
                if stock_item['price'] and stock_item['price'] != '0':
                    try:
                        price_val = float(stock_item['price'])
                        stock_item['price'] = f"{price_val:.2f}"
                    except:
                        pass

                self.logger.info(f"解析股票: {stock_item['symbol']} - {stock_item['name']}")
                return stock_item
            else:
                self.logger.warning(f"股票数据不完整: {stock_data}")
                return None

        except Exception as e:
            self.logger.error(f"解析股票数据失败: {e}")
            return None

    def get_next_page(self, page_num):
        """获取下一页数据"""
        api_url = "https://push2.eastmoney.com/api/qt/clist/get"

        params = {
            'cb': f'jQuery{self.generate_callback_id()}',
            'pn': str(page_num),  # 页码
            'pz': '50',
            'po': '1',
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',
            'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
        }

        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{api_url}?{param_str}"

        self.logger.info(f"请求第{page_num}页数据")

        yield scrapy.Request(
            url=full_url,
            callback=self.parse_api_response,
            headers=self.custom_settings['DEFAULT_REQUEST_HEADERS'],
            meta={'page': page_num}
        )


# 简化版爬虫，用于快速测试API是否可用
class EastmoneyTestSpider(scrapy.Spider):
    name = 'eastmoney_test'

    def start_requests(self):
        # 简单的测试API
        test_url = "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery&pn=1&pz=5&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:0+t:6&fields=f12,f14,f2,f3,f4"

        yield scrapy.Request(
            url=test_url,
            callback=self.parse_test,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/'
            }
        )

    def parse_test(self, response):
        self.logger.info(f"测试响应状态: {response.status}")
        self.logger.info(f"响应内容: {response.text}")
        return {"test": "API测试完成"}