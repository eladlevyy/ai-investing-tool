.PHONY: bootstrap seed-demo api workers web help clean

# Default target
help:
	@echo "AI Investing Tool - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make bootstrap    - Install all dependencies (pre-commit, venv, pnpm)"
	@echo "  make seed-demo    - Seed database with demo data"
	@echo ""
	@echo "Services:"
	@echo "  make api          - Run FastAPI server (port 8000)"
	@echo "  make workers      - Run background workers"
	@echo "  make web          - Run Next.js dev server (port 3000)"
	@echo ""
	@echo "Development:"
	@echo "  make clean        - Clean temporary files and caches"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo ""
	@echo "Docker:"
	@echo "  docker compose up -d     - Start development stack"
	@echo "  docker compose down      - Stop development stack"

# Bootstrap: Install all dependencies
bootstrap:
	@echo "🚀 Bootstrapping development environment..."
	@echo ""
	@echo "📦 Installing pre-commit hooks..."
	pip install pre-commit
	pre-commit install
	@echo ""
	@echo "🐍 Setting up Python virtual environment..."
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip setuptools wheel
	@echo ""
	@echo "📦 Installing pnpm..."
	npm install -g pnpm
	@echo ""
	@echo "✅ Bootstrap complete! Next steps:"
	@echo "   1. Copy .env.example to .env and configure"
	@echo "   2. Run: docker compose up -d"
	@echo "   3. Run: make seed-demo"
	@echo "   4. Start services with: make api, make workers, make web"

# Seed demo data
seed-demo:
	@echo "🌱 Seeding demo data..."
	@echo "⚠️  Note: This target will be implemented once the API is ready"
	@echo "   Expected: Load sample symbols and historical bars into database"
	# ./venv/bin/python scripts/seed_demo.py

# Run FastAPI server
api:
	@echo "🚀 Starting FastAPI server on port 8000..."
	@echo "⚠️  Note: This target will be implemented once the API code is ready"
	# cd apps/api && ../../venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run workers
workers:
	@echo "⚙️  Starting background workers..."
	@echo "⚠️  Note: This target will be implemented once the workers code is ready"
	# cd apps/workers && ../../venv/bin/python -m celery -A tasks worker --loglevel=info

# Run Next.js dev server
web:
	@echo "🌐 Starting Next.js dev server on port 3000..."
	@echo "⚠️  Note: This target will be implemented once the web app is ready"
	# cd apps/web && pnpm dev

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Clean complete"

# Run tests
test:
	@echo "🧪 Running tests..."
	@echo "⚠️  Note: This target will be implemented once tests are created"
	# ./venv/bin/pytest

# Run linters
lint:
	@echo "🔍 Running linters..."
	@echo "⚠️  Note: This target will be implemented once code is ready"
	# ./venv/bin/ruff check .
	# cd apps/web && pnpm lint

# Format code
format:
	@echo "✨ Formatting code..."
	@echo "⚠️  Note: This target will be implemented once code is ready"
	# ./venv/bin/black .
	# ./venv/bin/ruff check --fix .
	# cd apps/web && pnpm format
