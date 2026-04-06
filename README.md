# Stock Analyzer

<div align="center">

**基于多维度数据分析的智能股票分析系统**

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)

[English](README.md) | [中文文档](docs/README_CN.md)

</div>

---

## 📖 项目简介

Stock Analyzer 是一个**生产级**的股票分析系统，采用模块化架构设计，支持：

- ✅ **多数据源整合** - Tushare + AKShare 自动降级
- ✅ **双格式报告** - HTML（人看）+ Markdown（AI Agent用）
- ✅ **完整分析流程** - 技术面 + 基本面 + 交易信号
- ✅ **高可用设计** - 熔断器 + 缓存 + 重试机制
- ✅ **高测试覆盖** - 86% 测试覆盖率，关键模块 94%+ 达标

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆项目
git clone <repository-url>
cd stock-analyzer

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

配置示例：

```bash
# Tushare API Token（必需）
TUSHARE_TOKEN=your_token_here

# 分析配置（可选）
ANALYSIS_DAYS=120  # 日K线数据抓取天数
```

### 3. 运行分析

```bash
# 基本用法 - 分析恒瑞医药
python stock_analyzer.py 600276.SH

# 输出 Markdown 报告
python stock_analyzer.py 600276.SH --output markdown

# 同时输出两种格式
python stock_analyzer.py 600276.SH --output both

# 分析最近180天数据
python stock_analyzer.py 600276.SH --days 180

# 仅技术分析
python stock_analyzer.py 600276.SH --type technical

# 指定输出目录
python stock_analyzer.py 600276.SH --output-dir ./my-reports
```

### 4. 查看报告

```bash
# HTML 报告（浏览器打开）
open local_analyze_report/600276.SH/600276.SH_2026-04-06.html

# Markdown 报告（文本编辑器查看）
cat local_analyze_report/600276.SH/600276.SH_2026-04-06.md
```

---

## 📊 核心功能

### 1. 多数据源支持

| 数据源 | 类型 | 权限要求 | 特点 |
|-------|------|---------|------|
| Tushare | 主数据源 | 需要Token | 数据全面，权限分级 |
| AKShare | 备用数据源 | 免费 | 无需Token，降级使用 |

**自动降级策略**：Tushare 失败自动切换 AKShare

### 2. 分析维度

| 维度 | 说明 |
|-----|------|
| 技术面分析 | 趋势判断、技术指标、支撑压力位 |
| 基本面分析 | 财务状况、盈利能力、估值水平 |
| 交易信号 | 多空信号、入场时机、风险控制 |

### 3. 报告格式

**HTML 报告**：
- 包含 K 线图表
- 技术指标可视化
- 适合人类阅读

**Markdown 报告**：
- 结构化数据表格
- JSON 元数据
- 适合 AI Agent 解析

---

## 📁 项目结构

```
stock-analyzer/
├── analyze.py              # 统一命令行入口
├── app/
│   ├── analysis/          # 分析引擎
│   │   ├── analyst.py     # 分析师角色
│   │   ├── trader.py      # 交易员角色
│   │   └── system.py      # 系统级分析
│   ├── data/              # 数据层
│   │   ├── tushare_client.py    # Tushare 客户端
│   │   ├── akshare_client.py    # AKShare 客户端
│   │   └── data_fetcher.py      # 数据获取协调器
│   ├── report/            # 报告生成
│   │   ├── generator.py         # HTML 报告生成器
│   │   └── markdown_report.py   # Markdown 报告生成器
│   └── models/            # 数据模型
├── config/                # 配置管理
├── tests/                 # 测试代码
├── docs/                  # 文档
├── requirements.txt       # 依赖列表
└── README.md             # 项目说明
```

---

## ⚙️ 配置说明

### 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|-------|------|--------|------|
| TUSHARE_TOKEN | ✅ | - | Tushare API Token |
| ANALYSIS_DAYS | ❌ | 120 | 日K线数据抓取天数 |
| ANALYSIS_MIN_DAYS | ❌ | 20 | 最少数据天数要求 |

### 分析类型

| 类型 | 说明 |
|-----|------|
| `full` | 完整分析（技术面 + 基本面） |
| `technical` | 仅技术分析 |
| `fundamental` | 仅基本面分析 |

---

## 🧪 测试

```bash
# 运行测试
pytest tests/

# 查看覆盖率
pytest --cov=app tests/

# 运行特定测试
pytest tests/unit/test_data_fetcher.py -v
```

**测试覆盖率**: 86% (关键模块 94%+)

---

## 📄 License

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Tushare](https://tushare.pro/) - 金融数据接口
- [AKShare](https://akshare.akfamily.xyz/) - 开源财经数据接口
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化 Web 框架
- [TA-Lib](https://ta-lib.org/) - 技术分析库

---

## 📞 联系方式

- 架构师: Agent-Arch
- 产品负责人: How

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star ⭐**

</div>
