# database/test_query.py - 查询数据库数据
import sys
import os

sys.path.append(os.path.dirname(__file__))

from models import get_session, StockData, ResearchReport, FinancialNews


def test_database():
    """查询并显示数据库中的所有数据"""
    session = get_session()

    try:
        print("=" * 60)
        print("📊 金融数据库查询结果")
        print("=" * 60)

        # 查询股票数据
        stocks = session.query(StockData).order_by(StockData.crawl_time.desc()).all()
        print(f"\n📈 股票数据: {len(stocks)} 条")
        print("-" * 50)

        if stocks:
            print(f"{'股票代码':<12} {'股票名称':<15} {'当前价':<10} {'涨跌幅':<10} {'成交量':<15}")
            print("-" * 70)
            for stock in stocks:
                symbol = stock.symbol or "N/A"
                name = (stock.name[:12] + "..") if len(stock.name or "") > 12 else (stock.name or "N/A")
                price = stock.price or "N/A"
                change_pct = stock.change_percent or "N/A"
                volume = stock.volume or "N/A"
                print(f"{symbol:<12} {name:<15} {price:<10} {change_pct:<10} {volume:<15}")

        # 查询研究报告
        reports = session.query(ResearchReport).order_by(ResearchReport.crawl_time.desc()).all()
        print(f"\n📋 研究报告: {len(reports)} 条")
        print("-" * 50)

        if reports:
            for report in reports:
                print(f"标题: {report.title}")
                print(f"作者: {report.author} | 机构: {report.institution}")
                print(f"评级: {report.rating} | 发布日期: {report.publish_date}")
                print("-" * 30)

        # 查询财经新闻
        news = session.query(FinancialNews).order_by(FinancialNews.crawl_time.desc()).all()
        print(f"\n📰 财经新闻: {len(news)} 条")
        print("-" * 50)

        if news:
            for item in news:
                print(f"标题: {item.title}")
                print(f"作者: {item.author} | 来源: {item.source}")
                print(f"分类: {item.category} | 发布时间: {item.publish_time}")
                print("-" * 30)

        # 统计信息
        total_records = len(stocks) + len(reports) + len(news)
        print(f"\n📊 数据统计:")
        print(f"总记录数: {total_records}")
        print(f"  - 股票数据: {len(stocks)}")
        print(f"  - 研究报告: {len(reports)}")
        print(f"  - 财经新闻: {len(news)}")

        # 最新数据时间
        if stocks:
            latest_stock = stocks[0]
            print(f"\n⏰ 最新股票数据时间: {latest_stock.crawl_time}")

        print("=" * 60)
        print("✅ 数据库查询完成")

    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    test_database()

# database/compare_outputs.py - 对比文件和数据库输出
import json
import sys
import os

sys.path.append(os.path.dirname(__file__))

from models import get_session, StockData, ResearchReport, FinancialNews


