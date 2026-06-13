# Makefile for LUXORliving Development
# Common tasks for local development and CI validation

.PHONY: help test test-fast test-full mutation format lint check security pre-push install clean

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install all dependencies
	@echo "📦 Installing dependencies..."
	python -m pip install --upgrade pip
	pip install -e ".[dev,mutation]"

format:  ## Auto-format code with black and isort
	@echo "🎨 Formatting code..."
	black custom_components tests scripts
	isort custom_components tests scripts
	@echo "✅ Formatting complete"

lint:  ## Run linters (flake8, bandit - enforced)
	@echo "🔍 Running linters..."
	@echo "→ flake8..."
	@flake8 custom_components tests scripts
	@echo "→ bandit..."
	@bandit -ll -r custom_components/luxor_living/
	@echo "✅ Linting complete"

check:  ## Check formatting without modifying files
	@echo "🔍 Checking code formatting..."
	@black --check custom_components tests scripts
	@isort --check-only custom_components tests scripts
	@echo "✅ Format check passed"

security:  ## Run security scans (bandit + pip-audit)
	@echo "🔒 Running security scans..."
	@echo "→ bandit (medium+ severity)..."
	@bandit -r custom_components/luxor_living/ --severity-level medium || true
	@echo "→ pip-audit..."
	@pip-audit --desc || true
	@echo "✅ Security scan complete"

test-fast:  ## Run smoke tests only (~5s)
	@echo "🧪 Running smoke tests..."
	@python -m pytest tests/ -q -m "smoke and not enable_socket"

test:  ## Run full test suite (~30s)
	@echo "🧪 Running full test suite..."
	@python -m pytest tests/ -m "not enable_socket" --cov=custom_components.luxor_living

test-full:  ## Run all tests with coverage report
	@echo "🧪 Running full test suite with coverage..."
	@python -m pytest tests/ -m "not enable_socket" --cov=custom_components.luxor_living --cov-report=html --cov-report=term
	@echo "📊 Coverage report: htmlcov/index.html"

mutation:  ## Run mutation tests against the smoke subset
	@echo "🧬 Running mutation tests..."
	@mutmut run
	@mutmut results

pre-push:  ## Run all pre-push checks (same as CI) - FAST mode
	@./scripts/pre_push_checks.sh --fast

pre-push-full:  ## Run all pre-push checks - FULL mode
	@./scripts/pre_push_checks.sh --full

clean:  ## Clean build artifacts and caches
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .pytest_cache/ .mypy_cache/ htmlcov/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✅ Clean complete"

# CI simulation targets
ci-format:  ## Check formatting (same as CI)
	@echo "🔍 CI: Format check..."
	@black --check custom_components tests scripts || (echo "❌ Run 'make format' to fix" && exit 1)
	@isort --check-only custom_components tests scripts || (echo "❌ Run 'make format' to fix" && exit 1)
	@echo "✅ CI: Format check passed"

ci-test:  ## Run tests (same as CI)
	@echo "🧪 CI: Running tests..."
	@python -m pytest tests/ -m "not enable_socket"
	@echo "✅ CI: Tests passed"

ci-all:  ## Run all CI checks locally
	@echo "🚀 Running full CI validation..."
	@make ci-format
	@make ci-test
	@make security
	@echo "✅ All CI checks passed! Safe to push 🚀"
