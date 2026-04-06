.PHONY: install dev test lint format docker stress-test clean

install:
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v --cov=app --cov-report=term-missing

test-integration:
	pytest tests/integration/ -v

lint:
	black --check app tests
	flake8 app tests
	mypy app

format:
	black app tests
	isort app tests

docker:
	docker-compose -f docker/docker-compose.yml up --build

docker-prod:
	docker-compose -f docker/docker-compose.prod.yml up --build

stress-test:
	locust -f tests/stress/locustfile.py --users 50 --spawn-rate 5

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

db-init:
	python scripts/init_db.py

db-migrate:
	alembic revision --autogenerate -m "$(msg)"
	alembic upgrade head
