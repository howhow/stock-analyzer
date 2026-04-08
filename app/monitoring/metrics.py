"""
Prometheus 监控指标

定义和暴露业务监控指标
"""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

# ============ 请求指标 ============

# HTTP 请求计数
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

# HTTP 请求延迟
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ============ 分析指标 ============

# 分析请求计数
ANALYSIS_REQUESTS_TOTAL = Counter(
    "analysis_requests_total",
    "Total number of analysis requests",
    ["analysis_type", "mode", "status"],
)

# 分析处理时间
ANALYSIS_DURATION_SECONDS = Histogram(
    "analysis_duration_seconds",
    "Analysis processing time in seconds",
    ["analysis_type", "mode"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
)

# 分析评分分布
ANALYSIS_SCORE = Histogram(
    "analysis_score",
    "Distribution of analysis scores",
    ["analysis_type"],
    buckets=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
)

# ============ 数据源指标 ============

# 数据源请求计数
DATA_SOURCE_REQUESTS_TOTAL = Counter(
    "data_source_requests_total",
    "Total number of data source requests",
    ["source", "status"],
)

# 数据源延迟
DATA_SOURCE_LATENCY_SECONDS = Histogram(
    "data_source_latency_seconds",
    "Data source request latency in seconds",
    ["source"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# 数据源可用性
DATA_SOURCE_AVAILABILITY = Gauge(
    "data_source_availability",
    "Data source availability status (1=available, 0=unavailable)",
    ["source"],
)

# 熔断器状态
CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["name"],
)

# ============ 缓存指标 ============

# 缓存命中计数
CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_type"],
)

# 缓存未命中计数
CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_type"],
)

# 缓存大小
CACHE_SIZE = Gauge(
    "cache_size",
    "Current cache size in bytes",
    ["cache_type"],
)

# 缓存项目数
CACHE_ITEMS = Gauge(
    "cache_items_total",
    "Number of items in cache",
    ["cache_type"],
)

# ============ 任务队列指标 ============

# Celery 任务计数
CELERY_TASKS_TOTAL = Counter(
    "celery_tasks_total",
    "Total number of Celery tasks",
    ["task_name", "status"],
)

# Celery 任务延迟
CELERY_TASK_DURATION_SECONDS = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution time in seconds",
    ["task_name"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

# Celery 队列长度
CELERY_QUEUE_LENGTH = Gauge(
    "celery_queue_length",
    "Number of tasks waiting in queue",
    ["queue_name"],
)

# ============ 报告指标 ============

# 报告生成计数
REPORTS_GENERATED_TOTAL = Counter(
    "reports_generated_total",
    "Total number of reports generated",
    ["format", "status"],
)

# 报告存储大小
REPORT_STORAGE_SIZE_BYTES = Gauge(
    "report_storage_size_bytes",
    "Total size of report storage in bytes",
)

# 报告总数
REPORTS_TOTAL = Gauge(
    "reports_total",
    "Total number of stored reports",
)

# ============ 限流指标 ============

# 限流计数
RATE_LIMITS_TOTAL = Counter(
    "rate_limits_total",
    "Total number of rate limit hits",
    ["user_tier", "endpoint"],
)

# ============ AI 指标 ============

# AI 调用计数
AI_CALLS_TOTAL = Counter(
    "ai_calls_total",
    "Total number of AI API calls",
    ["provider", "model", "status"],
)

# AI 调用延迟
AI_CALL_LATENCY_SECONDS = Histogram(
    "ai_call_latency_seconds",
    "AI API call latency in seconds",
    ["provider", "model"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# AI 成本累计
AI_COST_TOTAL = Counter(
    "ai_cost_total",
    "Total AI API cost in USD",
    ["provider", "model"],
)

# ============ 系统信息 ============

# 应用信息
APP_INFO = Info(
    "app",
    "Application information",
)

# 设置应用信息
APP_INFO.info(
    {
        "version": "1.0.0",
        "name": "stock-analyzer",
    }
)


def get_metrics() -> bytes:
    """
    获取 Prometheus 指标

    Returns:
        指标数据（文本格式）
    """
    return generate_latest()


def get_content_type() -> str:
    """
    获取指标内容类型

    Returns:
        内容类型字符串
    """
    return CONTENT_TYPE_LATEST


# ============ 辅助函数 ============


def record_http_request(
    method: str,
    endpoint: str,
    status: int,
    duration: float,
) -> None:
    """
    记录 HTTP 请求指标

    Args:
        method: HTTP 方法
        endpoint: 端点路径
        status: 状态码
        duration: 请求时长（秒）
    """
    HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(
        duration
    )


def record_analysis(
    analysis_type: str,
    mode: str,
    status: str,
    duration: float,
    score: float,
) -> None:
    """
    记录分析指标

    Args:
        analysis_type: 分析类型
        mode: 分析模式
        status: 状态
        duration: 处理时长（秒）
        score: 评分
    """
    ANALYSIS_REQUESTS_TOTAL.labels(
        analysis_type=analysis_type, mode=mode, status=status
    ).inc()
    ANALYSIS_DURATION_SECONDS.labels(analysis_type=analysis_type, mode=mode).observe(
        duration
    )
    ANALYSIS_SCORE.labels(analysis_type=analysis_type).observe(score)


def record_cache_hit(cache_type: str) -> None:
    """记录缓存命中"""
    CACHE_HITS_TOTAL.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str) -> None:
    """记录缓存未命中"""
    CACHE_MISSES_TOTAL.labels(cache_type=cache_type).inc()


def update_cache_metrics(cache_type: str, size: int, items: int) -> None:
    """更新缓存指标"""
    CACHE_SIZE.labels(cache_type=cache_type).set(size)
    CACHE_ITEMS.labels(cache_type=cache_type).set(items)


def record_data_source_request(
    source: str,
    status: str,
    latency: float,
) -> None:
    """记录数据源请求指标"""
    DATA_SOURCE_REQUESTS_TOTAL.labels(source=source, status=status).inc()
    DATA_SOURCE_LATENCY_SECONDS.labels(source=source).observe(latency)


def update_data_source_availability(source: str, available: bool) -> None:
    """更新数据源可用性"""
    DATA_SOURCE_AVAILABILITY.labels(source=source).set(1 if available else 0)


def update_circuit_breaker_state(name: str, state: int) -> None:
    """更新熔断器状态"""
    CIRCUIT_BREAKER_STATE.labels(name=name).set(state)


def record_celery_task(
    task_name: str,
    status: str,
    duration: float,
) -> None:
    """记录 Celery 任务指标"""
    CELERY_TASKS_TOTAL.labels(task_name=task_name, status=status).inc()
    CELERY_TASK_DURATION_SECONDS.labels(task_name=task_name).observe(duration)


def record_report_generation(format_type: str, status: str) -> None:
    """记录报告生成指标"""
    REPORTS_GENERATED_TOTAL.labels(format=format_type, status=status).inc()


def record_rate_limit(user_tier: str, endpoint: str) -> None:
    """记录限流"""
    RATE_LIMITS_TOTAL.labels(user_tier=user_tier, endpoint=endpoint).inc()


def record_ai_call(
    provider: str,
    model: str,
    status: str,
    latency: float,
    cost: float,
) -> None:
    """记录 AI 调用指标"""
    AI_CALLS_TOTAL.labels(provider=provider, model=model, status=status).inc()
    AI_CALL_LATENCY_SECONDS.labels(provider=provider, model=model).observe(latency)
    AI_COST_TOTAL.labels(provider=provider, model=model).inc(cost)
