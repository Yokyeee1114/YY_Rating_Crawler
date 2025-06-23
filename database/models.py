from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class StockData(Base):
    __tablename__ = 'stock_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    price = Column(String(20))
    change = Column(String(20))
    change_percent = Column(String(20))
    volume = Column(String(50))
    source_url = Column(String(500))
    crawl_time = Column(DateTime, default=datetime.utcnow)


class ResearchReport(Base):
    __tablename__ = 'research_reports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    author = Column(String(100))
    institution = Column(String(100))
    publish_date = Column(String(50))
    report_type = Column(String(50))
    rating = Column(String(20))
    target_price = Column(String(20))
    summary = Column(Text)
    source_url = Column(String(500))
    crawl_time = Column(DateTime, default=datetime.utcnow)


class FinancialNews(Base):
    __tablename__ = 'financial_news'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    content = Column(Text)
    author = Column(String(100))
    publish_time = Column(String(50))
    source = Column(String(100))
    category = Column(String(50))
    keywords = Column(Text)  # 存储为字符串，用逗号分隔
    source_url = Column(String(500))
    crawl_time = Column(DateTime, default=datetime.utcnow)


# 获取项目根目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'financial_data.db')}"
# 数据库连接配置，避免文件夹问题
#DATABASE_URL = "sqlite:///./financial_data.db"


def get_engine():
    return create_engine(DATABASE_URL, echo=True)


def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_tables():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")