# Models 模块文档

> **模块路径**: `app/models/`  
> **功能**: 数据模型定义  
> **版本**: v1.1.0

---

## 📋 模块列表

| 模块 | 功能 | 状态 |
|------|------|------|
| `stock.py` | 股票数据模型 | ✅ |
| `analysis.py` | 分析结果模型 | ✅ |
| `report.py` | 报告模型 | ✅ |

---

## 📊 stock.py - 股票数据模型

### 数据类

#### StockInfo

**股票基本信息**

```python
from app.models.stock import StockInfo

stock_info = StockInfo(
    code="600276.SH",
    name="恒瑞医药",
    industry="医药生物",
    market="主板",
    list_date="2000-10-18",
)
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| code | str | 股票代码 |
| name | str | 股票名称 |
| industry | str | 所属行业 |
| market | str | 市场类型 |
| list_date | date | 上市日期 |

#### DailyQuote

**日线行情数据**

```python
from app.models.stock import DailyQuote

quote = DailyQuote(
    stock_code="600276.SH",
    trade_date=date(2026, 4, 8),
    open=57.0,
    close=57.45,
    high=57.64,
    low=55.91,
    volume=7344629,
    amount=418000000,
)
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| stock_code | str | 股票代码 |
| trade_date | date | 交易日期 |
| open | float | 开盘价 |
| close | float | 收盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| volume | int | 成交量（手） |
| amount | float | 成交额（元） |

#### FinancialData

**财务数据**

```python
from app.models.stock import FinancialData

financial = FinancialData(
    stock_code="600276.SH",
    report_date="2025-12-31",
    pe=35.2,
    pb=4.5,
    roe=12.8,
    revenue_growth=8.5,
    profit_margin=22.3,
)
```

---

## 📈 analysis.py - 分析结果模型

### AnalysisResult

**分析结果**

```python
from app.models.analysis import AnalysisResult, AnalysisType

result = AnalysisResult(
    analysis_id="analysis_600276_20260408",
    stock_code="600276.SH",
    analysis_type=AnalysisType.BOTH,
    details={
        "total_score": 48.5,
        "recommendation": "减持",
        "confidence": 0.45,
        "fundamental_score": 40.0,
        "technical_score": 60.0,
    },
)
```

**方法**:

```python
# 添加详细信息
result.add_detail("analyst", {"score": 85})

# 获取详细信息
analyst_data = result.get_detail("analyst")
```

### AnalysisType

**分析类型枚举**

```python
from app.models.analysis import AnalysisType

AnalysisType.TECHNICAL     # 技术分析
AnalysisType.FUNDAMENTAL   # 基本面分析
AnalysisType.BOTH          # 综合分析
```

---

## 📄 report.py - 报告模型

### ReportContent

**报告内容**

```python
from app.models.report import ReportContent, ReportFormat

report = ReportContent(
    report_id="rpt_20260408_001",
    stock_code="600276.SH",
    stock_name="恒瑞医药",
    analysis_data={
        "score": 48.5,
        "recommendation": "减持",
    },
    generator_version="1.0.0",
    content="<html>...</html>",
    format=ReportFormat.HTML,
)
```

### ReportFormat

**报告格式枚举**

```python
from app.models.report import ReportFormat

ReportFormat.HTML       # HTML 格式
ReportFormat.MARKDOWN   # Markdown 格式
```

---

## 🔄 模型关系

```
StockInfo (股票基本信息)
    ↓
DailyQuote (日线行情)
    ↓
AnalysisResult (分析结果)
    ↓
ReportContent (报告内容)
```

---

## 🛠️ 模型工具

### 数据验证

```python
from pydantic import ValidationError

try:
    quote = DailyQuote(
        stock_code="600276.SH",
        trade_date="2026-04-11",  # 类型错误
        open=57.0,
        close=57.45,
    )
except ValidationError as e:
    print(e.errors())
```

### 序列化

```python
# 转换为字典
data = quote.model_dump()

# 转换为 JSON
json_str = quote.model_dump_json()

# 从字典创建
quote = DailyQuote.model_validate(data)
```

---

## 📊 模型设计原则

1. **类型安全**: 使用 Pydantic 强类型
2. **不可变**: 关键字段不可修改
3. **验证**: 自动数据验证
4. **序列化**: 支持 JSON 序列化
5. **文档**: 字段说明文档

---

## 🔧 最佳实践

1. **使用模型**: 不要使用原始字典
2. **类型检查**: 利用 IDE 类型提示
3. **数据验证**: 捕获 ValidationError
4. **序列化**: 使用 model_dump_json()
5. **文档更新**: 及时更新字段说明

---

*文档版本: v1.1.0 | 最后更新: 2026-04-11*
