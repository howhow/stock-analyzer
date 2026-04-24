.PHONY: help venv install dev celery celery-beat test test-unit test-integration test-all lint lint-style lint-type format clean clean-all docker docker-prod docker-stop docker-logs docker-clean stress-test db-init db-migrate check-deps reinstall frontend frontend-dev install-hooks uninstall-hooks

# ============================================
# 配置变量
# ============================================
VENV_NAME ?= local_venv
VENV = $(VENV_NAME)
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

# 代码目录（新增模块时必须同步更新）
CODE_DIRS = app framework plugins tests frontend

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
	@echo "  make dev         启动开发服务器（后端，日志→local_log/）"
	@echo "  make celery      启动 Celery Worker（日志→local_log/）"
	@echo "  make celery-beat 启动 Celery 定时任务（日志→local_log/）"
	@echo "  make frontend    启动前端服务"
	@echo "  make frontend-dev 同时启动前后端（需要两个终端）"
	@echo "  make test        运行单元测试 + 覆盖率"
	@echo "  make lint        完整代码检查(style + type)"
	@echo "  make lint-style  代码风格检查(black + flake8)"
	@echo "  make lint-type   类型检查(mypy)"
	@echo "  make format      格式化代码(black + isort)"
	@echo "  make clean       清理缓存文件 + 测试产物"
	@echo "  make clean-all   深度清理（含虚拟环境）"
	@echo ""
	@echo "【Docker 部署】"
	@echo "  make docker       启动开发环境容器"
	@echo "  make docker-prod  启动生产环境容器"
	@echo "  make docker-stop  停止容器"
	@echo "  make docker-logs  查看日志"
	@echo "  make docker-clean 清理容器和镜像"
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
	@echo "【核心框架】"
	@$(PYTHON) -c "import uvicorn" 2>/dev/null && echo "  ✅ uvicorn" || echo "  ❌ uvicorn"
	@$(PYTHON) -c "import celery" 2>/dev/null && echo "  ✅ celery" || echo "  ❌ celery"
	@$(PYTHON) -c "import streamlit" 2>/dev/null && echo "  ✅ streamlit" || echo "  ❌ streamlit"
	@echo ""
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
	$(PIP) install --force-reinstall -r requirements.txt
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
# 日志目录（统一使用 local_log/，已被 .gitignore 排除）
# ============================================
LOG_DIR = local_log
API_LOG = $(LOG_DIR)/api.log
CELERY_LOG = $(LOG_DIR)/celery.log

# 确保日志目录存在
$(LOG_DIR):
	@mkdir -p $(LOG_DIR)

# ============================================
# 开发运行 — 日志自动输出到 local_log/
# ============================================
dev: venv-check $(LOG_DIR)
	@echo "🚀 启动 API 服务..."
	@echo "🌐 访问地址: http://localhost:8000"
	@echo "📋 日志输出: $(API_LOG)"
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > $(API_LOG) 2>&1

# Celery Worker
celery: venv-check $(LOG_DIR)
	@echo "🚀 启动 Celery Worker..."
	@echo "📋 日志输出: $(CELERY_LOG)"
	$(PYTHON) -m celery -A app.tasks.celery_app worker --loglevel=info > $(CELERY_LOG) 2>&1

# Celery Beat (定时任务调度器)
celery-beat: venv-check $(LOG_DIR)
	@echo "🚀 启动 Celery Beat..."
	@echo "📋 日志输出: $(LOG_DIR)/celery-beat.log"
	$(PYTHON) -m celery -A app.tasks.celery_app beat --loglevel=info > $(LOG_DIR)/celery-beat.log 2>&1

# 前端服务
frontend: venv-check
	@if ! $(PYTHON) -c "import streamlit" 2>/dev/null; then \
		echo "📦 安装前端依赖..."; \
		$(PIP) install streamlit plotly -q; \
	fi
	@echo "🚀 启动前端服务..."
	@echo "🌐 访问地址: http://localhost:8501"
	cd frontend && $(PYTHON) -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# 同时启动前后端（需要两个终端）
frontend-dev: venv-check
	@echo "🚀 启动前后端服务..."
	@echo "🌐 后端: http://localhost:8000"
	@echo "🌐 前端: http://localhost:8501"
	@echo ""
	@echo "请分别在两个终端运行:"
	@echo "  终端1: make dev"
	@echo "  终端2: make frontend"
	@echo "  终端3: make celery    (如需异步任务)"

# ============================================
# 测试（重构后）
# ============================================
# test: 运行单元测试（纯 Mock，快速，默认命令）
test: venv-check
	@echo "🧪 运行单元测试..."
	$(PYTHON) -m pytest tests/unit/ -v \
		--cov-report=term-missing \
		--cov-report=html:local_test_report/htmlcov
	@echo "✅ 单元测试完成"
	@echo "📊 HTML覆盖率报告: local_test_report/htmlcov/index.html"

# test-unit: test 的别名（语义清晰）
test-unit: test

# test-integration: 集成测试（真实环境，需要 .env + Tushare Token）
test-integration: venv-check
	@echo "🔌 运行集成测试..."
	@echo "⚠️  注意：集成测试会调用真实 Tushare API，消耗积分"
	@test -f .env || (echo "❌ .env 文件不存在，集成测试需要 TUSHARE_TOKEN" && exit 1)
	@mkdir -p local_test_report/integration
	$(PYTHON) -m pytest tests/integration/ -v \
		-s \
		--tb=short \
		--html=local_test_report/integration/report.html \
		--self-contained-html \
		2>&1 | tee local_test_report/integration/test_output.log
	@echo "✅ 集成测试完成"
	@echo "📊 HTML报告: local_test_report/integration/report.html"
	@echo "📝 日志文件: local_test_report/integration/test_output.log"

