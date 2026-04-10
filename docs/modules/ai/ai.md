# AI 模块文档

> **模块路径**: `app/ai/`  
> **功能**: AI协议适配与智能分析  
> **版本**: v1.1.0  
> **更新日期**: 2026-04-11

---

## 📋 模块列表

| 文件/目录 | 功能 | 状态 |
|-----------|------|------|
| `base.py` | AI提供者基类 | ✅ |
| `exceptions.py` | AI异常定义 | ✅ |
| `quota.py` | 配额管理 | ✅ |
| `providers/` | 协议适配器 | ✅ |

---

## 🏗️ 架构设计

### 协议适配器模式

```
app/ai/
├── base.py                 # 基类和接口定义
├── exceptions.py           # 自定义异常
├── quota.py               # 配额管理
└── providers/
    ├── factory.py          # 提供者工厂
    ├── openai_provider.py  # OpenAI协议适配器
    └── anthropic_provider.py # Anthropic协议适配器
```

### 设计理念

**协议兼容 > 模型绑定**

支持多种AI模型，用户自由选择，我们只负责协议适配：

| 协议 | 支持模型 |
|------|----------|
| OpenAI Protocol | GPT-4、DeepSeek、腾讯混元、Qwen等 |
| Anthropic Protocol | Claude 3.5 Sonnet、Claude 3 Opus等 |

---

## 🔧 核心类

### BaseAIProvider

**基类定义**:
```python
class BaseAIProvider(ABC):
    """AI提供者基类"""
    
    @abstractmethod
    async def analyze(
        self, 
        request: AIAnalysisRequest
    ) -> AIAnalysisResponse:
        """执行AI分析"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """测试连接"""
        pass
```

### AIAnalysisRequest

**请求模型**:
```python
@dataclass
class AIAnalysisRequest:
    prompt: str              # 提示词
    model: str | None        # 模型名称（可选）
    temperature: float = 0.7 # 温度参数
    max_tokens: int = 2000   # 最大token数
```

### AIAnalysisResponse

**响应模型**:
```python
@dataclass
class AIAnalysisResponse:
    content: str                    # AI生成内容
    model: str                      # 使用的模型
    usage: dict[str, int] | None    # Token使用情况
    latency_ms: float               # 响应延迟
```

---

## 🏭 工厂模式

### AIProviderFactory

**使用方式**:
```python
from app.ai.providers.factory import AIProviderFactory, AIProviderType

# 创建OpenAI提供者
provider = AIProviderFactory.create(
    provider_type=AIProviderType.OPENAI,
    api_key="sk-xxx",
    base_url="https://api.openai.com/v1",
    default_model="gpt-4-turbo-preview"
)

# 创建Anthropic提供者
provider = AIProviderFactory.create(
    provider_type=AIProviderType.ANTHROPIC,
    api_key="sk-ant-xxx",
    default_model="claude-3-opus-20240229"
)
```

**自定义OpenAI兼容API**:
```python
# 腾讯混元
provider = AIProviderFactory.create(
    provider_type=AIProviderType.OPENAI,
    api_key="xxx",
    base_url="https://hunyuan.tencentcloudapi.com/v1",
    default_model="hunyuan-lite"
)

# DeepSeek
provider = AIProviderFactory.create(
    provider_type=AIProviderType.OPENAI,
    api_key="sk-xxx",
    base_url="https://api.deepseek.com/v1",
    default_model="deepseek-chat"
)
```

---

## 📡 OpenAI协议适配器

### OpenAIProvider

**特性**:
- ✅ 支持所有OpenAI兼容API
- ✅ 自动重试机制
- ✅ 超时控制
- ✅ 限流处理

**配置参数**:
```python
OpenAIProvider(
    api_key: str,              # API密钥
    base_url: str = "...",     # API基础URL
    default_model: str = "...",# 默认模型
    timeout: float = 20.0,     # 超时时间（秒）
    max_retries: int = 3       # 最大重试次数
)
```

