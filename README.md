# Stock Analyzer

股票分析与交易机会识别系统 - 全AI自主股票分析系统

[![Coverage](https://img.shields.io/badge/coverage-81.08%25-brightgreen)](https://pytest.org)
[![Tests](https://img.shields.io/badge/tests-536%20passed-brightgreen)](https://pytest.org)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 项目概述

基于多维度数据分析，识别长线(1年+)和短线(3个月内)交易机会的智能股票分析系统。

### 核心特性

- **智能化分析**: 融合基本面、技术面分析
- **多时间框架**: MTF策略提升短线成功率
- **角色化协作**: 三角色分工确保分析质量
- **标准化输出**: HTML报告 + JSON数据接口

## 技术栈

| 层级 | 技术选型 | 版本 |
|-----|---------|-----|
| 语言 | Python | 3.11+ |
| Web框架 | FastAPI | 0.109+ |
| 数据处理 | pandas, numpy | latest |
| 技术指标 | ta-lib | 0.4.28 |
| 数据库 | PostgreSQL | 15+ |
| 缓存 | Redis | 7+ |
| 任务队列 | Celery | 5.3+ |
| 容器 | Docker | 24+ |

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd stock-analyzer

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# 安装依赖
make install
```

### 2. 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入必要配置
vim .env
```

### 3. 启动服务

```bash
# 开发模式
make dev

# 访问 API 文档
# http://localhost:8000/docs
```

### 4. 运行测试

```bash
# 运行所有测试
make test

# 运行代码检查
make lint
```

## 项目结构

```
stock-analyzer/
├── app/                    # 主应用
│   ├── api/               # API层
│   ├── core/              # 核心模块
│   ├── data/              # 数据获取模块
│   ├── analysis/          # 分析引擎模块
│   ├── ai/                # AI模块（可选）
│   ├── report/            # 报告生成模块
│   ├── tasks/             # 异步任务
│   ├── models/            # 数据模型
│   ├── monitoring/        # 监控指标
│   └── utils/             # 工具函数
├── tests/                 # 测试
├── config/                # 配置文件
├── docker/                # Docker配置
├── docs/                  # 文档
└── scripts/               # 脚本
```

## API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发规范

详见: [开发流程规范](https://feishu.cn/docx/X4aVdzY7Io0q1ZxzVtOc2prdnPf)

## 许可证

MIT License