# test-all: 顺序运行单元测试 + 集成测试 + 压力测试
test-all:
	@echo "🧪 阶段 1/3: 单元测试..."
	@$(MAKE) test
	@echo "🔌 阶段 2/3: 集成测试..."
	@$(MAKE) test-integration
	@echo "💥 阶段 3/3: 压力测试..."
	@$(MAKE) stress-test
	@echo "🎉 全部测试完成"

# stress-test: 压力测试（非UI模式，自动运行）
stress-test: venv-check
	@echo "💥 运行压力测试（非UI模式）..."
	$(PYTHON) -m pytest tests/stress/ -v || true
	$(PYTHON) -m locust -f tests/stress/locustfile.py \
		--headless \
		--users 50 \
		--spawn-rate 5 \
		--run-time 30s \
		--host http://localhost:8000
	@echo "✅ 压力测试完成"

# ============================================
# 代码质量检查
# ============================================
# lint: 完整代码检查（style + type）
lint: lint-style lint-type
	@echo "✅ 完整代码检查完成"

# lint-style: 代码风格检查（black + flake8）
lint-style: venv-check
	@echo "🔍 代码风格检查..."
	@echo "  → black 格式检查"
	$(PYTHON) -m black --check $(CODE_DIRS)
	@echo "  → flake8 静态分析"
	$(PYTHON) -m flake8 $(CODE_DIRS)
	@echo "✅ 代码风格检查通过"

# lint-type: 类型检查（mypy，只检查生产代码）
lint-type: venv-check
	@echo "🔍 类型检查..."
	$(PYTHON) -m mypy app framework plugins --ignore-missing-imports
	@echo "✅ 类型检查通过"

# format: 格式化代码（black + isort）
format: venv-check
	@echo "🎨 格式化代码..."
	@echo "  → isort 导入排序"
	$(PYTHON) -m isort $(CODE_DIRS)
	@echo "  → black 代码格式化"
	$(PYTHON) -m black $(CODE_DIRS)
	@echo "✅ 格式化完成"

# ============================================
# 清理（修复版）
# ============================================
# clean: 清理缓存文件 + 测试产物（保留虚拟环境）
clean:
	@echo "🧹 清理缓存文件..."
	@echo "  → Python 缓存"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "  → 测试产物"
	@rm -rf .pytest_cache 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@rm -rf local_test_report/htmlcov 2>/dev/null || true
	@rm -rf local_test_report/integration 2>/dev/null || true
	@echo "  → mypy 缓存"
	@rm -rf .mypy_cache 2>/dev/null || true
	@echo "  → 日志文件（保留目录）"
	@find $(LOG_DIR) -type f -name "*.log" -delete 2>/dev/null || true
	@echo "✅ 清理完成"

# clean-all: 深度清理（含虚拟环境 + 所有生成文件）
clean-all: clean
	@echo "🧹 深度清理..."
	@rm -rf $(VENV) 2>/dev/null || true
	@rm -rf local_venv 2>/dev/null || true
	@rm -rf local_test_report 2>/dev/null || true
	@rm -rf $(LOG_DIR) 2>/dev/null || true
	@rm -rf .tox 2>/dev/null || true
	@echo "✅ 深度清理完成（虚拟环境已删除，需重新 make venv + make install）"

# ============================================
# Docker 部署
# ============================================
docker: venv-check
	@echo "🐳 启动 Docker 开发环境..."
	docker-compose -f docker-compose.yml up -d --build
	@echo "✅ Docker 开发环境已启动"

docker-prod:
	@echo "🐳 启动 Docker 生产环境..."
	docker-compose -f docker-compose.prod.yml up -d --build
	@echo "✅ Docker 生产环境已启动"

docker-stop:
	@echo "🛑 停止 Docker 容器..."
	docker-compose -f docker-compose.yml down 2>/dev/null || true
	docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
	@echo "✅ Docker 容器已停止"

docker-logs:
	@echo "📋 查看 Docker 日志..."
	docker-compose -f docker-compose.yml logs -f

docker-clean:
	@echo "🧹 清理 Docker 容器和镜像..."
	docker-compose -f docker-compose.yml down -v --rmi all 2>/dev/null || true
	docker-compose -f docker-compose.prod.yml down -v --rmi all 2>/dev/null || true
	@echo "✅ Docker 清理完成"

# ============================================
# 数据库
# ============================================
db-init: venv-check
	@echo "🗄️  初始化数据库..."
	$(PYTHON) -c "from app.db.database import init_db; init_db()"
	@echo "✅ 数据库初始化完成"

db-migrate: venv-check
	@echo "🗄️  运行数据库迁移..."
	$(PYTHON) -m alembic upgrade head
	@echo "✅ 数据库迁移完成"

# ============================================
# Git Hooks
# ============================================
install-hooks: venv-check
	@echo "🔧 安装 Git Hooks..."
	$(PYTHON) -m pre_commit install
	@echo "✅ Git Hooks 安装完成"

uninstall-hooks: venv-check
	@echo "🔧 卸载 Git Hooks..."
	$(PYTHON) -m pre_commit uninstall
	@echo "✅ Git Hooks 卸载完成"
