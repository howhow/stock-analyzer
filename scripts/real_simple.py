#!/usr/bin/env python3
"""
简化真实分析脚本 - 使用真实数据生成报告

跳过复杂分析引擎，直接使用真实K线数据生成报告
"""

import asyncio
import json
import sys
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from app.data import TushareClient
from app.report import ReportGenerator
from app.models.analysis import AnalysisResult, AnalysisType, AnalysisMode, AnalystReport, TraderSignal, DimensionScores, Recommendation, WyckoffPhase, MTFAlignment, EntryTiming
from config import settings
from app.analysis.indicators import sma, macd, rsi, atr


def build_chart_data(df: pd.DataFrame) -> dict:
    """构建图表数据"""
    close = df['close']
    high = df['high']
    low = df['low']
    
    # 取最近60个交易日
    n = min(60, len(df))
    df_recent = df.tail(n)
    
    # 计算MA
    ma5 = sma(close, 5)
    ma20 = sma(close, 20)
    
    # 计算MACD
    macd_result = macd(close)
    macd_line = macd_result['macd']
    signal = macd_result['signal']
    hist = macd_result['histogram']
    
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
    dates = []
    for _, row in df_recent.iterrows():
        td = row["trade_date"]
        if hasattr(td, 'strftime'):
            dates.append(td.strftime("%m-%d"))
        else:
            dates.append(str(td)[-5:].replace("-", "-"))
    
    # 成交量（万手）
    volumes = [float(row["volume"]) / 10000 for _, row in df_recent.iterrows()]
    
    # 构建MA数据
    ma5_data = [float(ma5.iloc[i]) if i < len(ma5) and pd.notna(ma5.iloc[i]) else None 
                for i in range(-n, 0)]
    ma20_data = [float(ma20.iloc[i]) if i < len(ma20) and pd.notna(ma20.iloc[i]) else None 
                 for i in range(-n, 0)]
    
    # 构建MACD数据
    macd_data = {
        "dif": [float(macd_line.iloc[i]) if i < len(macd_line) and pd.notna(macd_line.iloc[i]) else None 
                for i in range(-n, 0)],
        "dea": [float(signal.iloc[i]) if i < len(signal) and pd.notna(signal.iloc[i]) else None 
                for i in range(-n, 0)],
        "histogram": [float(hist.iloc[i]) if i < len(hist) and pd.notna(hist.iloc[i]) else None 
                     for i in range(-n, 0)],
    }
    
    # 构建RSI数据
    rsi_data = [float(rsi_14.iloc[i]) if i < len(rsi_14) and pd.notna(rsi_14.iloc[i]) else None 
                for i in range(-n, 0)]
    
    # 支撑压力位
    recent_30 = df.tail(30)
    support = float(recent_30['low'].min())
    resistance = float(recent_30['high'].max())
    
    return {
        "dates": dates,
        "kline": kline,
        "volume": volumes,
        "ma5": ma5_data,
        "ma20": ma20_data,
        "macd": macd_data,
        "rsi": rsi_data,
        "support": support,
        "resistance": resistance,
    }


def calculate_indicators(df: pd.DataFrame) -> dict:
    """计算技术指标"""
    close = df['close']
    high = df['high']
    low = df['low']
    
    ema_20 = sma(close, 20)  # 使用SMA作为EMA的近似
    rsi_14 = rsi(close, 14)
    atr_14 = atr(high, low, close, 14)
    macd_result = macd(close)
    macd_line = macd_result['macd']
    signal = macd_result['signal']
    hist = macd_result['histogram']
    
    volatility = close.pct_change().tail(30).std() * 100
    
    return {
        "ema_20": float(ema_20.iloc[-1]) if ema_20 is not None else None,
        "sma_20": float(ema_20.iloc[-1]) if ema_20 is not None else None,
        "rsi_14": float(rsi_14.iloc[-1]) if rsi_14 is not None else None,
        "atr_14": float(atr_14.iloc[-1]) if atr_14 is not None else None,
        "volatility_30d": float(volatility),
        "macd": {
            "dif": float(macd_line.iloc[-1]) if macd_line is not None else None,
            "dea": float(signal.iloc[-1]) if signal is not None else None,
            "histogram": float(hist.iloc[-1]) if hist is not None else None,
        },
    }


