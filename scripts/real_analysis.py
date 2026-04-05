#!/usr/bin/env python3
"""
真实分析脚本 - 使用真实数据进行股票分析

使用中芯国际A股 (688981.SH) 进行真实分析演示
"""

import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 强制加载 .env 文件
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from app.data import TushareClient
from app.analysis import Analyst, Trader
from app.report import ReportGenerator
from app.models import AnalysisResult, AnalysisType, AnalysisMode
from config import settings
import pandas as pd


def calculate_technical_indicators(df: pd.DataFrame) -> dict:
    """计算技术指标"""
    from app.analysis.indicators import ema, sma, macd, rsi, atr
    
    close = df["close"]
    high = df["high"]
    low = df["low"]
    
    # 计算指标
    ema_20 = ema(close, 20)
    sma_20 = sma(close, 20)
    macd_result = macd(close)
    rsi_14 = rsi(close, 14)
    atr_14 = atr(high, low, close, 14)
    
    return {
        "ema_20": ema_20.iloc[-1] if ema_20 is not None else None,
        "sma_20": sma_20.iloc[-1] if sma_20 is not None else None,
        "macd": {
            "dif": float(macd_result["macd"].iloc[-1]) if macd_result is not None else None,
            "dea": float(macd_result["signal"].iloc[-1]) if macd_result is not None else None,
            "histogram": float(macd_result["histogram"].iloc[-1]) if macd_result is not None else None,
        },
        "rsi_14": float(rsi_14.iloc[-1]) if rsi_14 is not None else None,
        "atr_14": float(atr_14.iloc[-1]) if atr_14 is not None else None,
        "volatility_30d": float(close.pct_change().tail(30).std() * 100) if len(close) >= 30 else None,
    }


def build_chart_data(df: pd.DataFrame, indicators: dict) -> dict:
    """构建图表数据"""
    from app.analysis.indicators import sma, macd, rsi
    
    close = df["close"]
    
    # 取最近60个交易日
    n = min(60, len(df))
    df_recent = df.tail(n)
    
    # 计算MA
    ma5 = sma(close, 5)
    ma20 = sma(close, 20)
    
    # 计算MACD
    macd_result = macd(close)
    
    # 计算RSI
    rsi_14 = rsi(close, 14)
    
    # 构建K线数据 [open, close, low, high]
    kline = []
    for _, row in df_recent.iterrows():
        kline.append([
            float(row["open"]),
            float(row["close"]),
            float(row["low"]),
            float(row["high"]),
        ])
    
    # 构建日期
    dates = [row["trade_date"].strftime("%m-%d") if isinstance(row["trade_date"], date) 
             else str(row["trade_date"])[-5:].replace("-", "-") 
             for _, row in df_recent.iterrows()]
    
    # 成交量（万手）
    volumes = [float(row["volume"]) / 10000 for _, row in df_recent.iterrows()]
    
    # 构建MACD数据
    macd_data = {
        "dif": [float(macd_result["macd"].iloc[i]) if i < len(macd_result["macd"]) and pd.notna(macd_result["macd"].iloc[i]) else None 
                for i in range(-n, 0)],
        "dea": [float(macd_result["signal"].iloc[i]) if i < len(macd_result["signal"]) and pd.notna(macd_result["signal"].iloc[i]) else None 
                for i in range(-n, 0)],
        "histogram": [float(macd_result["histogram"].iloc[i]) if i < len(macd_result["histogram"]) and pd.notna(macd_result["histogram"].iloc[i]) else None 
                     for i in range(-n, 0)],
    }
    
    # 构建RSI数据
    rsi_data = [float(rsi_14.iloc[i]) if i < len(rsi_14) and pd.notna(rsi_14.iloc[i]) else None 
                for i in range(-n, 0)]
    
    # 构建MA数据
    ma5_data = [float(ma5.iloc[i]) if i < len(ma5) and pd.notna(ma5.iloc[i]) else None 
                for i in range(-n, 0)]
    ma20_data = [float(ma20.iloc[i]) if i < len(ma20) and pd.notna(ma20.iloc[i]) else None 
                 for i in range(-n, 0)]
    
    return {
        "dates": dates,
        "kline": kline,
        "volume": volumes,
        "ma5": ma5_data,
        "ma20": ma20_data,
        "macd": macd_data,
        "rsi": rsi_data,
        "support": float(df["close"].tail(30).min()),
        "resistance": float(df["close"].tail(30).max()),
    }


