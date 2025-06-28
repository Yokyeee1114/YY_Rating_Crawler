# database/crawler_config.py - 爬虫配置数据库模型
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

# 使用与models.py相同的Base
import sys
import os

sys.path.append(os.path.dirname(__file__))
from models import Base, get_session


class CrawlerConfig(Base):
    """爬虫配置表"""
    __tablename__ = 'crawler_configs'

    # 基础信息
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)  # 配置名称
    description = Column(Text)  # 配置描述
    website_name = Column(String(100), nullable=False)  # 目标网站名称

    # 配置内容 (JSON格式存储)
    config_json = Column(Text, nullable=False)  # 完整的爬虫配置

    # 状态管理
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run_at = Column(DateTime)  # 最后运行时间

    # 统计信息
    run_count = Column(Integer, default=0)  # 运行次数
    success_count = Column(Integer, default=0)  # 成功次数

    def get_config(self):
        """获取解析后的配置对象"""
        try:
            return json.loads(self.config_json)
        except json.JSONDecodeError:
            return {}

    def set_config(self, config_dict):
        """设置配置对象"""
        self.config_json = json.dumps(config_dict, ensure_ascii=False, indent=2)

    def validate_config(self):
        """验证配置是否有效"""
        config = self.get_config()
        required_fields = ['start_urls', 'data_fields']

        for field in required_fields:
            if field not in config:
                return False, f"缺少必要字段: {field}"

        if not isinstance(config['start_urls'], list) or not config['start_urls']:
            return False, "start_urls必须是非空列表"

        if not isinstance(config['data_fields'], dict):
            return False, "data_fields必须是字典格式"

        return True, "配置有效"


# 标准配置模板
DEFAULT_CONFIG_TEMPLATE = {
    "spider_settings": {
        "download_delay": 1,
        "randomize_download_delay": 0.5,
        "concurrent_requests": 16,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    "start_urls": [
        "https://example.com/data"
    ],
    "allowed_domains": [
        "example.com"
    ],
    "data_fields": {
        "title": {
            "selector": "h1.title::text",
            "type": "string",
            "required": True
        },
        "price": {
            "selector": ".price::text",
            "type": "float",
            "required": True,
            "regex": r"[\d\.]+"
        },
        "description": {
            "selector": ".description::text",
            "type": "string",
            "required": False
        }
    },
    "pagination": {
        "enabled": False,
        "next_page_selector": ".next-page::attr(href)",
        "max_pages": 10
    },
    "item_selector": {
        "list_selector": ".item-list .item",
        "detail_url_selector": "a::attr(href)"
    },
    "data_processing": {
        "remove_duplicates": True,
        "clean_text": True,
        "validate_data": True
    },
    "output_settings": {
        "data_type": "stock_data",  # stock_data, research_report, financial_news
        "save_to_database": True,
        "save_to_file": False
    }
}


def create_config_table():
    """创建配置表"""
    from models import get_engine
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("爬虫配置表创建完成")


def get_config_by_name(name):
    """根据名称获取配置"""
    session = get_session()
    try:
        config = session.query(CrawlerConfig).filter(CrawlerConfig.name == name).first()
        return config
    finally:
        session.close()


def create_default_config():
    """创建默认配置示例"""
    session = get_session()
    try:
        # 检查是否已存在示例配置
        existing = session.query(CrawlerConfig).filter(CrawlerConfig.name == "示例配置").first()
        if existing:
            print("示例配置已存在")
            return existing

        # 创建示例配置
        config = CrawlerConfig(
            name="示例配置",
            description="这是一个配置模板示例，展示如何配置爬虫规则",
            website_name="示例网站",
            config_json=json.dumps(DEFAULT_CONFIG_TEMPLATE, ensure_ascii=False, indent=2),
            is_active=False
        )

        session.add(config)
        session.commit()
        print("示例配置创建成功")
        return config

    except Exception as e:
        session.rollback()
        print(f"创建示例配置失败: {e}")
        return None
    finally:
        session.close()


if __name__ == "__main__":
    create_config_table()
    create_default_config()