.PHONY: help install install-dev sync test lint format type-check clean run worker docs

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync --no-group dev

install-dev: ## Install all dependencies including dev
	uv sync

sync: ## Sync dependencies (same as install-dev)
	uv sync

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=app --cov-report=html --cov-report=term

lint: ## Run linting
	uv run ruff check app/ tests/

lint-fix: ## Run linting and fix issues
	uv run ruff check --fix app/ tests/

format: ## Format code
	uv run black app/ tests/

format-check: ## Check code formatting
	uv run black --check app/ tests/

type-check: ## Run type checking
	uv run mypy app/

clean: ## Clean up cache files
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

run: ## Run the development server
	uv run python run.py

worker: ## Start Celery worker
	uv run celery -A celery_worker.celery worker --loglevel=info

docs: ## Generate and serve documentation (if configured)
	@echo "Documentation will be available at http://localhost:5001/docs/ when running the server"

check: ## Run all checks (lint, format-check, type-check, test)
	uv run ruff check app/ tests/
	uv run black --check app/ tests/
	uv run mypy app/
	uv run pytest

requirements: ## Generate requirements.txt for compatibility
	uv export --no-hashes --format requirements-txt > requirements.txt

add: ## Add a new dependency (usage: make add PACKAGE=package-name)
ifndef PACKAGE
	@echo "Usage: make add PACKAGE=package-name"
	@exit 1
endif
	uv add $(PACKAGE)

add-dev: ## Add a new dev dependency (usage: make add-dev PACKAGE=package-name)
ifndef PACKAGE
	@echo "Usage: make add-dev PACKAGE=package-name"
	@exit 1
endif
	uv add --group dev $(PACKAGE)