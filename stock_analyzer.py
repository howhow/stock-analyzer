#!/root/dev_work/stock-analyzer/local_venv/bin/python3
"""
Stock Analyzer - 股票分析统一入口（全功能版）

使用示例:
    ./stock_analyzer.py 688981.SH
    ./stock_analyzer.py 688981.SH --output markdown
    ./stock_analyzer.py 688981.SH --type dcf
    ./stock_analyzer.py 688981.SH --type seasons
    ./stock_analyzer.py 688981.SH --type wuxing
"""

import argparse
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.data.data_fetcher import DataFetcher
from app.analysis.system import SystemAnalyzer
from app.analysis.indicators.trend import sma, macd
from app.analysis.indicators.momentum import rsi
from app.models.stock import StockInfo
from app.report.generator import ReportGenerator
from app.report.markdown_report import MarkdownReportGenerator
from app.utils.logger import get_logger
from config import settings

# 导入框架级分析模块
from framework.trading.seasons.dcf import DCFValuation
from framework.trading.seasons.engine import SeasonsEngine
from framework.trading.wuxing.engine import WuxingEngine

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
        choices=["technical", "fundamental", "full", "dcf", "seasons", "wuxing", "safety"],
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


def analyze_dcf_sync(current_price: float) -> dict[str, Any]:
    """DCF 估值分析（同步版本）"""
    dcf = DCFValuation()
    
    # 使用当前股价反推合理 FCF 假设
    market_cap = current_price * 10.0  # 假设股本 10亿股
    current_fcf = market_cap * 0.06    # 6% FCF 收益率
    
    result = dcf.calculate_monte_carlo(
        current_fcf=current_fcf,
        shares_outstanding=10.0,
        industry="科技",
        simulations=1000,
    )
    
    return {
        "type": "dcf",
        "current_price": current_price,
        "dcf_mean": result.mean,
        "dcf_ci95_low": result.ci_95[0],
        "dcf_ci95_high": result.ci_95[1],
        "valuation": "undervalued" if result.mean > current_price * 1.2 else "overvalued" if result.mean < current_price * 0.8 else "fair",
    }


async def analyze_dcf_async(stock_code: str, data_hub: Any) -> dict[str, Any]:
    """DCF 估值分析（异步版本 — 通过 DataHub 获取数据）"""
    # 从 DataHub 获取财务数据
    daily_basic = await data_hub.fetch_financial(stock_code)
    income = await data_hub.fetch_income(stock_code)
    fina = await data_hub.fetch_fina_indicator(stock_code)
    
    # 聚合数据
    pe_ratio = None
    revenue = None
    roe = None
    
    if not daily_basic.empty:
        pe_ratio = daily_basic["pe"].iloc[0] if "pe" in daily_basic.columns else None
    
    if not income.empty:
        revenue = income["total_revenue"].iloc[0] if "total_revenue" in income.columns else None
    
    if not fina.empty:
        roe = fina["roe"].iloc[0] if "roe" in fina.columns else None
    
    # 使用聚合后的数据进行 DCF 计算
    # TODO: 根据实际财务数据计算 FCF
    current_fcf = revenue * 0.1 if revenue else 100.0  # 简化假设
    
    dcf = DCFValuation()
    result = dcf.calculate_monte_carlo(
        current_fcf=current_fcf,
        shares_outstanding=10.0,
        industry="科技",
        simulations=1000,
    )
    
    return {
        "type": "dcf",
        "stock_code": stock_code,
        "current_price": None,  # 需要额外获取
        "dcf_mean": result.mean,
        "dcf_ci95_low": result.ci_95[0],
        "dcf_ci95_high": result.ci_95[1],
        "pe_ratio": pe_ratio,
        "revenue": revenue,
        "roe": roe,
        "valuation": "undervalued" if result.mean > 100 * 1.2 else "overvalued" if result.mean < 100 * 0.8 else "fair",
    }


def analyze_seasons_sync(stock_code: str, current_price: float, dcf_value: float) -> dict[str, Any]:
    """四季引擎分析（同步版本）"""
    engine = SeasonsEngine()
    
    season = engine.analyze(
        ts_code=stock_code,
        dcf_value=dcf_value,
        current_price=current_price,
    )
    
    return {
        "type": "seasons",
        "current_season": season.season.value,
        "confidence": season.confidence,
        "safety_margin": season.safety_margin_result.safety_margin if hasattr(season, 'safety_margin_result') else 0,
    }


