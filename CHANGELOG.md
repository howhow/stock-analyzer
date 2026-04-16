# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-04-16

### Added

#### 核心框架重构
- **DataCore**: 数据核心模块，支持多数据源路由、缓存、质量检查、熔断机制
  - `framework/core/data_core.py` - 数据路由器核心实现
  - 智能数据源选择和降级策略
  - 数据质量评分体系 (0-1)
  - 熔断器保护机制

- **AlgorithmCore**: 算法核心模块，统一技术指标计算接口
  - `framework/core/algorithm_core.py` - 算法核心实现
  - 内置指标映射 (RSI, MACD, SMA, EMA, ATR, OBV, MFI 等)
  - AI 辅助分析接口
  - 异步处理支持

- **PluginManager**: 插件管理器，动态加载和管理插件
  - `framework/core/plugin_manager.py` - 插件管理器实现
  - 动态加载 (importlib)
  - 配置驱动 (YAML)
  - 自动发现插件
  - 健康检查
  - 热更新支持

#### 数据源插件
- **TusharePlugin**: Tushare 专业数据源
  - 熔断器保护 + 自动重试
  - 自定义异常类
  - 数据质量评分

- **AKSharePlugin**: AKShare 开源数据源
  - 实时行情支持
  - 中文字段映射
  - 自动重试机制

- **OpenBBPlugin**: OpenBB 全球数据源
  - A 股代码转换 (SH→SS)
  - 速率限制
  - 支持全球市场 (SH/SZ/HK/US)

- **LocalPlugin**: 本地数据源
  - CSV/Parquet 格式支持
  - 离线分析
  - 配置化数据目录

#### AI 插件
- **OpenAIPlugin**: OpenAI 兼容 API 插件
  - 支持 OpenAI 兼容服务 (硅基流动、腾讯混元等)
  - 流式输出支持
  - 健康检查

- **AnthropicPlugin**: Claude 系列模型插件
  - 支持 Claude 3 系列 (Opus/Sonnet/Haiku)
  - 流式输出支持
  - 健康检查

#### 报告插件
- **MarkdownReportPlugin**: Markdown 报告生成
  - 结构化报告格式
  - 模板支持
  - 文件渲染

- **PDFReportPlugin**: PDF 报告生成
  - 专业排版
  - HTML 模板转换
  - 中文字体支持

#### 预测验证体系
- **Prediction Model**: 预测数据模型
  - 预测方向 (UP/DOWN/FLAT)
  - 预测状态 (PENDING/CORRECT/INCORRECT/EXPIRED)
  - 准确率计算方法

- **AccuracyCalculator**: 准确率计算器
  - 简单准确率
  - 加权准确率
  - 按方向统计
  - 时间序列分析

- **AccuracyRanker**: 排行榜生成器
  - 按股票排名
  - 按策略排名
  - 按时间段排名

- **PredictionStore**: 预测存储
  - CRUD 操作
  - 批量验证
  - 统计查询

- **Verification Tasks**: Celery 验证任务
  - 每日验证任务
  - 统计计算任务
  - 排行榜生成任务
  - 过期清理任务

### Changed

- 重构数据获取逻辑，统一使用 DataCore
- 重构技术指标计算，统一使用 AlgorithmCore
- 插件化架构，支持动态扩展

### Fixed

- 修复 Tushare Token 泄露风险
- 修复异常类重复定义问题
- 修复测试数据类型问题 (TA-Lib 需要 float/double)

### Testing

- 测试用例数: 901+
- 测试覆盖率: 86.71%
- Lint 错误: 0

---

## [1.1.0] - 2026-04-11

### Added

- Web 前端 (Streamlit 多页面应用)
- AI 增强分析 (OpenAI/Claude 支持)
- 用户配置 API
- 安全模块增强
- 测试覆盖率提升 (775 → 901 用例)

### Changed

- 文件命名规范化 (移除 emoji)
- .gitignore 安全优化

---

## [1.0.0] - 2026-04-07

### Added

- 初始版本发布
- 核心分析功能
- 数据获取 (Tushare, AKShare)
- 技术指标计算
- 基础报告生成