**使用示例**:
```python
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.base import AIAnalysisRequest

provider = OpenAIProvider(
    api_key="sk-xxx",
    base_url="https://api.openai.com/v1"
)

request = AIAnalysisRequest(
    prompt="分析恒瑞医药(600276.SH)的投资价值...",
    model="gpt-4-turbo-preview"
)

response = await provider.analyze(request)
print(response.content)
```

---

## 🤖 Anthropic协议适配器

### AnthropicProvider

**特性**:
- ✅ 支持Claude 3系列模型
- ✅ 自动重试机制
- ✅ 超时控制
- ✅ 限流处理

**配置参数**:
```python
AnthropicProvider(
    api_key: str,              # API密钥
    base_url: str = "...",     # API基础URL
    default_model: str = "...",# 默认模型
    timeout: float = 30.0,     # 超时时间（秒）
    max_retries: int = 3       # 最大重试次数
)
```

**使用示例**:
```python
from app.ai.providers.anthropic_provider import AnthropicProvider

provider = AnthropicProvider(
    api_key="sk-ant-xxx",
    default_model="claude-3-opus-20240229"
)

request = AIAnalysisRequest(
    prompt="分析恒瑞医药(600276.SH)的投资价值..."
)

response = await provider.analyze(request)
print(response.content)
```

---

## ⚠️ 异常处理

### 自定义异常

| 异常 | 说明 | 处理建议 |
|------|------|----------|
| `AIConfigError` | 配置错误 | 检查API Key配置 |
| `AIAPIError` | API调用错误 | 检查API状态 |
| `AITimeoutError` | 请求超时 | 增加timeout或重试 |
| `AIRateLimitError` | 限流错误 | 降低请求频率 |

**异常捕获示例**:
```python
from app.ai.exceptions import (
    AIConfigError,
    AIAPIError,
    AITimeoutError,
    AIRateLimitError
)

try:
    response = await provider.analyze(request)
except AIConfigError as e:
    print(f"配置错误: {e}")
except AITimeoutError as e:
    print(f"请求超时: {e}")
except AIRateLimitError as e:
    print(f"触发限流: {e}")
except AIAPIError as e:
    print(f"API错误: {e}")
```

---

## 📊 配额管理

### quota.py

**功能**（v1.2完整实现）:
- 用户配额限制
- 使用量统计
- 配额告警

---

## 🔒 安全配置

### API Key管理

**存储方式**:
- ✅ 加密存储（AES-128-CBC）
- ✅ 随机Salt（防止彩虹表攻击）
- ✅ 返回时脱敏（sk-****-key）

**配置示例**:
```bash
# .env
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
ENCRYPTION_KEY=your-encryption-key
```

---

## 📈 性能指标

### 测试覆盖率

| 模块 | 覆盖率 | 状态 |
|------|--------|------|
| OpenAI Provider | **100%** | ✅ 达标 |
| Anthropic Provider | **96.30%** | ✅ 达标 |
| Factory | **91.67%** | ✅ 达标 |

### 推荐模型

| 用途 | 推荐模型 | 原因 |
|------|----------|------|
| 首次使用 | 腾讯混元 | 性价比最高 |
| 深度研究 | Claude 3.5 Sonnet | 推理能力强 |
| 成本敏感 | DeepSeek | 最便宜 |
| 高质量 | GPT-4 Turbo | 综合最优 |

---

## 📝 开发规范

### 添加新协议适配器

1. 继承 `BaseAIProvider`
2. 实现 `analyze()` 方法
3. 实现 `test_connection()` 方法
4. 在 `factory.py` 添加枚举
5. 编写单元测试

---

## 🔄 版本规划

### v1.1 (当前)
- ✅ OpenAI协议适配器
- ✅ Anthropic协议适配器
- ✅ 工厂模式
- ✅ 重试机制

### v1.2 (计划)
- 🚧 文心一言适配器
- 🚧 配额管理完善
- 🚧 多模型对比分析
- 🚧 AI增强分析模式

---

## 📚 相关文档

- **[README.md](../../README.md)** - 项目说明
- **[USER_GUIDE.md](../USER_GUIDE.md)** - 用户手册
- **[api.md](../api/api.md)** - API文档
- **[core.md](../core/core.md)** - 安全模块

---

*文档版本: v1.1.0 | 最后更新: 2026-04-11*
