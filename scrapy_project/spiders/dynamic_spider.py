# scrapy_project/spiders/dynamic_spider.py
import scrapy
import json
import sys
import os
from scrapy_project.items import StockDataItem, ResearchReportItem, FinancialNewsItem

# 添加数据库路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'database'))
from database.crawler_config import get_config_by_name


class DynamicSpider(scrapy.Spider):
    name = 'dynamic'

    def __init__(self, config_name=None, *args, **kwargs):
        super(DynamicSpider, self).__init__(*args, **kwargs)

        if not config_name:
            raise ValueError("必须提供config_name参数")

        # 从数据库加载配置
        self.config_obj = get_config_by_name(config_name)
        if not self.config_obj:
            raise ValueError(f"找不到配置: {config_name}")

        # 解析配置
        self.config = self.config_obj.get_config()
        self.logger.info(f"加载配置: {config_name}")

        # 应用配置到爬虫
        self._apply_config()

    def _apply_config(self):
        """应用配置到爬虫"""

        # 设置起始URL
        self.start_urls = self.config.get('start_urls', [])

        # 设置允许的域名
        if 'allowed_domains' in self.config:
            self.allowed_domains = self.config['allowed_domains']

        # 应用爬虫设置
        spider_settings = self.config.get('spider_settings', {})
        for key, value in spider_settings.items():
            setattr(self, key.upper(), value)

    def parse(self, response):
        """动态解析函数"""

        # 获取配置中的数据字段
        data_fields = self.config.get('data_fields', {})
        output_settings = self.config.get('output_settings', {})

        # 如果有列表选择器，先提取列表项
        item_selector = self.config.get('item_selector', {})
        if item_selector.get('list_selector'):
            items = response.css(item_selector['list_selector'])
            for item in items:
                yield from self._extract_data(item, data_fields, output_settings, response)
        else:
            # 直接从页面提取数据
            yield from self._extract_data(response, data_fields, output_settings, response)

        # 处理分页
        pagination = self.config.get('pagination', {})
        if pagination.get('enabled'):
            yield from self._handle_pagination(response, pagination)

    def _extract_data(self, selector, data_fields, output_settings, response):
        """提取数据"""

        # 根据输出类型选择Item类
        data_type = output_settings.get('data_type', 'stock_data')

        if data_type == 'stock_data':
            item = StockDataItem()
        elif data_type == 'research_report':
            item = ResearchReportItem()
        elif data_type == 'financial_news':
            item = FinancialNewsItem()
        else:
            item = StockDataItem()  # 默认

        # 提取各个字段
        extracted_data = {}
        for field_name, field_config in data_fields.items():
            value = self._extract_field(selector, field_config)
            if value is not None:
                extracted_data[field_name] = value

        # 检查必填字段
        required_fields = [name for name, config in data_fields.items() if config.get('required', False)]
        if all(extracted_data.get(field) for field in required_fields):
            # 填充item
            for field_name, value in extracted_data.items():
                #if hasattr(item, field_name):
                    item[field_name] = value

            # 添加源URL
            item['source_url'] = response.url

            self.logger.info(f"提取数据成功: {extracted_data}")
            yield item
        else:
            self.logger.warning(f"缺少必填字段，跳过数据: {extracted_data}")

    def _extract_field(self, selector, field_config):
        """提取单个字段"""
        css_selector = field_config.get('selector', '')
        field_type = field_config.get('type', 'string')
        regex_pattern = field_config.get('regex')

        try:
            # 使用CSS选择器提取
            if '::text' in css_selector:
                raw_value = selector.css(css_selector).get()
            elif '::attr(' in css_selector:
                raw_value = selector.css(css_selector).get()
            else:
                raw_value = selector.css(css_selector + '::text').get()

            if raw_value is None:
                return None

            # 清理文本
            cleaned_value = raw_value.strip()

            # 应用正则表达式
            if regex_pattern:
                import re
                match = re.search(regex_pattern, cleaned_value)
                if match:
                    cleaned_value = match.group(1) if match.groups() else match.group(0)
                else:
                    return None

            # 类型转换
            if field_type == 'float':
                return float(cleaned_value)
            elif field_type == 'int':
                return int(cleaned_value)
            else:
                return cleaned_value

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"字段提取失败 {css_selector}: {e}")
            return None

    def _handle_pagination(self, response, pagination):
        """处理分页"""
        next_page_selector = pagination.get('next_page_selector')
        max_pages = pagination.get('max_pages', 10)

        if next_page_selector:
            next_page_url = response.css(next_page_selector).get()
            if next_page_url:
                # 检查页数限制
                current_page = getattr(self, '_current_page', 1)
                if current_page < max_pages:
                    self._current_page = current_page + 1
                    yield response.follow(next_page_url, self.parse)