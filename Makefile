.PHONY: help setup ensure-api dev up down logs restart rebuild ps clean prod-up prod-down

# Sibling mimir-api repo (override: make dev API_DIR=/path/to/mimir-api)
API_DIR       ?= $(abspath ../mimir-api)
API_URL       ?= http://localhost:5000
PORT          ?= 5000
POSTGRES_PORT ?= 5432
API_WAIT_SECS ?= 60
ENV_FILE      ?= .env
COMPOSE       := docker compose -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_PROD  := docker compose
COMPOSE_FLAGS := --remove-orphans

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Create .env from .env.default if missing
	@test -f $(ENV_FILE) || (cp .env.default $(ENV_FILE) && echo "Created $(ENV_FILE) from .env.default — fill in secrets.")
	@echo "Ready — edit $(ENV_FILE) if needed."

# mimir-api `make dev` is foreground; we call `make up` (same compose stack, detached)
# so both API and bot can run on the same machine.
ensure-api: ## Start mimir-api (make -C API_DIR up) if not already reachable
	@if curl -sf -o /dev/null --max-time 2 "$(API_URL)/api/docs" \
		|| curl -sf -o /dev/null --max-time 2 "$(API_URL)/" \
		|| curl -sf -o /dev/null --max-time 2 "$(API_URL)"; then \
		echo "mimir-api already reachable at $(API_URL)."; \
	else \
		if [ ! -f "$(API_DIR)/Makefile" ]; then \
			echo "mimir-api Makefile not found at $(API_DIR)" >&2; \
			echo "Set API_DIR=/path/to/mimir-api" >&2; \
			exit 1; \
		fi; \
		echo "mimir-api not reachable — running: make -C $(API_DIR) up"; \
		$(MAKE) -C $(API_DIR) up; \
		echo "Waiting for mimir-api at $(API_URL)…"; \
		elapsed=0; \
		until curl -sf -o /dev/null --max-time 2 "$(API_URL)/api/docs" \
			|| curl -sf -o /dev/null --max-time 2 "$(API_URL)/" \
			|| curl -sf -o /dev/null --max-time 2 "$(API_URL)"; do \
			if [ $$elapsed -ge $(API_WAIT_SECS) ]; then \
				echo "Timed out after $(API_WAIT_SECS)s waiting for mimir-api" >&2; \
				exit 1; \
			fi; \
			sleep 2; \
			elapsed=$$((elapsed + 2)); \
		done; \
		echo "mimir-api is up."; \
	fi

dev: setup ensure-api ## Ensure mimir-api is up, then bot Docker hot reload (foreground)
	@echo "Starting mimir-bot (Docker dev)…"
	$(COMPOSE) up --build $(COMPOSE_FLAGS)

up: setup ensure-api ## Ensure mimir-api is up, then bot in background
	@echo "Starting mimir-bot (Docker, detached)…"
	$(COMPOSE) up --build -d $(COMPOSE_FLAGS)
	@echo "Bot running. Logs: make logs"

down: ## Stop bot Docker stack (does not stop mimir-api)
	$(COMPOSE) down $(COMPOSE_FLAGS)

logs: ## Follow bot logs
	$(COMPOSE) logs -f bot

restart: ## Restart bot container
	$(COMPOSE) restart bot

rebuild: setup ensure-api ## Force rebuild bot and restart
	$(COMPOSE) up --build -d --force-recreate $(COMPOSE_FLAGS)

ps: ## Show bot containers
	$(COMPOSE) ps

prod-up: setup ## Build and start production bot (detached)
	$(COMPOSE_PROD) up --build -d

prod-down: ## Stop production bot
	$(COMPOSE_PROD) down

clean: down ## Stop bot stack
	@echo "Bot stopped. mimir-api left running — stop it with: make -C $(API_DIR) down"
