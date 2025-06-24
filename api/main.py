# api/main.py - FastAPI主应用
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os
import subprocess

# 添加数据库路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))

from database.models import get_session, StockData, ResearchReport, FinancialNews
from pydantic import BaseModel

# 创建FastAPI应用
app = FastAPI(
    title="金融数据爬虫API",
    description="提供股票数据、研究报告和财经新闻的REST API接口",
    version="1.0.0"
)

# 添加CORS中间件，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic模型用于API响应
class StockDataResponse(BaseModel):
    id: int
    symbol: str
    name: str
    price: Optional[str]
    change: Optional[str]
    change_percent: Optional[str]
    volume: Optional[str]
    source_url: Optional[str]
    crawl_time: Optional[datetime]

    class Config:
        from_attributes = True


class ResearchReportResponse(BaseModel):
    id: int
    title: str
    author: Optional[str]
    institution: Optional[str]
    publish_date: Optional[str]
    report_type: Optional[str]
    rating: Optional[str]
    summary: Optional[str]
    source_url: Optional[str]
    crawl_time: Optional[datetime]

    class Config:
        from_attributes = True


class FinancialNewsResponse(BaseModel):
    id: int
    title: str
    content: Optional[str]
    author: Optional[str]
    source: Optional[str]
    category: Optional[str]
    source_url: Optional[str]
    crawl_time: Optional[datetime]

    class Config:
        from_attributes = True


class SystemStatsResponse(BaseModel):
    total_stocks: int
    total_reports: int
    total_news: int
    last_update: Optional[datetime]


# 依赖项：获取数据库会话
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


# 根路径
@app.get("/", tags=["系统"])
async def root():
    return {
        "message": "金融数据爬虫API",
        "version": "1.0.0",
        "status": "运行中",
        "docs": "/docs",
        "api_endpoints": {
            "stocks": "/api/stocks",
            "reports": "/api/reports",
            "news": "/api/news",
            "stats": "/api/stats"
        }
    }