def analyze_trend(df: pd.DataFrame) -> dict:
    """简单趋势分析"""
    close = df['close']
    volume = df['volume']
    
    # 计算均线
    ma5 = sma(close, 5)
    ma20 = sma(close, 20)
    ma60 = sma(close, 60)
    
    # 趋势判断
    current_price = float(close.iloc[-1])
    ma5_val = float(ma5.iloc[-1])
    ma20_val = float(ma20.iloc[-1])
    
    # RSI
    rsi_14 = rsi(close, 14)
    rsi_val = float(rsi_14.iloc[-1]) if rsi_14 is not None else 50
    
    # MACD
    macd_result = macd(close)
    macd_line = macd_result['macd']
    signal_line = macd_result['signal']
    macd_val = float(macd_line.iloc[-1]) if macd_line is not None else 0
    signal_val = float(signal_line.iloc[-1]) if signal_line is not None else 0
    
    # 评分计算
    scores = {"trend": 3.0, "momentum": 3.0, "volume": 3.0}
    
    # 趋势评分
    if current_price > ma5_val > ma20_val:
        scores["trend"] = 4.0  # 多头排列
    elif current_price < ma5_val < ma20_val:
        scores["trend"] = 2.0  # 空头排列
    else:
        scores["trend"] = 3.0  # 震荡
    
    # 动量评分 (RSI)
    if rsi_val < 30:
        scores["momentum"] = 4.5  # 超卖，可能反弹
    elif rsi_val > 70:
        scores["momentum"] = 2.0  # 超买，可能回调
    elif 40 <= rsi_val <= 60:
        scores["momentum"] = 3.0  # 中性
    else:
        scores["momentum"] = 3.5
    
    # MACD评分
    if macd_val > signal_val and macd_val > 0:
        scores["momentum"] = min(5.0, scores["momentum"] + 0.5)  # 金叉向上
    elif macd_val < signal_val and macd_val < 0:
        scores["momentum"] = max(1.0, scores["momentum"] - 0.5)  # 死叉向下
    
    # 成交量评分
    avg_volume = volume.tail(20).mean()
    recent_volume = volume.iloc[-1]
    if recent_volume > avg_volume * 1.5:
        scores["volume"] = 4.0  # 放量
    elif recent_volume < avg_volume * 0.5:
        scores["volume"] = 2.5  # 缩量
    
    # 综合评分
    total = (scores["trend"] * 0.4 + scores["momentum"] * 0.4 + scores["volume"] * 0.2)
    
    # 建议判断
    if total >= 4.0:
        recommendation = Recommendation.BUY
    elif total >= 3.5:
        recommendation = Recommendation.HOLD
    elif total >= 2.5:
        recommendation = Recommendation.HOLD
    else:
        recommendation = Recommendation.SELL
    
    # 置信度
    confidence = min(90, max(50, total * 20))
    
    # Wyckoff阶段
    if current_price > ma20_val and macd_val > 0:
        wyckoff = WyckoffPhase.MARKUP
    elif current_price < ma20_val and macd_val < 0:
        wyckoff = WyckoffPhase.MARKDOWN
    else:
        wyckoff = WyckoffPhase.ACCUMULATION
    
    return {
        "scores": scores,
        "total": total,
        "recommendation": recommendation,
        "confidence": confidence,
        "wyckoff_phase": wyckoff,
        "ma5": ma5_val,
        "ma20": ma20_val,
        "rsi": rsi_val,
        "macd": macd_val,
    }