def analyze_wuxing_sync(stock_code: str, quotes: list) -> dict[str, Any]:
    """五行引擎分析（同步版本）"""
    engine = WuxingEngine()
    
    # 准备 DataFrame
    df = pd.DataFrame([{
        "trade_date": q.trade_date,
        "open": q.open,
        "high": q.high,
        "low": q.low,
        "close": q.close,
        "volume": q.volume,
    } for q in quotes])
    
    # 计算必要参数
    current_price = quotes[-1].close
    historical_high = max(q.high for q in quotes)
    recent_low = min(q.low for q in quotes[-20:])
    recent_high = max(q.high for q in quotes[-20:])
    avg_volume_20d = np.mean([q.volume for q in quotes[-20:]])
    current_volume = quotes[-1].volume
    daily_change = (quotes[-1].close - quotes[-2].close) / quotes[-2].close * 100 if len(quotes) > 1 else 0
    price_n_days_ago = quotes[-5].close if len(quotes) >= 5 else quotes[0].close
    
    wuxing = engine.analyze(
        ts_code=stock_code,
        df=df,
        current_price=current_price,
        historical_high=historical_high,
        recent_low=recent_low,
        recent_high=recent_high,
        avg_volume_20d=avg_volume_20d,
        current_volume=current_volume,
        daily_change=daily_change,
        price_n_days_ago=price_n_days_ago,
    )
    
    return {
        "type": "wuxing",
        "element": wuxing.element.value,
        "confidence": wuxing.confidence,
        "action": wuxing.action.value if wuxing.action else None,
        "position_guidance": wuxing.position_guidance,
    }


