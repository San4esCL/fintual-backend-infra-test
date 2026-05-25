.PHONY: help deps sync env-init wait-db migrate seed seed-force setup run run-local \
	run-staging run-production docker-up docker-down up down test format lint check doctor

DOCKER_COMPOSE := docker compose

help:
	@echo "Backend/DevOps Interview - Setup Commands"
	@echo ""
	@echo "🚀 FIRST TIME (Local):"
	@echo "  make env-init           Create .env files from .env.example (once)"
	@echo "  make deps               Install Python dependencies (uv sync)"
	@echo "  make setup              deps + docker + migrate + seed (no server)"
	@echo ""
	@echo "💻 DAILY USE:"
	@echo "  make run                Start development server (uses .env.local)"
	@echo ""
	@echo "🔄 OTHER ENVIRONMENTS:"
	@echo "  make run-staging        Copy .env.staging → .env, then run"
	@echo "  make run-production     Copy .env.production → .env, then run"
	@echo ""
	@echo "🐳 DOCKER:"
	@echo "  make docker-up          Start PostgreSQL container"
	@echo "  make docker-down        Stop PostgreSQL container"
	@echo "  make up                 Start Postgres + web (gunicorn in Docker)"
	@echo "  make down               Stop all compose services"
	@echo ""
	@echo "🧪 TESTING:"
	@echo "  make test               Run tests (starts Postgres first)"
	@echo "  make check              lint + test (mirrors CI)"
	@echo "  make format             Format code"
	@echo "  make lint               Lint code"
	@echo "  make doctor             Print toolchain and DB diagnostics"

# ============================================================================
# DEPENDENCIES
# ============================================================================

deps sync:
	uv sync

# ============================================================================
# SETUP & RUN
# ============================================================================

env-init:
	@echo "🚀 Initializing environment files..."
	@for f in .env .env.local .env.staging .env.production; do \
		if [ -f "$$f" ] && [ "$(FORCE)" != "1" ]; then \
			echo "Skip $$f (exists). Use FORCE=1 to overwrite."; \
		else \
			cp .env.example $$f && echo "Created $$f"; \
		fi; \
	done
	@echo "Environment files initialized."

wait-db:
	@$(DOCKER_COMPOSE) exec -T postgres pg_isready -U postgres -d backend_devops_interview >/dev/null 2>&1 \
		|| (echo "Waiting for Postgres..." && sleep 2 && $(MAKE) wait-db)

migrate:
	uv run python manage.py migrate

seed:
	uv run python manage.py seed

seed-force:
	uv run python manage.py seed --force

setup: deps docker-up wait-db migrate seed
	@echo ""
	@echo "✅ Setup complete!"
	@echo "   Run: make run"
	@echo "   API docs: http://localhost:8000/api/docs"

run: docker-up wait-db
	@cp .env.local .env
	@echo "🚀 Starting development server (LOCAL)..."
	@echo "API docs: http://localhost:8000/api/docs"
	@echo "Admin: http://localhost:8000/admin"
	uv run python manage.py runserver

run-staging:
	@cp .env.staging .env
	@echo "🔄 Switched to STAGING environment"
	@echo "⚠️  Smoke test only — not a production deployment"
	uv run python manage.py runserver 0.0.0.0:8000

run-production:
	@cp .env.production .env
	@echo "🌍 Switched to PRODUCTION environment"
	@echo "⚠️  Smoke test only — not a production deployment"
	uv run python manage.py runserver 0.0.0.0:8000

# ============================================================================
# DOCKER
# ============================================================================

docker-up:
	@$(DOCKER_COMPOSE) up -d postgres
	@echo "✅ PostgreSQL starting (use make wait-db if migrate fails)"

docker-down:
	@$(DOCKER_COMPOSE) stop postgres
	@echo "✅ PostgreSQL stopped"

up:
	@$(DOCKER_COMPOSE) up -d --build
	@echo "✅ Postgres + web running at http://localhost:8000"

down:
	@$(DOCKER_COMPOSE) down
	@echo "✅ All services stopped"

# ============================================================================
# TESTING & CODE QUALITY
# ============================================================================

test: docker-up wait-db
	uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

check: lint docker-up wait-db
	uv run pytest -v

doctor:
	@echo "=== Toolchain ==="
	@python --version 2>/dev/null || python3 --version 2>/dev/null || echo "python: not found"
	@uv --version 2>/dev/null || echo "uv: not found"
	@docker --version 2>/dev/null || echo "docker: not found"
	@$(DOCKER_COMPOSE) version 2>/dev/null || echo "docker compose: not found"
	@echo ""
	@echo "=== Compose status ==="
	@$(DOCKER_COMPOSE) ps 2>/dev/null || true
	@echo ""
	@echo "=== Database ==="
	@$(DOCKER_COMPOSE) exec -T postgres pg_isready -U postgres 2>/dev/null && echo "Postgres: ready" || echo "Postgres: not ready (run make docker-up)"
	@echo ""
	@echo "=== Migrations ==="
	@uv run python manage.py showmigrations --plan 2>/dev/null | tail -5 || echo "Run make deps first"
