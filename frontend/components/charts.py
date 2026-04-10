"""
图表组件

使用 Plotly 创建交互式图表
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_candlestick_chart(
    df: pd.DataFrame,
    title: str = "K线图",
    show_volume: bool = True,
    show_ma: bool = True,
) -> go.Figure:
    """
    创建 K 线图

    Args:
        df: 包含 OHLCV 数据的 DataFrame
        title: 图表标题
        show_volume: 是否显示成交量
        show_ma: 是否显示均线

    Returns:
        Plotly Figure 对象
    """
    # 创建子图
    if show_volume:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(title, "成交量"),
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # K 线图
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="K线",
            increasing_line_color="red",
            decreasing_line_color="green",
        ),
        row=1,
        col=1,
    )

    # 均线
    if show_ma and "ma5" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["ma5"],
                mode="lines",
                name="MA5",
                line=dict(color="orange", width=1),
            ),
            row=1,
            col=1,
        )

    if show_ma and "ma20" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["ma20"],
                mode="lines",
                name="MA20",
                line=dict(color="purple", width=1),
            ),
            row=1,
            col=1,
        )

    # 成交量
    if show_volume and "volume" in df.columns:
        colors = [
            "red" if close >= open_price else "green"
            for close, open_price in zip(df["close"], df["open"], strict=False)
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["volume"],
                name="成交量",
                marker_color=colors,
                opacity=0.7,
            ),
            row=2,
            col=1,
        )

    # 布局设置
    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        hovermode="x unified",
    )

    fig.update_xaxes(title_text="日期", row=2, col=1)
    fig.update_yaxes(title_text="价格", row=1, col=1)
    if show_volume:
        fig.update_yaxes(title_text="成交量", row=2, col=1)

    return fig


def create_indicator_chart(
    df: pd.DataFrame,
    indicator: str = "MACD",
    title: str | None = None,
) -> go.Figure:
    """
    创建技术指标图表

    Args:
        df: 包含指标数据的 DataFrame
        indicator: 指标类型 (MACD, RSI, KDJ)
        title: 图表标题

    Returns:
        Plotly Figure 对象
    """
    fig = go.Figure()
    title = title or f"{indicator} 指标"

    if indicator == "MACD":
        if "macd" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["macd"],
                    mode="lines",
                    name="MACD",
                    line=dict(color="blue", width=1),
                )
            )
        if "macd_signal" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["macd_signal"],
                    mode="lines",
                    name="Signal",
                    line=dict(color="orange", width=1),
                )
            )
        if "macd_hist" in df.columns:
            colors = ["red" if v >= 0 else "green" for v in df["macd_hist"]]
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df["macd_hist"],
                    name="Histogram",
                    marker_color=colors,
                    opacity=0.7,
                )
            )

    elif indicator == "RSI":
        if "rsi" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["rsi"],
                    mode="lines",
                    name="RSI",
                    line=dict(color="purple", width=1),
                )
            )
            # 超买超卖线
            fig.add_hline(
                y=70, line_dash="dash", line_color="red", annotation_text="超买"
            )
            fig.add_hline(
                y=30, line_dash="dash", line_color="green", annotation_text="超卖"
            )

    fig.update_layout(
        title=title,
        height=300,
        showlegend=True,
        hovermode="x unified",
    )

    return fig


def create_score_gauge(score: float, title: str = "综合评分") -> go.Figure:
    """
    创建评分仪表盘

    Args:
        score: 评分 (0-100)
        title: 标题

    Returns:
        Plotly Figure 对象
    """
    # 根据分数确定颜色
    if score >= 80:
        color = "green"
    elif score >= 60:
        color = "yellow"
    elif score >= 40:
        color = "orange"
    else:
        color = "red"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 40], "color": "#ffcccc"},
                    {"range": [40, 60], "color": "#ffffcc"},
                    {"range": [60, 80], "color": "#ccffcc"},
                    {"range": [80, 100], "color": "#99ff99"},
                ],
            },
        )
    )

    fig.update_layout(height=250)

    return fig


def create_radar_chart(
    data: dict[str, float],
    title: str = "能力雷达图",
) -> go.Figure:
    """
    创建雷达图

    Args:
        data: 维度数据 {维度名称: 分数}
        title: 图表标题

    Returns:
        Plotly Figure 对象
    """
    categories = list(data.keys())
    values = list(data.values())

    # 闭合雷达图
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name="评分",
        )
    )

    fig.update_layout(
        polar={"radialaxis": {"visible": True, "range": [0, 100]}},
        showlegend=False,
        title=title,
        height=400,
    )

    return fig
