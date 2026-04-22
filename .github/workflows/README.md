# GitHub Actions CI 配置说明

## 触发条件
- push 到 master/main 分支
- pull_request 到 master/main 分支

## 检查流程
1. **代码风格** (black + flake8)
2. **类型检查** (mypy)
3. **测试** (pytest + coverage)
4. **覆盖率阈值检查**
   - 总体覆盖率 ≥ 80%
   - 单个文件覆盖率 ≥ 60%

## 失败条件
- 任何 lint 错误
- 任何测试失败
- 覆盖率不达标

## 本地验证
提交前运行：
```bash
make clean && make lint && make test
```