def analyze_safety_margin_sync(current_price: float, dcf_result: dict) -> dict[str, Any]:
    """安全边际分析（同步版本）"""
    dcf_mean = dcf_result.get("dcf_mean", current_price)
    
    if dcf_mean > 0:
        margin = (dcf_mean - current_price) / dcf_mean * 100
    else:
        margin = 0
    
    return {
        "type": "safety_margin",
        "current_price": current_price,
        "dcf_value": dcf_mean,
        "margin_percent": margin,
        "rating": "high" if margin > 30 else "medium" if margin > 15 else "low" if margin > 0 else "none",
    }


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
        current_price = latest.close
        print(f"   ✅ 最新交易日: {latest.trade_date}")
        print(f"   ✅ 收盘价: {current_price:.2f} 元")
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
        
        # 6. 框架级分析（DCF/四季/五行/安全边际）
        if args.type in ["full", "dcf", "seasons", "wuxing", "safety"]:
            print(f"\n🔮 [5/5] 执行框架级分析...")
            
            # DCF 估值
            if args.type in ["full", "dcf", "seasons", "safety"]:
                dcf_result = analyze_dcf_sync(current_price)
                result.details["dcf"] = dcf_result
                print(f"\n💰 DCF 估值: ¥{dcf_result['dcf_mean']:.2f} ({dcf_result['valuation']})")
            
            # 四季引擎
            if args.type in ["full", "seasons"]:
                seasons_result = analyze_seasons_sync(args.stock_code, current_price, result.details.get("dcf", {}).get("dcf_mean", current_price))
                result.details["seasons"] = seasons_result
                print(f"🌸 四季状态: {seasons_result['current_season']} (置信度: {seasons_result['confidence']:.2f})")
            
            # 五行引擎
            if args.type in ["full", "wuxing"]:
                wuxing_result = analyze_wuxing_sync(args.stock_code, quotes)
                result.details["wuxing"] = wuxing_result
                print(f"🔥 五行属性: {wuxing_result['element']} (置信度: {wuxing_result['confidence']:.2f})")
            
            # 安全边际
            if args.type in ["full", "safety"]:
                if "dcf" not in result.details:
                    dcf_result = analyze_dcf_sync(current_price)
                    result.details["dcf"] = dcf_result
                safety_result = analyze_safety_margin_sync(current_price, result.details["dcf"])
                result.details["safety_margin"] = safety_result
                print(f"🛡️ 安全边际: {safety_result['margin_percent']:.1f}% ({safety_result['rating']})")
        
        # 6. 生成报告
        output_dir = args.output_dir / args.stock_code
        output_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = date.today().strftime("%Y-%m-%d")
        generated_files = []
        
        # 准备基本面数据（供 HTML 和 Markdown 报告共用）
        fundamentals = None
        if financial:
            fundamentals = {
                "revenue": financial.revenue,
                "net_profit": financial.net_profit,
                "pe_ratio": getattr(financial, 'pe_ratio', None),
                "pb_ratio": getattr(financial, 'pb_ratio', None),
                "roe": getattr(financial, 'roe', None),
                "report_date": str(financial.report_date) if hasattr(financial, 'report_date') else None,
                "revenue_growth": None,
                "profit_growth": None,
                "pe_ttm": getattr(financial, 'pe_ratio', None),
            }
        
        # 准备技术指标数据（供 HTML 和 Markdown 报告共用）
        indicators = None
        if quotes and len(quotes) > 0:
            # 计算技术指标
            closes = [q.close for q in quotes]
            ma5_series = sma(closes, 5)
            ma20_series = sma(closes, 20)
            macd_data = macd(closes)
            rsi_series = rsi(closes, 14)
            
            # 准备技术指标详情数据
            from app.analysis.indicators.volatility import atr
            
            returns = np.diff(closes) / np.array(closes[:-1])
            
            # 获取最新指标值
            ma5_val = ma5_series.iloc[-1] if len(ma5_series) > 0 else None
            ma20_val = ma20_series.iloc[-1] if len(ma20_series) > 0 else None
            macd_dif_val = macd_data["macd"].iloc[-1] if len(macd_data["macd"]) > 0 else None
            macd_dea_val = macd_data["signal"].iloc[-1] if len(macd_data["signal"]) > 0 else None
            macd_hist_val = macd_data["histogram"].iloc[-1] if len(macd_data["histogram"]) > 0 else None
            rsi_val = rsi_series.iloc[-1] if len(rsi_series) > 0 else None
            
            # 计算ATR
            highs = [q.high for q in quotes]
            lows = [q.low for q in quotes]
            atr_series = atr(highs, lows, closes, period=14)
            atr_val = atr_series.iloc[-1] if len(atr_series) > 0 and not np.isnan(atr_series.iloc[-1]) else None
            
            # 计算布林带
            close_series = pd.Series(closes)
            ma20 = close_series.rolling(window=20).mean()
            std20 = close_series.rolling(window=20).std()
            bollinger_upper = ma20.iloc[-1] + 2 * std20.iloc[-1] if not np.isnan(ma20.iloc[-1]) else None
            bollinger_lower = ma20.iloc[-1] - 2 * std20.iloc[-1] if not np.isnan(ma20.iloc[-1]) else None
            
            # 计算波动率
            volatility_30d = float(np.std(returns) * np.sqrt(252) * 100) if len(returns) > 0 else None
            
            # 计算简化 VaR (95%) 和 最大回撤
            var_95 = float(np.percentile(returns, 5) * 100 * np.sqrt(20)) if len(returns) > 0 else None
            cum_returns = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cum_returns)
            drawdowns = (cum_returns - running_max) / running_max
            max_drawdown = float(np.min(drawdowns) * 100) if len(drawdowns) > 0 else None
            
            indicators = {
                "ma5": round(float(ma5_val), 2) if ma5_val is not None and not np.isnan(ma5_val) else None,
                "ma20": round(float(ma20_val), 2) if ma20_val is not None and not np.isnan(ma20_val) else None,
                "macd": round(float(macd_dif_val), 4) if macd_dif_val is not None and not np.isnan(macd_dif_val) else None,
                "macd_signal": round(float(macd_dea_val), 4) if macd_dea_val is not None and not np.isnan(macd_dea_val) else None,
                "macd_hist": round(float(macd_hist_val), 4) if macd_hist_val is not None and not np.isnan(macd_hist_val) else None,
                "rsi": round(float(rsi_val), 2) if rsi_val is not None and not np.isnan(rsi_val) else None,
                "volatility_30d": volatility_30d,
                "volume_ratio": round(quotes[-1].volume / np.mean([q.volume for q in quotes[-5:]]), 2) if len(quotes) >= 5 else None,
                "turnover_rate": None,
                "atr": round(float(atr_val), 2) if atr_val is not None else None,
                "bollinger_upper": round(float(bollinger_upper), 2) if bollinger_upper is not None else None,
                "bollinger_lower": round(float(bollinger_lower), 2) if bollinger_lower is not None else None,
                "var_95": var_95,
                "max_drawdown": max_drawdown,
            }
        
        if args.output in ["html", "both"]:
            print(f"\n📄 生成 HTML 报告...")
            html_generator = ReportGenerator()
            
            # 准备图表数据（真实数据）
            chart_data = {
                "dates": [q.trade_date.strftime("%m-%d") for q in quotes],
                "kline": [[q.open, q.close, q.low, q.high] for q in quotes],
                "volume": [q.volume / 10000 for q in quotes],
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
                indicators=indicators,
                fundamentals=fundamentals,
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
                quotes=quotes,
                indicators=indicators,
                fundamentals=fundamentals,
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
