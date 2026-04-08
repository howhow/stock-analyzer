# 监控配置

本目录包含 Stock Analyzer 的监控配置文件。

## 组件

### Prometheus
- **配置文件**: `prometheus/prometheus.yml`
- **端口**: 9090
- **功能**: 收集和存储监控指标

### Grafana
- **配置文件**: `grafana/datasources.yml`
- **端口**: 3000
- **功能**: 可视化监控数据

## 使用方法

### 1. 启动监控服务

```bash
# 使用 Docker Compose 启动
docker-compose -f docker/docker-compose.yml up -d prometheus grafana

# 或使用 Makefile
make docker
```

### 2. 访问监控界面

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (默认账号: admin/admin)

### 3. 应用暴露指标

Stock Analyzer 在 `/metrics` 端点暴露 Prometheus 指标：

```bash
curl http://localhost:8000/metrics
```

## 可用指标

### HTTP 指标
- `http_requests_total` - HTTP 请求总数
- `http_request_duration_seconds` - HTTP 请求延迟

### 分析指标
- `analysis_requests_total` - 分析请求总数
- `analysis_duration_seconds` - 分析处理时间
- `analysis_score` - 分析评分分布

### 数据源指标
- `data_source_requests_total` - 数据源请求总数
- `data_source_latency_seconds` - 数据源延迟
- `data_source_errors_total` - 数据源错误计数

### 缓存指标
- `cache_hits_total` - 缓存命中次数
- `cache_misses_total` - 缓存未命中次数
- `cache_size` - 缓存大小

## 配置说明

### Prometheus 配置
编辑 `prometheus/prometheus.yml` 调整抓取间隔和目标。

### Grafana 配置
1. 数据源配置: `grafana/datasources.yml`
2. Dashboard 配置: 通过 Grafana UI 导入或创建

## 注意事项

- 生产环境请修改 Grafana 默认密码
- 根据实际需求调整 Prometheus 数据保留时间
- 建议配置告警规则
