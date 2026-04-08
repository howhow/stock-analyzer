# Stock Analyzer 用户使用手册

> **版本**: v1.0.0  
> **更新日期**: 2026-04-08  
> **适用人群**: 个人投资者、量化开发者

---

## 📋 目录

1. [系统简介](#1-系统简介)
2. [环境准备](#2-环境准备)
3. [安装配置](#3-安装配置)
4. [快速开始](#4-快速开始)
5. [使用方式](#5-使用方式)
6. [输出说明](#6-输出说明)
7. [常见问题](#7-常见问题)
8. [技术支持](#8-技术支持)

---

## 1. 系统简介

Stock Analyzer 是一款**开源、生产级**的智能股票分析系统，专为个人投资者和量化开发者设计。

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| **多数据源** | Tushare + AKShare，自动降级熔断 |
| **完整技术分析** | MA/EMA/MACD/RSI/布林带等20+指标 |
| **双格式报告** | HTML（可视化图表）+ Markdown（AI友好） |
| **交互式图表** | ECharts K线图、MACD、RSI可视化 |
| **高测试覆盖** | 100%测试通过率，80.93%代码覆盖率 |
| **生产就绪** | 熔断器、缓存、重试机制 |

### 🎯 分析维度

| 维度 | 指标 | 说明 |
|-----|------|------|
| **技术面** | MA5/MA20/EMA | 趋势判断 |
| | MACD | 动量指标 |
| | RSI(14) | 超买超卖 |
| | 布林带 | 波动区间 |
| | ATR | 波动率 |
| **基本面** | 财务数据 | 盈利能力 |
| | 估值指标 | PE/PB/ROE |
| **交易信号** | 多空判断 | 入场时机 |
| | 支撑压力位 | 价格区间 |

### 📊 评分系统

**综合评分 = 基本面评分 × 40% + 技术面评分 × 60%**

| 评分范围 | 建议 | 说明 |
|---------|------|------|
| 70-100 | 买入 | 强烈看多信号 |
| 60-70 | 持有偏多 | 有上涨潜力 |
| 50-60 | 持有 | 观望为主 |
| 40-50 | 减持 | 风险较大 |
| 0-40 | 卖出 | 强烈看空 |

---

## 2. 环境准备

### 2.1 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Linux / macOS / Windows |
| Python | 3.11+ |
| 内存 | ≥2GB |
| 磁盘 | ≥1GB |

### 2.2 获取 Tushare Token

**Tushare 是主要数据源，需要注册获取 Token：**

1. 访问 [Tushare官网](https://tushare.pro/)
2. 注册账号（免费）
3. 登录后，进入「个人中心」→「接口Token」
4. 复制您的 Token（类似：`e9c480ef2b555568...`）

**免费版权限**：
- 每日 8000 次调用
- 日K线数据（需120+积分）
- 基础财务数据

> **注意**: 如果 Token 积分不足，系统会自动降级到 AKShare（免费，无需Token）

---

## 3. 安装配置

### 3.1 克隆项目

```bash
# 克隆代码仓库
git clone https://github.com/howhow/stock-analyzer.git
cd stock-analyzer
```

### 3.2 创建虚拟环境

```bash
# 使用 Makefile 创建虚拟环境
make venv

# 或手动创建
python3 -m venv local_venv
source local_venv/bin/activate  # Linux/macOS
# local_venv\Scripts\activate   # Windows
```

### 3.3 安装依赖

```bash
# 使用 Makefile 智能安装
make install

# 或手动安装
pip install -r requirements.txt
```

### 3.4 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用您喜欢的编辑器
```

**`.env` 文件内容示例：**

```ini
# Tushare 配置（必填）
TUSHARE_TOKEN=your_tushare_token_here

# AKShare 配置（可选）
AKSHARE_TIMEOUT=15
AKSHARE_MAX_RETRIES=3

# 分析配置（可选）
ANALYSIS_DAYS=120
ANALYSIS_MIN_DAYS=20

# Redis 配置（可选，用于缓存）
REDIS_URL=redis://localhost:6379/0
```

**重要**: 请将 `your_tushare_token_here` 替换为您在步骤 2.2 获取的真实 Token。

### 3.5 安装 TA-Lib（可选）

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y python3-dev build-essential

cd /tmp
curl -L -O http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=/usr
make
sudo make install
sudo ldconfig
```

**macOS**:
```bash
brew install ta-lib
```

---

## 4. 快速开始

### 4.1 验证安装

```bash
# 激活虚拟环境
source local_venv/bin/activate

# 运行测试
make test

# 预期输出: 716 passed
```

### 4.2 生成第一份报告

```bash
# 分析恒瑞医药
python stock_analyzer.py 600276.SH --output both

# 输出示例:
# 📊 开始分析: 600276.SH
# 📌 [1/4] 获取股票基本信息...
# 📈 [2/4] 获取行情数据（最近 120 天）...
# 💰 [3/4] 获取财务数据...
# 🔍 [4/4] 执行综合分析...
# 📄 生成 HTML 报告...
#    ✅ HTML 报告: local_analyze_report/600276.SH/600276.SH_2026-04-08.html
# 📄 生成 Markdown 报告...
#    ✅ Markdown 报告: local_analyze_report/600276.SH/600276.SH_2026-04-08.md
# 
# 🎯 综合评分: 48.5/100
# 💡 投资建议: 减持
# 🎯 置信度: 45%
```

### 4.3 查看报告

```bash
# HTML 报告（浏览器打开）
open local_analyze_report/600276.SH/600276.SH_2026-04-08.html

# Markdown 报告
cat local_analyze_report/600276.SH/600276.SH_2026-04-08.md
```

---

## 5. 使用方式

### 5.1 命令行参数

```bash
python stock_analyzer.py <股票代码> [选项]
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `stock_code` | 必需 | - | 股票代码（如 600276.SH） |
| `--output` | 可选 | html | 输出格式：html/markdown/both |
| `--days` | 可选 | 120 | 分析天数 |
| `--type` | 可选 | full | 分析类型：full/technical/fundamental |
| `--output-dir` | 可选 | local_analyze_report | 输出目录 |

### 5.2 使用示例

**基本用法**：
```bash
# 分析恒瑞医药（默认HTML输出）
python stock_analyzer.py 600276.SH

# 输出两种格式
python stock_analyzer.py 600276.SH --output both

# 分析最近180天数据
python stock_analyzer.py 600276.SH --days 180

# 仅技术分析
python stock_analyzer.py 600276.SH --type technical

# 指定输出目录
python stock_analyzer.py 600276.SH --output-dir ./my-reports
```

**分析不同市场**：
```bash
# 上海主板
python stock_analyzer.py 600519.SH  # 贵州茅台

# 上海科创板
python stock_analyzer.py 688981.SH  # 中芯国际

# 深圳主板
python stock_analyzer.py 000001.SZ  # 平安银行

# 深圳创业板
python stock_analyzer.py 300750.SZ  # 宁德时代
```

### 5.3 Python API（开发者）

```python
import asyncio
from app.data.data_fetcher import DataFetcher
from app.analysis.system import SystemAnalyzer
from app.report.generator import ReportGenerator
from app.analysis.indicators.trend import sma, macd
from app.analysis.indicators.momentum import rsi
from config import settings

async def analyze_stock(stock_code: str):
    """分析股票并生成报告"""
    
    # 1. 获取数据
    fetcher = DataFetcher()
    stock_info = await fetcher.get_stock_info(stock_code)
    quotes = await fetcher.get_daily_quotes(stock_code, days=120)
    
    # 2. 执行分析
    analyzer = SystemAnalyzer()
    result = analyzer.analyze(quotes, analysis_type="full")
    
    # 3. 计算技术指标
    closes = [q.close for q in quotes]
    ma5 = sma(closes, 5)
    ma20 = sma(closes, 20)
    macd_data = macd(closes)
    rsi_series = rsi(closes, 14)
    
    # 4. 准备图表数据
    chart_data = {
        "dates": [q.trade_date.strftime("%m-%d") for q in quotes],
        "kline": [[q.open, q.close, q.low, q.high] for q in quotes],
        "volume": [q.volume / 10000 for q in quotes],
        "support": result.details.get("support_levels", [quotes[-1].low])[0],
        "resistance": result.details.get("resistance_levels", [quotes[-1].high])[0],
        "ma5": ma5.tolist(),
        "ma20": ma20.tolist(),
        "macd": {
            "dif": macd_data["macd"].tolist(),
            "dea": macd_data["signal"].tolist(),
            "histogram": macd_data["histogram"].tolist(),
        },
        "rsi": rsi_series.tolist(),
    }
    
    # 5. 生成报告
    generator = ReportGenerator()
    html_report = generator.generate(
        result,
        stock_code=stock_code,
        stock_name=stock_info.name,
        chart_data=chart_data,
    )
    
    # 6. 保存报告
    output_file = f"{stock_code}_report.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_report.content)
    
    print(f"✅ 报告已保存: {output_file}")

# 运行
asyncio.run(analyze_stock("600276.SH"))
```

---

## 6. 输出说明

### 6.1 报告文件

**输出位置**: `local_analyze_report/<股票代码>/`

**文件命名**: `<股票代码>_<日期>.html` 或 `.md`

**示例**：
```
local_analyze_report/600276.SH/
├── 600276.SH_2026-04-08.html  # 恒瑞医药 HTML 报告
└── 600276.SH_2026-04-08.md    # 恒瑞医药 Markdown 报告

local_analyze_report/688981.SH/
├── 688981.SH_2026-04-08.html  # 中芯国际 HTML 报告
└── 688981.SH_2026-04-08.md    # 中芯国际 Markdown 报告
```

### 6.2 HTML 报告内容

**基本信息**：
- 股票代码 / 名称
- 分析时间
- 报告版本

**评分体系**：
- 综合评分 (0-100)
- 基本面评分
- 技术面评分
- 信号强度

**投资建议**：
- 建议（买入/持有/减持/卖出）
- 置信度 (0-100%)

**价格参考**：
- 支撑位 / 压力位
- 30日最高/最低

**技术指标**：
- K线图（ECharts交互式）
- MA5/MA20 移动平均线
- MACD 指标图
- RSI(14) 指标图
- 成交量柱状图

**风险提示**：
- VaR(95%)
- 最大回撤
- 波动率

### 6.3 Markdown 报告内容

**结构化表格**：
- 综合评分表
- 技术指标表
- 风险提示表

**JSON 元数据**：
```json
{
  "stock_code": "600276.SH",
  "analysis_date": "2026-04-08",
  "score": 48.5,
  "recommendation": "减持",
  "confidence": 0.45
}
```

### 6.4 技术指标说明

| 指标 | 说明 | 参考值 |
|------|------|--------|
| **MA5** | 5日移动平均线 | 短期趋势 |
| **MA20** | 20日移动平均线 | 中期趋势 |
| **MACD** | 异同移动平均线 | DIF上穿DEA为金叉（买入信号） |
| **RSI(14)** | 14日相对强弱指标 | <30超卖，>70超买 |
| **ATR(14)** | 14日平均真实波幅 | 反映波动性 |

---

## 7. 常见问题

### Q1: 提示 "ModuleNotFoundError: No module named 'app'"

**原因**: 未正确设置 Python 路径

**解决方案**:
```bash
# 确保在项目根目录运行
cd /path/to/stock-analyzer

# 或添加路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Q2: 提示 "Tushare Pro API 初始化失败"

**原因**: Token 未配置或无效

**解决方案**:
```bash
# 检查 .env 文件
cat .env | grep TUSHARE_TOKEN

# 确保格式正确（无引号）
TUSHARE_TOKEN=e9c480ef2b555568...
```

### Q3: 提示 "获取数据失败或数据不足"

**原因**: 
- Token 积分不足（需要 120+ 积分）
- 股票代码错误
- 网络问题

**解决方案**:
```bash
# 检查 Tushare 积分
# 登录 https://tushare.pro/ 查看积分

# 确认股票代码格式
# 上海交易所: 600276.SH
# 深圳交易所: 000001.SZ
```

### Q4: 提示 "您没有接口访问权限"

**原因**: Tushare 免费版权限有限

**解决方案**:
- 系统会自动降级到 AKShare
- 或升级 Tushare 积分

### Q5: HTML 报告 K 线图数据错误

**原因**: v1.0.0 之前版本存在数据排序问题

**解决方案**:
```bash
# 确保使用最新版本
git pull origin main
make clean
make install
```

### Q6: 测试失败（Redis 连接错误）

**说明**: 3个测试需要 Redis 环境

**解决方案**:
```bash
# 安装 Redis（可选）
sudo apt-get install redis-server
sudo systemctl start redis

# 或跳过这些测试（不影响主要功能）
```

### Q7: 如何分析多只股票？

**方法一**: 循环调用
```bash
for stock in 600276.SH 688981.SH 600519.SH; do
    python stock_analyzer.py $stock --output html
done
```

**方法二**: Python 脚本
```python
import asyncio
from stock_analyzer import analyze_stock

async def batch_analyze():
    stocks = ["600276.SH", "688981.SH", "600519.SH"]
    for stock in stocks:
        await analyze_stock(stock)

asyncio.run(batch_analyze())
```

---

## 8. 技术支持

### 项目信息

| 项目 | 信息 |
|------|------|
| **版本** | v1.0.0 |
| **测试覆盖率** | 80.93% |
| **测试通过率** | 100% (716/716) |
| **Python版本** | 3.11+ |
| **开源协议** | MIT |

### 相关文档

- **README.md** - 项目说明
- **docs/CHANGELOG.md** - 更新日志
- **飞书文档** - 架构设计、PRD、技术评审

### 联系方式

- **GitHub Issues**: 提交 Bug 报告或功能建议
- **架构师**: Agent-Arch
- **产品负责人**: How

---

## 附录：股票代码格式

| 交易所 | 代码格式 | 示例 |
|--------|----------|------|
| 上海主板 | 60XXXX.SH | 600519.SH (贵州茅台) |
| 上海科创板 | 688XXX.SH | 688981.SH (中芯国际) |
| 深圳主板 | 000XXX.SZ | 000001.SZ (平安银行) |
| 深圳创业板 | 300XXX.SZ | 300750.SZ (宁德时代) |

---

## 免责声明

⚠️ **重要提示**：

本系统生成的分析报告**仅供参考**，不构成任何投资建议。股市有风险，投资需谨慎。

- 所有分析基于历史数据，不保证未来表现
- 技术指标存在滞后性，需结合基本面分析
- 请根据自身风险承受能力做出投资决策

---

<div align="center">

**文档版本: v1.0 | 最后更新: 2026-04-08**

</div>
