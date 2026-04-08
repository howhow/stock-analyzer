#!/usr/bin/env python3
"""
Stock Analyzer - 股票分析统一入口

使用示例:
    python analyze.py 600276.SH
    python analyze.py 600276.SH --output markdown
    python analyze.py 600276.SH --output both --days 180
    python analyze.py 600276.SH --type technical
    python analyze.py 600276.SH --output-dir ./my-reports
"""

import argparse
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from app.data.data_fetcher import DataFetcher
from app.analysis.system import SystemAnalyzer
from app.analysis.indicators.trend import sma, macd
from app.analysis.indicators.momentum import rsi
from app.models.stock import StockInfo
from app.report.generator import ReportGenerator
from app.report.markdown_report import MarkdownReportGenerator
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Stock Analyzer - 股票分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python analyze.py 600276.SH                    # 分析恒瑞医药
    python analyze.py 600276.SH --output markdown  # 输出 Markdown 报告
    python analyze.py 600276.SH --output both      # 输出两种格式
    python analyze.py 600276.SH --days 180         # 分析最近180天数据
    python analyze.py 600276.SH --type technical   # 仅技术分析
        """,
    )
    
    parser.add_argument(
        "stock_code",
        help="股票代码，格式：600276.SH"
    )
    
    parser.add_argument(
        "--output",
        choices=["html", "markdown", "both"],
        default="html",
        help="输出格式（默认：html）"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=settings.analysis_days,
        help=f"分析天数（默认：{settings.analysis_days}）"
    )
    
    parser.add_argument(
        "--type",
        choices=["technical", "fundamental", "full"],
        default="full",
        help="分析类型（默认：full）"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./local_analyze_report"),
        help="输出目录（默认：./local_analyze_report）"
    )
    
    return parser.parse_args()


async def get_stock_info_safe(
    fetcher: DataFetcher,
    stock_code: str,
) -> StockInfo | None:
    """
    安全获取股票信息
    
    优先从数据源获取，如果失败则尝试构造基本信息
    """
    try:
        return await fetcher.get_stock_info(stock_code)
    except Exception as e:
        logger.warning("stock_info_fetch_failed", error=str(e))
        
        # 尝试从股票代码推断基本信息
        code, market = stock_code.split(".")
        market_name = {"SH": "上海证券交易所", "SZ": "深圳证券交易所"}.get(market, market)
        
        logger.info("using_inferred_stock_info", stock_code=stock_code)
        return StockInfo(
            code=stock_code,
            name=f"股票{code}",
            market=market,
            industry="未知",
        )


async def analyze_stock(args: argparse.Namespace) -> dict[str, Any] | None:
    """执行股票分析"""
    print(f"\n{'='*80}")
    print(f"📊 开始分析: {args.stock_code}")
    print(f"{'='*80}\n")
    
    # 1. 初始化
    fetcher = DataFetcher()
    
    try:
        # 2. 获取股票基本信息
        print("📌 [1/4] 获取股票基本信息...")
        stock_info = await get_stock_info_safe(fetcher, args.stock_code)
        
        if not stock_info:
            print(f"❌ 无法获取股票信息: {args.stock_code}")
            return None
        
        print(f"   ✅ {stock_info.name} ({stock_info.code})")
        print(f"   ✅ 行业: {stock_info.industry or '未知'}")
        print(f"   ✅ 市场: {stock_info.market}")
        
        # 3. 获取行情数据
        print(f"\n📈 [2/4] 获取行情数据（最近 {args.days} 天）...")
        end_date = date.today()
        start_date = end_date - timedelta(days=args.days)
        
        quotes = await fetcher.get_daily_quotes(
            args.stock_code, 
            start_date, 
            end_date
        )
        
        if not quotes:
            print(f"❌ 无法获取行情数据")
            return None
        
        print(f"   ✅ 获取到 {len(quotes)} 条日线数据")
        
        latest = quotes[-1]
        print(f"   ✅ 最新交易日: {latest.trade_date}")
        print(f"   ✅ 收盘价: {latest.close:.2f} 元")
        print(f"   ✅ 成交量: {latest.volume:.0f} 手")
        
        # 4. 获取财务数据（如果需要）
        financial = None
        if args.type in ["fundamental", "full"]:
            print(f"\n💰 [3/4] 获取财务数据...")
            try:
                financial = await fetcher.get_financial_data(args.stock_code)
                if financial:
                    print(f"   ✅ 报告日期: {financial.report_date}")
                    if financial.revenue:
                        print(f"   ✅ 营业收入: {financial.revenue/1e8:.2f} 亿元")
                    if financial.net_profit:
                        print(f"   ✅ 净利润: {financial.net_profit/1e8:.2f} 亿元")
                else:
                    print(f"   ⚠️  未获取到财务数据，将基于技术面分析")
            except Exception as e:
                print(f"   ⚠️  财务数据获取失败: {e}")
        else:
            print(f"\n💰 [3/4] 跳过财务数据（仅技术分析）")
        
        # 5. 执行分析
        print(f"\n🔍 [4/4] 执行综合分析...")
        analyzer = SystemAnalyzer()
        
        result = await analyzer.analyze(
            stock_info=stock_info,
            quotes=quotes,
            financial=financial,
            stock_code=args.stock_code,
        )
        
        # 将基本信息添加到 result.details 中（供报告生成器使用）
        result.details["stock_code"] = args.stock_code
        result.details["stock_name"] = stock_info.name
        result.details["stock_info"] = {
            "code": stock_info.code,
            "name": stock_info.name,
            "industry": stock_info.industry,
            "market": stock_info.market,
        }
        
        # 6. 生成报告
        output_dir = args.output_dir / args.stock_code
        output_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = date.today().strftime("%Y-%m-%d")
        generated_files = []
        
        if args.output in ["html", "both"]:
            print(f"\n📄 生成 HTML 报告...")
            html_generator = ReportGenerator()
            
            # 计算技术指标
            closes = [q.close for q in quotes]
            ma5_series = sma(closes, 5)
            ma20_series = sma(closes, 20)
            macd_data = macd(closes)
            rsi_series = rsi(closes, 14)
            
            # 准备图表数据（真实数据）
            chart_data = {
                "dates": [q.trade_date.strftime("%m-%d") for q in quotes],
                "kline": [[q.open, q.close, q.low, q.high] for q in quotes],
                "volume": [q.volume / 10000 for q in quotes],  # 转换为万手
                "support": result.details.get("support_levels", [quotes[-1].low])[0],
                "resistance": result.details.get("resistance_levels", [quotes[-1].high])[0],
                "ma5": ma5_series.tolist(),
                "ma20": ma20_series.tolist(),
                "macd": {
                    "dif": macd_data["macd"].tolist(),
                    "dea": macd_data["signal"].tolist(),
                    "histogram": macd_data["histogram"].tolist(),
                },
                "rsi": rsi_series.tolist(),
            }
            
            html_report = html_generator.generate(
                result,
                stock_code=args.stock_code,
                stock_name=stock_info.name,
                chart_data=chart_data,
            )
            html_file = output_dir / f"{args.stock_code}_{date_str}.html"
            html_file.write_text(html_report.content, encoding="utf-8")
            print(f"   ✅ HTML 报告: {html_file}")
            generated_files.append(str(html_file))
        
        if args.output in ["markdown", "both"]:
            print(f"\n📄 生成 Markdown 报告...")
            md_generator = MarkdownReportGenerator()
            md_report = md_generator.generate(
                result,
                stock_code=args.stock_code,
                stock_name=stock_info.name,
            )
            md_file = output_dir / f"{args.stock_code}_{date_str}.md"
            md_file.write_text(md_report, encoding="utf-8")
            print(f"   ✅ Markdown 报告: {md_file}")
            generated_files.append(str(md_file))
        
        # 7. 输出摘要
        print_summary(result, stock_info)
        
        return {
            "stock_code": args.stock_code,
            "stock_name": stock_info.name,
            "result": result,
            "files": generated_files,
        }
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        logger.error("analysis_failed", error=str(e), exc_info=True)
        return None
        
    finally:
        await fetcher.close()


def print_summary(result: Any, stock_info: StockInfo) -> None:
    """输出控制台摘要"""
    print(f"\n{'='*80}")
    print("📋 分析摘要")
    print(f"{'='*80}")
    print(f"股票: {stock_info.name} ({stock_info.code})")
    
    # 综合评分
    total_score = result.scores.get("total", 0)
    print(f"\n🎯 综合评分: {total_score:.1f}/100")
    
    # 详细评分
    if result.details:
        analyst_data = result.details.get("analyst", {})
        if analyst_data and "scores" in analyst_data:
            scores = analyst_data["scores"]
            if "fundamental" in scores:
                print(f"   • 基本面: {scores['fundamental']:.1f}")
            if "technical" in scores:
                print(f"   • 技术面: {scores['technical']:.1f}")
        
        trader_data = result.details.get("trader", {})
        if trader_data and "scores" in trader_data:
            scores = trader_data["scores"]
            if "signal_strength" in scores:
                print(f"   • 信号强度: {scores['signal_strength']:.1f}/5.0")
    
    # 投资建议
    recommendation = result.details.get("recommendation", "无")
    confidence = result.details.get("confidence", 0)
    print(f"\n💡 投资建议: {recommendation}")
    print(f"🎯 置信度: {confidence}%")
    
    # 信号
    if result.signals:
        print(f"\n📡 关键信号:")
        for signal in result.signals[:5]:
            print(f"   • {signal}")
    
    print(f"\n{'='*80}\n")


def main() -> int:
    """主入口"""
    args = parse_args()
    
    try:
        result = asyncio.run(analyze_stock(args))
        return 0 if result else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return 130
    except Exception as e:
        print(f"\n\n❌ 程序异常: {e}")
        logger.error("main_error", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