async def run_real_analysis():
    """运行真实分析"""
    print("=" * 60)
    print("Stock Analyzer - 真实数据分析演示")
    print("=" * 60)
    
    # 1. 初始化客户端
    print("\n[1/5] 初始化 Tushare 客户端...")
    client = TushareClient(token=settings.tushare_token)
    
    if not client.pro:
        print("❌ Tushare Pro API 初始化失败")
        return
    
    print(f"✅ Tushare 客户端初始化成功 (Token: {settings.tushare_token[:10]}...)")
    
    # 2. 获取数据
    print("\n[2/5] 获取中芯国际A股数据...")
    stock_code = "688981.SH"
    stock_name = "中芯国际"
    end_date = date.today()
    start_date = end_date - timedelta(days=150)  # 获取更多数据用于计算指标
    
    quotes = await client.get_daily_quotes(stock_code, start_date, end_date)
    
    if not quotes or len(quotes) < 50:
        print(f"❌ 数据获取失败或数据不足 (获取到 {len(quotes) if quotes else 0} 条)")
        return
    
    print(f"✅ 获取到 {len(quotes)} 条行情数据")
    
    # 转换为 DataFrame
    df = pd.DataFrame([q.model_dump() for q in quotes])
    df = df.sort_values("trade_date").reset_index(drop=True)
    
    print(f"   日期范围: {df['trade_date'].iloc[0]} ~ {df['trade_date'].iloc[-1]}")
    print(f"   最新收盘价: {df['close'].iloc[-1]:.2f}")
    print(f"   最新成交量: {df['volume'].iloc[-1]:.0f} 手")
    
    # 3. 计算技术指标
    print("\n[3/5] 计算技术指标...")
    indicators = calculate_technical_indicators(df)
    
    print(f"✅ EMA(20): {indicators['ema_20']:.2f}")
    print(f"✅ SMA(20): {indicators['sma_20']:.2f}")
    print(f"✅ RSI(14): {indicators['rsi_14']:.2f}")
    print(f"✅ ATR(14): {indicators['atr_14']:.2f}")
    print(f"✅ MACD: DIF={indicators['macd']['dif']:.4f}, DEA={indicators['macd']['dea']:.4f}")
    print(f"✅ 30日波动率: {indicators['volatility_30d']:.2f}%")
    
    # 4. 运行分析引擎
    print("\n[4/5] 运行分析引擎...")
    analyst = Analyst()
    trader = Trader()
    
    # 准备股票信息
    stock_info = {
        "code": stock_code,
        "name": stock_name,
        "close": float(df["close"].iloc[-1]),
        "volume": float(df["volume"].iloc[-1]),
    }
    
    # 分析师分析
    analyst_report = await analyst.analyze(df, stock_info)
    print(f"✅ 分析师分析完成:")
    print(f"   - 总评分: {analyst_report.total_score:.2f}")
    print(f"   - 技术评分: {analyst_report.technical_score:.2f}")
    print(f"   - 基本面评分: {analyst_report.fundamental_score:.2f}")
    print(f"   - Wyckoff阶段: {analyst_report.wyckoff_phase.value}")
    
    # 交易员分析
    trader_signal = await trader.analyze(df, analyst_report)
    print(f"✅ 交易员分析完成:")
    print(f"   - 建议: {trader_signal.recommendation.value}")
    print(f"   - 置信度: {trader_signal.confidence:.1f}%")
    print(f"   - 入场价: {trader_signal.entry_price:.2f}")
    print(f"   - 止损价: {trader_signal.stop_loss_price:.2f}")
    print(f"   - 目标价: {trader_signal.target_price:.2f}")
    print(f"   - 预期收益: {trader_signal.expected_return:.2f}%")
    
    # 5. 生成报告
    print("\n[5/5] 生成分析报告...")
    generator = ReportGenerator()
    
    # 构建分析结果
    analysis_result = AnalysisResult(
        stock_code=stock_code,
        stock_name=stock_name,
        analysis_type=AnalysisType.TECHNICAL,
        mode=AnalysisMode.LONG_TERM,
        analyst_report=analyst_report,
        trader_signal=trader_signal,
    )
    
    # 构建图表数据
    chart_data = build_chart_data(df, indicators)
    
    # 生成报告
    report = generator.generate(
        analysis_result,
        chart_data=chart_data,
        indicators=indicators,
    )
    
    # 保存报告
    output_dir = project_root / "reports" / "real"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = date.today().strftime("%Y-%m-%d")
    output_file = output_dir / f"{stock_code}_{date_str}.html"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report.content)
    
    print(f"✅ 报告已保存: {output_file}")
    print(f"   - 文件大小: {output_file.stat().st_size / 1024:.1f} KB")
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("📊 分析摘要")
    print("=" * 60)
    print(f"股票: {stock_name} ({stock_code})")
    print(f"最新价格: {df['close'].iloc[-1]:.2f}")
    print(f"分析建议: {trader_signal.recommendation.value}")
    print(f"置信度: {trader_signal.confidence:.1f}%")
    print(f"总评分: {analyst_report.total_score:.2f}/5.0")
    print(f"报告路径: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_real_analysis())