async def run_real_analysis():
    """运行真实分析"""
    print("=" * 60)
    print("Stock Analyzer - 真实数据分析演示")
    print("=" * 60)
    
    # 1. 获取数据
    print("\n[1/4] 获取中芯国际A股数据...")
    client = TushareClient(token=settings.tushare_token)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=150)
    
    quotes = await client.get_daily_quotes("688981.SH", start_date, end_date)
    
    if not quotes or len(quotes) < 50:
        print(f"❌ 数据获取失败 (获取到 {len(quotes) if quotes else 0} 条)")
        return
    
    df = pd.DataFrame([q.model_dump() for q in quotes])
    df = df.sort_values("trade_date").reset_index(drop=True)
    
    print(f"✅ 获取到 {len(df)} 条行情数据")
    print(f"   日期范围: {df['trade_date'].iloc[0]} ~ {df['trade_date'].iloc[-1]}")
    print(f"   最新收盘价: {df['close'].iloc[-1]:.2f}")
    print(f"   最新成交量: {df['volume'].iloc[-1]:.0f} 手")
    
    # 2. 计算技术指标
    print("\n[2/4] 计算技术指标...")
    indicators = calculate_indicators(df)
    
    print(f"✅ EMA(20): {indicators['ema_20']:.2f}")
    print(f"✅ RSI(14): {indicators['rsi_14']:.2f}")
    print(f"✅ ATR(14): {indicators['atr_14']:.2f}")
    print(f"✅ MACD: DIF={indicators['macd']['dif']:.4f}, DEA={indicators['macd']['dea']:.4f}")
    print(f"✅ 30日波动率: {indicators['volatility_30d']:.2f}%")
    
    # 3. 简单分析
    print("\n[3/4] 执行趋势分析...")
    analysis = analyze_trend(df)
    
    print(f"✅ 趋势评分: {analysis['scores']['trend']:.1f}")
    print(f"✅ 动量评分: {analysis['scores']['momentum']:.1f}")
    print(f"✅ 成交量评分: {analysis['scores']['volume']:.1f}")
    print(f"✅ 综合评分: {analysis['total']:.2f}/5.0")
    print(f"✅ 投资建议: {analysis['recommendation'].value}")
    print(f"✅ 置信度: {analysis['confidence']:.1f}%")
    print(f"✅ Wyckoff阶段: {analysis['wyckoff_phase'].value}")
    
    # 4. 生成报告
    print("\n[4/4] 生成分析报告...")
    generator = ReportGenerator()
    
    # 构建图表数据
    chart_data = build_chart_data(df)
    
    # 构建支撑压力位
    recent_30 = df.tail(30)
    support_levels = [float(recent_30['low'].min()), float(recent_30['low'].nsmallest(3).iloc[-1])]
    resistance_levels = [float(recent_30['high'].max()), float(recent_30['high'].nlargest(3).iloc[-1])]
    
    # 当前价格
    current_price = float(df['close'].iloc[-1])
    
    # 创建分析师报告
    analyst_report = AnalystReport(
        stock_code="688981.SH",
        stock_name="中芯国际",
        analysis_type=AnalysisType.BOTH,
        total_score=analysis['total'],
        technical_score=analysis['scores']['trend'],
        fundamental_score=analysis['scores']['momentum'],
        dimension_scores=DimensionScores(
            signal_strength=analysis['scores']['momentum'],
            opportunity_quality=analysis['scores']['trend'],
            risk_level=analysis['scores']['volume'],
        ),
        wyckoff_phase=analysis['wyckoff_phase'],
        support_levels=support_levels,
        resistance_levels=resistance_levels,
    )
    
    # 创建交易员信号
    trader_signal = TraderSignal(
        stock_code="688981.SH",
        recommendation=analysis['recommendation'],
        confidence=analysis['confidence'],
        entry_price=current_price * 0.98,  # 入场价 = 当前价 - 2%
        stop_loss_price=current_price * 0.95,  # 止损价 = -5%
        target_price=current_price * 1.08,  # 目标价 = +8%
        expected_return=8.0,
        var_95=5.0,
        max_drawdown=10.0,
        mtf_alignment=MTFAlignment.NEUTRAL,
        entry_timing=EntryTiming.WAIT if analysis['rsi'] > 60 else EntryTiming.IMMEDIATE,
    )
    
    # 创建分析结果
    result = AnalysisResult(
        analysis_id=f"real_{date.today().strftime('%Y%m%d%H%M%S')}",
        stock_code="688981.SH",
        stock_name="中芯国际",
        analysis_type=AnalysisType.BOTH,
        mode=AnalysisMode.ALGORITHM,
        analyst_report=analyst_report,
        trader_signal=trader_signal,
    )
    
    # 生成报告
    report = generator.generate(result, chart_data=chart_data, indicators=indicators)
    
    # 获取HTML内容（需要重新生成，因为ReportContent不存储HTML）
    report_data = generator._prepare_report_data(result, chart_data, indicators)
    html_content = generator._generate_html(report_data)
    
    # 保存报告
    output_dir = Path(__file__).parent.parent / "reports" / "real"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = date.today().strftime("%Y-%m-%d")
    output_file = output_dir / f"688981.SH_{date_str}.html"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ 报告已保存: {output_file}")
    print(f"   文件大小: {output_file.stat().st_size / 1024:.1f} KB")
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("📊 分析摘要")
    print("=" * 60)
    print(f"股票: 中芯国际 (688981.SH)")
    print(f"最新价格: {current_price:.2f}")
    print(f"MA5: {analysis['ma5']:.2f}")
    print(f"MA20: {analysis['ma20']:.2f}")
    print(f"RSI(14): {analysis['rsi']:.1f}")
    print(f"投资建议: {analysis['recommendation'].value}")
    print(f"综合评分: {analysis['total']:.2f}/5.0")
    print(f"置信度: {analysis['confidence']:.1f}%")
    print(f"报告路径: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_real_analysis())
