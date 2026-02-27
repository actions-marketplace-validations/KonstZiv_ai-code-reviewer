.PHONY: help setup install test test-fast test-unit test-full lint format check clean docs pre-commit

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Complete project setup (venv + deps + pre-commit)
	uv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  source .venv/bin/activate  (Linux/Mac)"
	@echo "  .venv\\Scripts\\activate     (Windows)"
	@echo ""
	@echo "Then run: make install"

install: ## Install dependencies (PEP 735)
	uv sync --all-groups
	uv run pre-commit install
	@echo "✓ Dependencies installed"
	@echo "✓ Pre-commit hooks configured"

install-prod: ## Install production dependencies only
	uv sync

install-dev: ## Install dev dependencies only
	uv sync --group dev

install-docs: ## Install docs dependencies only
	uv sync --group docs

test-fast: ## Run unit tests excluding slow (fastest feedback loop)
	uv run pytest tests/unit/ -x -q -m "not slow" --no-header --tb=short

test: ## Run unit + integration tests (pre-commit check)
	uv run pytest tests/unit/ tests/integration/ -x -q --tb=short

test-full: ## Run all tests with coverage (CI / pre-PR)
	uv run pytest --cov=ai_reviewer --cov-report=term-missing --cov-report=html --cov-report=xml

lint: ## Run all linters (ruff + mypy)
	@echo "Running ruff check..."
	uv run ruff check .
	@echo "Running ruff format check..."
	uv run ruff format --check .
	@echo "Running mypy..."
	uv run mypy src/

format: ## Format code with ruff
	uv run ruff format .
	uv run ruff check --fix .

check: lint test-full ## Run all checks (lint + full tests with coverage)

pre-commit: ## Run pre-commit on all files
	uv run pre-commit run --all-files

clean: ## Clean build artifacts and caches
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

docs: ## Serve documentation locally
	uv run mkdocs serve

docs-build: ## Build documentation
	uv run mkdocs build

docs-deploy: ## Deploy documentation to GitHub Pages
	uv run mkdocs gh-deploy

build: ## Build distribution packages
	uv run python -m build

publish-test: ## Publish to TestPyPI
	uv run python -m twine upload --repository testpypi dist/*

publish: ## Publish to PyPI
	uv run python -m twine upload dist/*

update: ## Update all dependencies
	uv lock --upgrade
	uv sync --all-groups

# Development shortcuts
dev: ## Start development environment
	@echo "Starting development environment..."
	@echo "1. Activating virtual environment"
	@echo "   Run: source .venv/bin/activate"
	@echo "2. Documentation server will start at http://127.0.0.1:8000"
	uv run mkdocs serve

watch-test: ## Watch tests (requires pytest-watch)
	uv run ptw

# Quick quality check before commit
quick: ## Quick check (format + lint)
	uv run ruff check --fix .
	uv run ruff format .
	uv run mypy src/
	@echo "✓ Quick check complete!"
