# Stock Analyzer

<div align="center">

**生产级智能股票分析系统**

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Test Coverage](https://img.shields.io/badge/coverage-86.71%25-brightgreen.svg)](tests/)
[![Tests](https://img.shields.io/badge/tests-901%20passed-success.svg)](tests/)

</div>

---

## 📖 项目简介

- Stock Analyzer 是一个**开源、生产级**的股票分析系统，专为个人投资者和量化开发者设计
- 本项目代码全部由OpenClaw提供的AI Agent能力完成，仍在不断自我进化中...

### 核心特性

- ✅ **多数据源支持** - Tushare + AKShare，自动降级熔断
- ✅ **完整技术分析** - MA/EMA/MACD/RSI/布林带等20+指标
- ✅ **双格式报告** - HTML（可视化图表）+ Markdown（AI友好）
- ✅ **交互式图表** - ECharts K线图、MACD、RSI可视化
- ✅ **模块化架构** - 清晰的分层设计，易于扩展
- ✅ **高测试覆盖** - 100%测试通过率，86.71%代码覆盖率
- ✅ **Web 前端** - Streamlit 交互式界面
- ✅ **AI 增强** - OpenAI/Claude 多模型支持
- ✅ **生产就绪** - 熔断器、缓存、重试机制、健康检查

### 快速示例

```bash
# 分析恒瑞医药
python stock_analyzer.py 600276.SH --output both

# 分析中芯国际
python stock_analyzer.py 688981.SH --output html
```

**生成报告示例**：
- 📊 [恒瑞医药分析报告](local_analyze_report/600276.SH/600276.SH_2026-04-08.html) - 综合评分 48.5/100
- 📊 [中芯国际分析报告](local_analyze_report/688981.SH/688981.SH_2026-04-08.html) - 综合评分 52.4/100

---

## 🚀 快速开始

### 1. 环境要求

| 项目 | 要求 |
|------|------|
| Python | 3.11+ |
| 操作系统 | Linux / macOS / Windows |
| 内存 | ≥2GB |
| 磁盘 | ≥1GB |

### 2. 安装步骤

```bash
# 克隆项目
git clone https://github.com/howhow/stock-analyzer.git
cd stock-analyzer

# 创建虚拟环境
make venv

# 安装依赖
make install

# 配置 Tushare Token
cp .env.example .env
# 编辑 .env，填入你的 TUSHARE_TOKEN
```

### 3. 运行分析

```bash
# 基本用法
python stock_analyzer.py 600276.SH

# 输出两种格式
python stock_analyzer.py 600276.SH --output both

# 指定分析天数
python stock_analyzer.py 600276.SH --days 180

# 仅技术分析
python stock_analyzer.py 600276.SH --type technical

# 指定输出目录
python stock_analyzer.py 600276.SH --output-dir ./my-reports
```

### 4. 查看报告

```bash
# HTML 报告（浏览器打开）
open local_analyze_report/600276.SH/600276.SH_2026-04-08.html

# Markdown 报告
cat local_analyze_report/600276.SH/600276.SH_2026-04-08.md
```

---

## 📊 功能详解

### 1. 多数据源架构

| 数据源 | 类型 | 权限 | 特点 |
|-------|------|------|------|
| **Tushare** | 主数据源 | 需Token | 数据全面，权限分级 |
| **AKShare** | 备用数据源 | 免费 | 无需Token，自动降级 |

**智能降级策略**：
- Tushare 失败 → 自动切换 AKShare
- 熔断器保护 → 避免雪崩效应
- 健康检查 → 实时监控数据源状态

### 2. 分析维度

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

### 3. 报告格式

#### HTML 报告（适合人类阅读）

**内容包含**：
- 📈 **K线图** - ECharts 交互式图表
- 📊 **技术指标** - MACD、RSI、成交量
- 🎯 **综合评分** - 100分制评分系统
- 💡 **投资建议** - 买入/持有/减持/卖出
- ⚠️ **风险提示** - VaR、最大回撤、波动率

**特点**：
- 响应式设计，支持移动端
- 交互式图表，支持缩放、悬停
- 专业金融配色，一目了然

#### Markdown 报告（适合 AI Agent）

**特点**：
- 结构化表格
- JSON 元数据
- 易于解析
- 可集成到自动化流程

### 4. 评分系统

**综合评分 = 基本面评分 × 40% + 技术面评分 × 60%**

| 评分范围 | 建议 | 说明 |
|---------|------|------|
| 70-100 | 买入 | 强烈看多信号 |
| 60-70 | 持有偏多 | 有上涨潜力 |
| 50-60 | 持有 | 观望为主 |
| 40-50 | 减持 | 风险较大 |
| 0-40 | 卖出 | 强烈看空 |

---

## 📁 项目结构

```
stock-analyzer/
├── stock_analyzer.py          # 统一命令行入口
├── app/
│   ├── analysis/              # 分析引擎
│   │   ├── system.py          # 系统级分析
│   │   ├── indicators/        # 技术指标计算
│   │   │   ├── trend.py       # MA/EMA/MACD
│   │   │   ├── momentum.py    # RSI
│   │   │   ├── volatility.py  # ATR/布林带
│   │   │   └── volume.py      # 成交量指标
│   │   └── base.py            # 分析基类
│   ├── data/                  # 数据层
│   │   ├── tushare_client.py  # Tushare 客户端
│   │   ├── akshare_client.py  # AKShare 客户端
│   │   ├── data_fetcher.py    # 数据协调器
│   │   ├── health_check.py    # 健康检查
│   │   └── preprocessor.py    # 数据预处理
│   ├── report/                # 报告生成
│   │   ├── generator.py       # HTML 报告生成器
│   │   ├── markdown_report.py # Markdown 报告生成器
│   │   └── templates/         # HTML 模板
│   ├── models/                # 数据模型
│   │   ├── stock.py           # 股票模型
│   │   └── analysis.py        # 分析结果模型
│   ├── core/                  # 核心组件
│   │   ├── cache.py           # 缓存管理
│   │   ├── circuit_breaker.py # 熔断器
│   │   └── config.py          # 配置管理
│   └── utils/                 # 工具函数
│       ├── logger.py          # 日志系统
│       └── field_mapper.py    # 字段映射
├── tests/                     # 测试代码
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   └── regression/            # 回归测试
├── docs/                      # 文档
│   ├── USER_GUIDE.md         # 用户文档
│   ├── CHANGELOG.md           # 更新日志
│   └── modules/               # 模块文档
├── scripts/                   # 工具脚本
├── config/                    # 配置文件
├── requirements.txt           # 生产依赖
├── requirements-dev.txt       # 开发依赖
├── Makefile                   # 构建命令
└── README.md                  # 项目说明
```

---

## ⚙️ 配置说明

### 环境变量

创建 `.env` 文件：

```bash
# Tushare API Token（必需）
TUSHARE_TOKEN=your_token_here

# AKShare 配置（可选）
AKSHARE_TIMEOUT=15
AKSHARE_MAX_RETRIES=3

# 分析配置（可选）
ANALYSIS_DAYS=120
ANALYSIS_MIN_DAYS=20

# Redis 配置（可选，用于缓存）
REDIS_URL=redis://localhost:6379/0
```

### 获取 Tushare Token

1. 访问 [Tushare官网](https://tushare.pro/)
2. 注册账号（免费）
3. 登录后，进入「个人中心」→「接口Token」
4. 复制 Token

**免费版权限**：
- 每日 8000 次调用
- 日K线数据（需120+积分）
- 基础财务数据

### 系统依赖：TA-Lib

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

## 🐳 Docker 部署（预览）

> ⚠️ **预览状态**: Docker 部署为预览功能，建议优先使用本地部署方式。我们已提供完整配置，但尚未在所有环境验证。

### 前置条件

| 工具 | 版本要求 | 检查命令 |
|------|----------|----------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ | `docker-compose --version` |

**安装 Docker**:
- macOS: [Docker Desktop](https://docs.docker.com/desktop/install/mac-install/)
- Windows: [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/)
- Linux: [Docker Engine](https://docs.docker.com/engine/install/)

### 首次部署

```bash
# 1. 克隆项目
git clone https://github.com/howhow/stock-analyzer.git
cd stock-analyzer

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填写 TUSHARE_TOKEN、POSTGRES_PASSWORD 等

# 3. 启动开发环境
make docker

# 或生产环境
make docker-prod
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 后端 API | http://localhost:8000 |
| 前端界面 | http://localhost:8501 |
| API 文档 | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### Docker 命令

```bash
# 启动服务
make docker

# 生产环境启动
make docker-prod

# 停止服务
make docker-stop

# 查看日志
make docker-logs

# 清理资源
make docker-clean
```

### 服务架构

```
┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │
│ (Streamlit) │     │  (FastAPI)  │
│  :8501      │     │   :8000     │
└─────────────┘     └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │PostgreSQL│  │  Redis  │  │ Celery  │
        │  :5432   │  │  :6379  │  │ Worker  │
        └─────────┘  └─────────┘  └─────────┘
```

### 环境变量配置

| 变量 | 必需 | 说明 |
|------|------|------|
| TUSHARE_TOKEN | ✅ | Tushare API Token |
| POSTGRES_PASSWORD | ✅ | PostgreSQL 密码 |
| ENCRYPTION_KEY | ✅ | API Key 加密密钥 |
| APP_SECRET_KEY | ✅ | 应用安全密钥 |
| OPENAI_API_KEY | ❌ | OpenAI API Key（AI 分析）|
| ANTHROPIC_API_KEY | ❌ | Anthropic API Key（AI 分析）|

---

## 🛠️ Makefile 命令

| 命令 | 说明 |
|------|------|
| `make help` | 显示帮助信息 |
| `make venv` | 创建虚拟环境 |
| `make install` | 安装依赖 |
| `make check-deps` | 检查依赖状态 |
| `make test` | 运行测试 + 覆盖率 |
| `make lint` | 代码质量检查 |
| `make format` | 格式化代码 |
| `make clean` | 清理缓存文件 |
| `make clean-all` | 清理虚拟环境 |

---

## 🧪 测试

### 测试统计

| 指标 | 数值 |
|------|------|
| **总测试数** | 716 |
| **通过率** | 100% (716 passed) |
| **失败数** | 0 |
| **代码覆盖率** | 80.93% |
| **关键模块覆盖率** | 94%+ |

### 运行测试

```bash
# 运行所有测试
make test

# 或手动运行
local_venv/bin/python3 -m pytest tests/ -v --cov=app --cov-report=html

# 运行特定测试
local_venv/bin/python3 -m pytest tests/unit/test_data_fetcher.py -v

# 查看覆盖率报告
open htmlcov/index.html
```

---

## 📈 性能优化

### 已实现

- ✅ Redis 缓存（可选）
- ✅ 熔断器保护
- ✅ 异步数据获取
- ✅ 数据预处理

### 待优化

- 🔲 批量股票分析
- 🔲 历史数据本地存储
- 🔲 WebSocket 实时推送

---

## 🗺️ 开发路线

### v1.0.0 (当前版本)

- ✅ 多数据源支持
- ✅ 技术分析完整实现
- ✅ HTML/Markdown 报告
- ✅ 交互式图表
- ✅ 高测试覆盖率

### v1.1.0 (当前版本)

- ✅ Web 前端（Streamlit）
- ✅ AI 增强分析（OpenAI/Claude）
- ✅ 测试覆盖率提升至 86.71%
- ✅ 用户配置 API
- ✅ 安全模块增强

### v2.0.0 (未来)

- 🔲 机器学习预测
- 🔲 实时监控告警
- 🔲 多账户管理
- 🔲 策略市场

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

**代码规范**：
- 使用 Black 格式化代码
- 通过 mypy 类型检查
- 测试覆盖率不低于 80%

---

## ⚠️ 已知问题

### 数据源问题

#### AKShare 数据获取不稳定

**问题描述**：AKShare 调用东方财富数据接口时可能失败，原因：
- 东方财富对爬虫和 API 调用管控严格
- 频繁访问会触发反爬机制
- 网络波动导致连接中断

**影响范围**：
- 股票基本信息获取失败
- 财务数据获取失败

**解决方案**：
1. **推荐**：使用 Tushare Pro（需要积分权限）
2. 降低 AKShare 调用频率
3. 等待一段时间后重试

**错误示例**：
```
akshare_get_stock_info_failed: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

**系统行为**：
- Tushare 失败 → 自动降级到 AKShare
- AKShare 失败 → 返回空数据，系统继续运行
- 财务数据获取失败 → 自动退化为纯技术面分析

### Tushare 权限问题

**问题描述**：免费版 Tushare Token 权限有限：
- 每分钟最多访问 1 次接口
- 部分财务数据需要更高级别积分

**解决方案**：
- 升级 Tushare 积分等级
- 使用 AKShare 作为备用数据源

---

## 📄 License

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Tushare](https://tushare.pro/) - 金融数据接口
- [AKShare](https://akshare.akfamily.xyz/) - 开源财经数据接口
- [ECharts](https://echarts.apache.org/) - 可视化图表库
- [TA-Lib](https://ta-lib.org/) - 技术分析库

---

## 📞 联系方式

- **GitHub Issues**: 提交 Bug 报告或功能建议
- **Pull Requests**: 欢迎贡献代码

---

## ⚠️ 免责声明

本系统生成的分析报告**仅供参考**，不构成任何投资建议。股市有风险，投资需谨慎。

- 所有分析基于历史数据，不保证未来表现
- 技术指标存在滞后性，需结合基本面分析
- 请根据自身风险承受能力做出投资决策

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star ⭐**

</div>