def compare_file_and_database():
    """对比JSON文件和数据库中的数据"""

    # 查找JSON文件
    json_files = []
    for file in os.listdir('..'):
        if file.endswith('.json') and any(keyword in file for keyword in ['sina', 'stock', 'test']):
            json_files.append(file)

    if not json_files:
        print("❌ 未找到相关的JSON文件")
        return

    print("📁 找到以下JSON文件:")
    for i, file in enumerate(json_files):
        print(f"  {i + 1}. {file}")

    # 使用最新的文件
    latest_file = max(json_files, key=lambda x: os.path.getmtime(f"../{x}"))
    print(f"\n🔍 分析最新文件: {latest_file}")

    try:
        # 读取JSON文件数据
        with open(f'../{latest_file}', 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        print(f"📄 JSON文件记录数: {len(file_data)}")

        # 查询数据库数据
        session = get_session()
        try:
            db_stock_count = session.query(StockData).count()
            db_report_count = session.query(ResearchReport).count()
            db_news_count = session.query(FinancialNews).count()
            db_total = db_stock_count + db_report_count + db_news_count

            print(f"🗄️  数据库记录数: {db_total}")
            print(f"  - 股票: {db_stock_count}")
            print(f"  - 研报: {db_report_count}")
            print(f"  - 新闻: {db_news_count}")

            # 验证数据一致性
            if len(file_data) <= db_total:
                print("✅ 数据库包含了JSON文件的所有数据（可能有历史数据）")
            else:
                print("❌ JSON文件记录数大于数据库记录数")

            # 显示数据样本
            if file_data:
                print(f"\n🔍 JSON文件数据样本:")
                sample = file_data[0]
                for key, value in sample.items():
                    print(f"  {key}: {value}")

        except Exception as e:
            print(f"❌ 数据库查询失败: {e}")
        finally:
            session.close()

    except Exception as e:
        print(f"❌ 文件读取失败: {e}")


if __name__ == "__main__":
    compare_file_and_database()

# database/clean_db.py - 清理数据库
import sys
import os

sys.path.append(os.path.dirname(__file__))

from models import get_session, StockData, ResearchReport, FinancialNews


def clean_database():
    """清空数据库中的所有数据"""
    session = get_session()

    try:
        # 统计清理前的数据
        stock_count = session.query(StockData).count()
        report_count = session.query(ResearchReport).count()
        news_count = session.query(FinancialNews).count()
        total_count = stock_count + report_count + news_count

        print(f"📊 清理前数据统计:")
        print(f"  - 股票数据: {stock_count} 条")
        print(f"  - 研究报告: {report_count} 条")
        print(f"  - 财经新闻: {news_count} 条")
        print(f"  - 总计: {total_count} 条")

        if total_count == 0:
            print("✅ 数据库已经是空的")
            return

        # 确认清理
        confirm = input(f"\n⚠️  确定要清空所有 {total_count} 条数据吗？(y/N): ")
        if confirm.lower() != 'y':
            print("❌ 已取消清理操作")
            return

        # 删除所有数据
        session.query(StockData).delete()
        session.query(ResearchReport).delete()
        session.query(FinancialNews).delete()
        session.commit()

        print("✅ 数据库已清空")

    except Exception as e:
        print(f"❌ 清理失败: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    clean_database()

# database/export_data.py - 导出数据
import json
import csv
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from models import get_session, StockData, ResearchReport, FinancialNews


def export_to_json():
    """导出数据库数据到JSON文件"""
    session = get_session()

    try:
        # 获取所有数据
        stocks = session.query(StockData).all()
        reports = session.query(ResearchReport).all()
        news = session.query(FinancialNews).all()

        # 转换为字典
        data = {
            "export_time": datetime.now().isoformat(),
            "stock_data": [
                {
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "price": stock.price,
                    "change": stock.change,
                    "change_percent": stock.change_percent,
                    "volume": stock.volume,
                    "source_url": stock.source_url,
                    "crawl_time": stock.crawl_time.isoformat() if stock.crawl_time else None
                }
                for stock in stocks
            ],
            "research_reports": [
                {
                    "title": report.title,
                    "author": report.author,
                    "institution": report.institution,
                    "publish_date": report.publish_date,
                    "report_type": report.report_type,
                    "rating": report.rating,
                    "source_url": report.source_url,
                    "crawl_time": report.crawl_time.isoformat() if report.crawl_time else None
                }
                for report in reports
            ],
            "financial_news": [
                {
                    "title": news_item.title,
                    "content": news_item.content,
                    "author": news_item.author,
                    "source": news_item.source,
                    "category": news_item.category,
                    "source_url": news_item.source_url,
                    "crawl_time": news_item.crawl_time.isoformat() if news_item.crawl_time else None
                }
                for news_item in news
            ]
        }

        # 保存到文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"../database_export_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        total_records = len(stocks) + len(reports) + len(news)
        print(f"✅ 已导出 {total_records} 条记录到 {filename}")

    except Exception as e:
        print(f"❌ 导出失败: {e}")
    finally:
        session.close()


def export_stocks_to_csv():
    """导出股票数据到CSV文件"""
    session = get_session()

    try:
        stocks = session.query(StockData).order_by(StockData.crawl_time.desc()).all()

        if not stocks:
            print("❌ 没有股票数据可导出")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"../stocks_export_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # 写入表头
            writer.writerow(['股票代码', '股票名称', '当前价', '涨跌额', '涨跌幅', '成交量', '爬取时间'])

            # 写入数据
            for stock in stocks:
                writer.writerow([
                    stock.symbol,
                    stock.name,
                    stock.price,
                    stock.change,
                    stock.change_percent,
                    stock.volume,
                    stock.crawl_time.strftime('%Y-%m-%d %H:%M:%S') if stock.crawl_time else ''
                ])

        print(f"✅ 已导出 {len(stocks)} 条股票数据到 {filename}")

    except Exception as e:
        print(f"❌ 导出失败: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("1. 导出到JSON")
    print("2. 导出股票数据到CSV")
    choice = input("请选择导出方式 (1/2): ")

    if choice == "1":
        export_to_json()
    elif choice == "2":
        export_stocks_to_csv()
    else:
        print("❌ 无效选择")