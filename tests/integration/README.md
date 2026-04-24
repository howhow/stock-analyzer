"""集成测试README"""

# 集成测试说明

## 运行方式

```bash
# 运行所有集成测试
make test-integration

# 只运行CLI场景测试
make test-integration-cli

# 只运行Web场景测试
make test-integration-web
```

## 环境要求

1. 复制 `.env.example` 为 `.env` 并填入真实 TUSHARE_TOKEN
2. 确保本地可以访问 Tushare API
3. Web测试需要启动API服务（测试会自动启动）

## 测试分类

- **CLI场景**: 模拟用户命令行操作
- **Web场景**: 模拟用户网页操作
- **Framework**: DataHub、熔断器、数据库集成
- **Plugins**: 插件真实调用

## 注意事项

- 集成测试会消耗 Tushare 积分
- 测试运行时间较长（>30秒证明有真实API调用）
- 测试数据隔离，不污染生产环境
