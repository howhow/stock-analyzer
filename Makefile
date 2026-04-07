.PHONY: help venv install dev test test-unit test-integration lint format clean docker docker-prod stress-test db-init db-migrate check-deps

# ============================================
# 配置变量
# ============================================
VENV_NAME ?= local_venv
VENV = $(VENV_NAME)
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

# ============================================
# 帮助信息
# ============================================
help:
	@echo "Stock Analyzer - Makefile 命令指南"
	@echo ""
	@echo "【首次使用】"
	@echo "  make venv        创建/检查虚拟环境"
	@echo "  make install     安装所有依赖"
	@echo ""
	@echo "【日常开发】"
	@echo "  make dev         启动开发服务器"
	@echo "  make test        运行所有测试 + 覆盖率"
	@echo "  make lint        代码检查"
	@echo "  make format      格式化代码"
	@echo "  make clean       清理缓存文件"
	@echo ""
	@echo "【Docker - 未完成】"
	@echo "  make docker      开发环境容器 (TODO)"
	@echo "  make docker-prod 生产环境容器 (TODO)"
	@echo ""
	@echo "【其他】"
	@echo "  make stress-test 压力测试"
	@echo "  make db-init     初始化数据库"
	@echo "  make db-migrate  数据库迁移"

# ============================================
# 环境管理 - 智能检测
# ============================================
venv:
	@if [ -d "$(VENV)" ] && [ -f "$(VENV)/bin/python3" ] && [ -f "$(VENV)/bin/pip" ]; then \
		echo "✅ 虚拟环境已存在且完整: $(VENV_NAME)"; \
		echo "   如需重建，请先删除: rm -rf $(VENV_NAME)"; \
	elif [ -d "$(VENV)" ]; then \
		echo "⚠️  虚拟环境不完整，正在重建..."; \
		rm -rf $(VENV); \
		python3 -m venv $(VENV); \
		echo "✅ 虚拟环境重建完成"; \
	else \
		echo "🔨 创建虚拟环境: $(VENV_NAME)"; \
		python3 -m venv $(VENV); \
		echo "✅ 虚拟环境创建完成"; \
	fi
	@$(MAKE) --no-print-directory check-python-version

check-python-version:
	@$(PYTHON) -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" || \
		(echo "❌ Python 版本不满足要求 (需要 3.11+)"; exit 1)
	@echo "✅ Python 版本检查通过"

# 检查单个依赖是否已安装
define check_dep
	@$(PYTHON) -c "import $(1)" 2>/dev/null || echo "  ⚠️  $(1) 未安装"
endef

# 检查核心依赖状态
check-deps: venv-check
	@echo "检查依赖状态..."
	@echo ""
	@echo "【生产依赖】"
	@$(PYTHON) -c "import fastapi" 2>/dev/null && echo "  ✅ fastapi" || echo "  ❌ fastapi"
	@$(PYTHON) -c "import tushare" 2>/dev/null && echo "  ✅ tushare" || echo "  ❌ tushare"
	@$(PYTHON) -c "import akshare" 2>/dev/null && echo "  ✅ akshare" || echo "  ❌ akshare"
	@$(PYTHON) -c "import talib" 2>/dev/null && echo "  ✅ talib" || echo "  ❌ talib"
	@$(PYTHON) -c "import pandas" 2>/dev/null && echo "  ✅ pandas" || echo "  ❌ pandas"
	@echo ""
	@echo "【开发依赖】"
	@$(PYTHON) -c "import pytest" 2>/dev/null && echo "  ✅ pytest" || echo "  ❌ pytest"
	@$(PYTHON) -c "import black" 2>/dev/null && echo "  ✅ black" || echo "  ❌ black"
	@$(PYTHON) -c "import flake8" 2>/dev/null && echo "  ✅ flake8" || echo "  ❌ flake8"
	@$(PYTHON) -c "import mypy" 2>/dev/null && echo "  ✅ mypy" || echo "  ❌ mypy"
	@$(PYTHON) -c "import isort" 2>/dev/null && echo "  ✅ isort" || echo "  ❌ isort"

# 智能安装：检查缺失依赖并仅安装缺失部分
install: venv
	@echo "检查缺失依赖..."
	@if $(PYTHON) -c "import fastapi, tushare, akshare, talib, pandas" 2>/dev/null; then \
		echo "✅ 生产依赖已完整"; \
	else \
		echo "📦 安装生产依赖..."; \
		$(PIP) install -r requirements.txt; \
	fi
	@if $(PYTHON) -c "import pytest, black, flake8, mypy, isort" 2>/dev/null; then \
		echo "✅ 开发依赖已完整"; \
	else \
		echo "📦 安装开发依赖..."; \
		$(PIP) install -r requirements-dev.txt; \
	fi
	@echo ""
	@echo "✅ 所有依赖已就绪"

# 强制重新安装所有依赖
reinstall: venv
	@echo "🔄 强制重新安装所有依赖..."
	$(PIP) install --force-reinstall -r requirements-dev.txt
	@echo "✅ 重新安装完成"

venv-check:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ 虚拟环境不存在"; \
		echo ""; \
		echo "请先执行:"; \
		echo "  make venv"; \
		echo "  make install"; \
		exit 1; \
	fi

# ============================================
# 开发运行
# ============================================
dev: venv-check
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ============================================
# 测试
# ============================================
test: venv-check
	$(PYTHON) -m pytest tests/ -v --cov=app --cov-report=term-missing

test-unit: venv-check
	$(PYTHON) -m pytest tests/unit/ -v --cov=app --cov-report=term-missing

test-integration: venv-check
	$(PYTHON) -m pytest tests/integration/ -v

# ============================================
# 代码质量
# ============================================
lint: venv-check
	$(PYTHON) -m black --check app tests
	$(PYTHON) -m flake8 app tests
	$(PYTHON) -m mypy app

format: venv-check
	$(PYTHON) -m black app tests
	$(PYTHON) -m isort app tests

# ============================================
# 清理
# ============================================
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ 缓存文件已清理"

# 清理虚拟环境（完全重置）
clean-all: clean
	@rm -rf $(VENV)
	@echo "✅ 虚拟环境已删除，请重新 make venv && make install"

# ============================================
# Docker (TODO - 未完成)
# ============================================
docker:
	@echo "⚠️  Docker 功能开发中，暂不可用"
	@echo "预计完成时间: TBD"
	# docker-compose -f docker/docker-compose.yml up --build

docker-prod:
	@echo "⚠️  Docker 功能开发中，暂不可用"
	@echo "预计完成时间: TBD"
	# docker-compose -f docker/docker-compose.prod.yml up --build

# ============================================
# 其他工具
# ============================================
stress-test: venv-check
	$(PYTHON) -m locust -f tests/stress/locustfile.py --users 50 --spawn-rate 5

db-init: venv-check
	@if [ ! -f scripts/init_db.py ]; then \
		echo "❌ 错误: scripts/init_db.py 不存在"; \
		exit 1; \
	fi
	$(PYTHON) scripts/init_db.py

db-migrate: venv-check
	$(VENV)/bin/alembic revision --autogenerate -m "$(msg)"
	$(VENV)/bin/alembic upgrade head
