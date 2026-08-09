# GuideU — developer task runner.
# Works on macOS/Linux and on Windows via Git Bash / WSL.

CORE := services/core-engine
ANALYTICS := services/analytics-engine
REALTIME := services/real-time-engine

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ---- Environment -----------------------------------------------------------
.PHONY: env
env: ## Create .env from the template if missing
	@test -f .env || cp .env.example .env && echo ".env ready"

.PHONY: install
install: ## Install dependencies for all services
	cd $(CORE) && uv sync
	cd $(ANALYTICS) && uv sync
	cd $(REALTIME) && npm install

# ---- Django core-engine ----------------------------------------------------
.PHONY: migrate
migrate: ## Make + apply Django migrations
	cd $(CORE) && uv run python manage.py makemigrations
	cd $(CORE) && uv run python manage.py migrate

.PHONY: seed
seed: ## Ingest the Travel Planning synthetic dataset into the core DB (path auto-resolved)
	cd $(CORE) && uv run python manage.py seed_from_dataset

.PHONY: superuser
superuser: ## Create a Django superuser
	cd $(CORE) && uv run python manage.py createsuperuser

.PHONY: core
core: ## Run the Django dev server
	cd $(CORE) && uv run python manage.py runserver 0.0.0.0:8000

.PHONY: worker
worker: ## Run the Celery worker
	cd $(CORE) && uv run celery -A config worker -l info

# ---- analytics-engine ------------------------------------------------------
.PHONY: ml
ml: ## Run the FastAPI analytics-engine
	cd $(ANALYTICS) && uv run uvicorn app.main:app --reload --port 8001

.PHONY: train
train: ## Train all ML models on the synthetic dataset
	cd $(ANALYTICS) && uv run python -m training.run_all --dataset-dir "../../../Travel Planning"

# ---- real-time-engine ------------------------------------------------------
.PHONY: realtime
realtime: ## Run the Node real-time-engine in watch mode
	cd $(REALTIME) && npm run dev

# ---- Quality ---------------------------------------------------------------
.PHONY: test
test: ## Run the test suites
	cd $(CORE) && uv run pytest
	cd $(ANALYTICS) && uv run pytest

.PHONY: lint
lint: ## Lint TypeScript
	cd $(REALTIME) && npm run lint

# ---- Docker ----------------------------------------------------------------
.PHONY: up
up: ## Start the full stack with Docker Compose
	docker compose up --build

.PHONY: down
down: ## Stop the stack
	docker compose down
