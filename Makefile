.PHONY: help start stop restart status logs test test-ai test-core test-ui docker-up docker-down

GATEWAY_PORT ?= 8080
AI_PORT ?= 8000
UI_PORT ?= 5173

LOG_DIR := $(CURDIR)/.logs
PID_DIR := $(CURDIR)/.pids

help: ## Show available commands
	@echo "Local RAG — Polyglot Orchestration Commands"
	@echo "-------------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Start all 3 services (ai-service, core-service, web-ui) in the background
	@mkdir -p "$(LOG_DIR)" "$(PID_DIR)"
	@echo "1/3 Starting Python AI Service on :$(AI_PORT)..."
	@if curl -sf http://127.0.0.1:$(AI_PORT)/health >/dev/null 2>&1; then \
		echo "    ai-service is already healthy on :$(AI_PORT)"; \
	else \
		(cd services/ai-service && LOCAL_RAG_PORT=$(AI_PORT) nohup uv run python main.py > "$(LOG_DIR)/ai-service.log" 2>&1 & echo $$! > "$(PID_DIR)/ai-service.pid"); \
		echo "    ai-service started (logs: .logs/ai-service.log)"; \
	fi
	@echo "2/3 Starting Java Core Gateway on :$(GATEWAY_PORT)..."
	@if curl -sf http://127.0.0.1:$(GATEWAY_PORT)/api/v1/health >/dev/null 2>&1; then \
		echo "    core-service is already healthy on :$(GATEWAY_PORT)"; \
	else \
		(cd services/core-service && SERVER_PORT=$(GATEWAY_PORT) AI_SERVICE_URL=http://127.0.0.1:$(AI_PORT) nohup ./mvnw spring-boot:run > "$(LOG_DIR)/core-service.log" 2>&1 & echo $$! > "$(PID_DIR)/core-service.pid"); \
		echo "    core-service started (logs: .logs/core-service.log)"; \
	fi
	@echo "3/3 Starting React Web UI on :$(UI_PORT)..."
	@if curl -sf http://localhost:$(UI_PORT) >/dev/null 2>&1; then \
		echo "    web-ui is already running on :$(UI_PORT)"; \
	else \
		(cd services/web-ui && VITE_GATEWAY_URL=http://localhost:$(GATEWAY_PORT) nohup npm run dev -- --port $(UI_PORT) > "$(LOG_DIR)/web-ui.log" 2>&1 & echo $$! > "$(PID_DIR)/web-ui.pid"); \
		echo "    web-ui started (logs: .logs/web-ui.log)"; \
	fi
	@printf "Waiting for AI Service (:$(AI_PORT)) and Core Gateway (:$(GATEWAY_PORT)) to be ready"
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do \
		if curl -sf http://127.0.0.1:$(AI_PORT)/health >/dev/null 2>&1 && curl -sf http://127.0.0.1:$(GATEWAY_PORT)/api/v1/health >/dev/null 2>&1; then \
			break; \
		fi; \
		printf "."; \
		sleep 1; \
	done
	@echo " READY!"
	@echo ""
	@echo "All services launched!"
	@echo "  - Web UI:       http://localhost:$(UI_PORT)"
	@echo "  - Core Gateway: http://localhost:$(GATEWAY_PORT)/api/v1/health"
	@echo "  - AI Service:   http://localhost:$(AI_PORT)/docs"
	@echo "Run 'make status' to check readiness or 'make logs' to tail logs."

stop: ## Stop all background services
	@echo "Stopping Local RAG services..."
	@for svc in web-ui core-service ai-service; do \
		if [ -f $(PID_DIR)/$$svc.pid ]; then \
			pid=$$(cat $(PID_DIR)/$$svc.pid); \
			if kill -0 $$pid 2>/dev/null; then \
				pkill -P $$pid 2>/dev/null || true; \
				kill $$pid 2>/dev/null || true; \
			fi; \
			rm -f $(PID_DIR)/$$svc.pid; \
		fi; \
	done
	@for port in $(UI_PORT) $(GATEWAY_PORT) $(AI_PORT); do \
		pids=$$(lsof -ti :$$port -sTCP:LISTEN 2>/dev/null || true); \
		if [ -n "$$pids" ]; then \
			kill $$pids 2>/dev/null || true; \
			echo "  Stopped service on port :$$port (PID $$pids)"; \
		fi; \
	done
	@sleep 1

restart: stop start ## Restart all 3 services

status: ## Check live status of Ollama, AI Service, Core Gateway, and Web UI
	@echo "=== Local RAG Service Status ==="
	@printf "  Ollama       (:11434): "; curl -sf http://127.0.0.1:11434/api/tags >/dev/null && echo "RUNNING" || echo "STOPPED"
	@printf "  AI Service   (:$(AI_PORT)) : "; curl -sf http://127.0.0.1:$(AI_PORT)/health >/dev/null && echo "HEALTHY" || echo "STOPPED"
	@printf "  Core Gateway (:$(GATEWAY_PORT)) : "; curl -sf http://127.0.0.1:$(GATEWAY_PORT)/api/v1/health >/dev/null && echo "HEALTHY" || echo "STOPPED"
	@printf "  Web UI       (:$(UI_PORT)) : "; curl -sf http://localhost:$(UI_PORT) >/dev/null && echo "RUNNING" || echo "STOPPED"

logs: ## Tail logs from all 3 services
	@tail -f $(LOG_DIR)/*.log

test: test-ai test-core test-ui ## Run tests and build checks across all 3 tiers
	@echo ""
	@echo "ALL 3 TIERS PASSED TESTS & BUILD VERIFICATION!"

test-ai: ## Run Python AI Service pipeline unit tests
	@echo "=== Testing Python AI Service ==="
	cd services/ai-service && uv run python tests/test_pipeline.py

test-core: ## Run Java 21 Core Service JUnit tests
	@echo "=== Testing Java Core Service ==="
	cd services/core-service && ./mvnw test

test-ui: ## Run TypeScript typecheck and Vite production build
	@echo "=== Verifying TypeScript + React Web UI ==="
	cd services/web-ui && npm run build

docker-up: ## Build and start all services via Docker Compose
	docker compose up --build -d

docker-down: ## Stop Docker Compose services
	docker compose down
