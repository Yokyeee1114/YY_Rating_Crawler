# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import json
import sys
import os
from datetime import datetime

# 添加database目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))

try:
    from database.models import get_session, StockData, ResearchReport, FinancialNews

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("Warning: 数据库模块未找到，将只使用文件存储")


class FinancialDataPipeline:
    def __init__(self):
        self.file = None
        self.session = None

    def open_spider(self, spider):
        # 文件存储
        filename = f"{spider.name}_data.json"
        self.file = open(filename, 'w', encoding='utf-8')

        # 数据库存储
        if DATABASE_AVAILABLE:
            try:
                self.session = get_session()
                spider.logger.info("数据库连接成功")
            except Exception as e:
                spider.logger.error(f"数据库连接失败: {e}")
                self.session = None

    def close_spider(self, spider):
        if self.file:
            self.file.close()
        if self.session:
            self.session.close()

    def process_item(self, item, spider):
        # 添加爬取时间
        item['crawl_time'] = datetime.now().isoformat()

        # 文件存储（保持原有功能）
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)

        # 数据库存储（新增功能）
        if self.session:
            try:
                self._save_to_database(item, spider)
            except Exception as e:
                spider.logger.error(f"数据库保存失败: {e}")

        return item

    def _save_to_database(self, item, spider):
        item_dict = dict(item)

        # 根据item类型创建对应的数据库记录
        if 'symbol' in item_dict:  # 股票数据
            db_item = StockData(
                symbol=item_dict.get('symbol'),
                name=item_dict.get('name'),
                price=item_dict.get('price'),
                change=item_dict.get('change'),
                change_percent=item_dict.get('change_percent'),
                volume=item_dict.get('volume'),
                source_url=item_dict.get('source_url')
            )
        elif 'institution' in item_dict:  # 研究报告
            db_item = ResearchReport(
                title=item_dict.get('title'),
                author=item_dict.get('author'),
                institution=item_dict.get('institution'),
                publish_date=item_dict.get('publish_date'),
                report_type=item_dict.get('report_type'),
                rating=item_dict.get('rating'),
                target_price=item_dict.get('target_price'),
                summary=item_dict.get('summary'),
                source_url=item_dict.get('source_url')
            )
        elif 'category' in item_dict:  # 财经新闻
            keywords = item_dict.get('keywords', [])
            if isinstance(keywords, list):
                keywords = ','.join(keywords)

            db_item = FinancialNews(
                title=item_dict.get('title'),
                content=item_dict.get('content'),
                author=item_dict.get('author'),
                publish_time=item_dict.get('publish_time'),
                source=item_dict.get('source'),
                category=item_dict.get('category'),
                keywords=keywords,
                source_url=item_dict.get('source_url')
            )
        else:
            spider.logger.warning("未知的item类型，跳过数据库存储")
            return

        self.session.add(db_item)
        self.session.commit()
        spider.logger.info(f"数据已保存到数据库: {item_dict.get('title', item_dict.get('name', 'Unknown'))}")