# 系统状态
@app.get("/api/stats", response_model=SystemStatsResponse, tags=["系统"])
async def get_system_stats(db: Session = Depends(get_db)):
    """获取系统统计信息"""
    try:
        total_stocks = db.query(StockData).count()
        total_reports = db.query(ResearchReport).count()
        total_news = db.query(FinancialNews).count()

        # 获取最新更新时间
        latest_stock = db.query(StockData).order_by(StockData.crawl_time.desc()).first()
        last_update = latest_stock.crawl_time if latest_stock else None

        return SystemStatsResponse(
            total_stocks=total_stocks,
            total_reports=total_reports,
            total_news=total_news,
            last_update=last_update
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# 股票数据API
@app.get("/api/stocks", response_model=List[StockDataResponse], tags=["股票数据"])
async def get_stocks(
        skip: int = Query(0, ge=0, description="跳过的记录数"),
        limit: int = Query(20, ge=1, le=100, description="返回的记录数，最大100"),
        symbol: Optional[str] = Query(None, description="按股票代码筛选"),
        name_contains: Optional[str] = Query(None, description="按股票名称模糊搜索"),
        sort_by: str = Query("crawl_time", description="排序字段"),
        order: str = Query("desc", description="排序方向 (asc/desc)"),
        db: Session = Depends(get_db)
):
    """获取股票数据列表"""
    try:
        query = db.query(StockData)

        # 筛选条件
        if symbol:
            query = query.filter(StockData.symbol.ilike(f"%{symbol}%"))

        if name_contains:
            query = query.filter(StockData.name.ilike(f"%{name_contains}%"))

        # 排序
        if hasattr(StockData, sort_by):
            order_column = getattr(StockData, sort_by)
            if order.lower() == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # 分页
        stocks = query.offset(skip).limit(limit).all()

        return stocks

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票数据失败: {str(e)}")


# 单个股票详情
@app.get("/api/stocks/{stock_id}", response_model=StockDataResponse, tags=["股票数据"])
async def get_stock_detail(stock_id: int, db: Session = Depends(get_db)):
    """获取单个股票的详细信息"""
    stock = db.query(StockData).filter(StockData.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票数据不存在")
    return stock


# 研究报告API
@app.get("/api/reports", response_model=List[ResearchReportResponse], tags=["研究报告"])
async def get_research_reports(
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        institution: Optional[str] = Query(None, description="按机构筛选"),
        rating: Optional[str] = Query(None, description="按评级筛选"),
        db: Session = Depends(get_db)
):
    """获取研究报告列表"""
    try:
        query = db.query(ResearchReport)

        if institution:
            query = query.filter(ResearchReport.institution.ilike(f"%{institution}%"))

        if rating:
            query = query.filter(ResearchReport.rating.ilike(f"%{rating}%"))

        reports = query.order_by(ResearchReport.crawl_time.desc()).offset(skip).limit(limit).all()
        return reports

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取研究报告失败: {str(e)}")


# 财经新闻API
@app.get("/api/news", response_model=List[FinancialNewsResponse], tags=["财经新闻"])
async def get_financial_news(
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        category: Optional[str] = Query(None, description="按分类筛选"),
        source: Optional[str] = Query(None, description="按来源筛选"),
        db: Session = Depends(get_db)
):
    """获取财经新闻列表"""
    try:
        query = db.query(FinancialNews)

        if category:
            query = query.filter(FinancialNews.category.ilike(f"%{category}%"))

        if source:
            query = query.filter(FinancialNews.source.ilike(f"%{source}%"))

        news = query.order_by(FinancialNews.crawl_time.desc()).offset(skip).limit(limit).all()
        return news

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取财经新闻失败: {str(e)}")


# 搜索API
@app.get("/api/search", tags=["搜索"])
async def search_all(
        q: str = Query(..., description="搜索关键词"),
        limit: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db)
):
    """全局搜索股票、报告和新闻"""
    try:
        results = {
            "stocks": [],
            "reports": [],
            "news": []
        }

        # 搜索股票
        stocks = db.query(StockData).filter(
            StockData.name.ilike(f"%{q}%") |
            StockData.symbol.ilike(f"%{q}%")
        ).limit(limit).all()
        results["stocks"] = [StockDataResponse.from_orm(s) for s in stocks]

        # 搜索报告
        reports = db.query(ResearchReport).filter(
            ResearchReport.title.ilike(f"%{q}%") |
            ResearchReport.author.ilike(f"%{q}%") |
            ResearchReport.institution.ilike(f"%{q}%")
        ).limit(limit).all()
        results["reports"] = [ResearchReportResponse.from_orm(r) for r in reports]

        # 搜索新闻
        news = db.query(FinancialNews).filter(
            FinancialNews.title.ilike(f"%{q}%") |
            FinancialNews.content.ilike(f"%{q}%")
        ).limit(limit).all()
        results["news"] = [FinancialNewsResponse.from_orm(n) for n in news]

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


# 爬虫控制API
@app.post("/api/crawl/start", tags=["爬虫控制"])
async def start_crawling(
        spider_name: str = Query("sina_stock", description="爬虫名称"),
        background_tasks: BackgroundTasks = BackgroundTasks()
):
    """启动爬虫任务"""
    try:
        # 在后台启动爬虫
        background_tasks.add_task(run_spider, spider_name)

        return {
            "message": f"爬虫 {spider_name} 已启动",
            "spider_name": spider_name,
            "status": "started",
            "start_time": datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动爬虫失败: {str(e)}")


def run_spider(spider_name: str):
    """后台运行爬虫"""
    try:
        # 切换到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 运行爬虫
        result = subprocess.run([
            'scrapy', 'crawl', spider_name,
            '-s', 'CLOSESPIDER_ITEMCOUNT=20'
        ], cwd=project_root, capture_output=True, text=True)

        print(f"爬虫 {spider_name} 执行完成，返回码: {result.returncode}")
        if result.stdout:
            print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")

    except Exception as e:
        print(f"运行爬虫失败: {e}")


# 数据统计API
@app.get("/api/analytics/top-stocks", tags=["数据分析"])
async def get_top_stocks(
        limit: int = Query(10, ge=1, le=50),
        sort_by: str = Query("change_percent", description="排序字段：change_percent, volume"),
        db: Session = Depends(get_db)
):
    """获取涨幅榜或成交量榜"""
    try:
        query = db.query(StockData)

        if sort_by == "change_percent":
            # 按涨跌幅排序（需要处理字符串格式）
            stocks = query.order_by(StockData.crawl_time.desc()).limit(100).all()
            # 手动排序涨跌幅
            sorted_stocks = sorted(stocks, key=lambda x: float(
                x.change_percent.replace('%', '')) if x.change_percent and x.change_percent.replace('%', '').replace(
                '+', '').replace('-', '').replace('.', '').isdigit() else 0, reverse=True)
            return sorted_stocks[:limit]
        elif sort_by == "volume":
            # 按成交量排序
            stocks = query.order_by(StockData.crawl_time.desc()).limit(100).all()
            sorted_stocks = sorted(stocks, key=lambda x: int(x.volume) if x.volume and x.volume.isdigit() else 0,
                                   reverse=True)
            return sorted_stocks[:limit]
        else:
            # 默认按时间排序
            return query.order_by(StockData.crawl_time.desc()).limit(limit).all()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排行榜失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)