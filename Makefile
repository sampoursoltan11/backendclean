# Enterprise TRA - Makefile
# Quick commands to manage backend and frontend servers

.PHONY: help install start stop restart clean test build dev backend frontend logs status health

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ Help

help: ## Display this help message
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║           Enterprise TRA - Development Commands           ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: $(GREEN)make <target>$(NC)\n\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Setup & Installation

install: ## Install all dependencies (backend + frontend)
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@echo "$(YELLOW)→ Installing Python dependencies...$(NC)"
	@pip3 install -r requirements.txt 2>&1 | grep -v "already satisfied" || true
	@echo "$(GREEN)✓ Python dependencies installed$(NC)"
	@echo ""
	@echo "$(YELLOW)→ Installing frontend dependencies...$(NC)"
	@cd frontend && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"
	@echo ""
	@echo "$(GREEN)✓ All dependencies installed successfully!$(NC)"

##@ Development

dev: ## Start both backend and frontend in development mode
	@$(MAKE) start

start: ## Start both backend and frontend servers
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║              Starting Enterprise TRA Servers               ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@$(MAKE) start-backend-bg
	@sleep 2
	@$(MAKE) start-frontend-bg
	@sleep 2
	@echo ""
	@$(MAKE) status
	@echo ""
	@echo "$(GREEN)✓ Both servers started successfully!$(NC)"
	@echo ""
	@echo "$(YELLOW)Access the application:$(NC)"
	@echo "  Frontend: $(BLUE)http://localhost:5173/enterprise_tra_home_clean.html$(NC)"
	@echo "  Backend:  $(BLUE)http://localhost:8000/docs$(NC)"
	@echo ""
	@echo "$(YELLOW)Stop servers with:$(NC) $(GREEN)make stop$(NC)"

start-backend-bg: ## Start backend server in background
	@echo "$(YELLOW)→ Starting backend server...$(NC)"
	@if pgrep -f "uvicorn backend.api.main:app" > /dev/null; then \
		echo "$(YELLOW)  Backend already running$(NC)"; \
	else \
		nohup python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 & \
		echo "$(GREEN)  ✓ Backend started (PID: $$!)$(NC)"; \
	fi

start-frontend-bg: ## Start frontend server in background
	@echo "$(YELLOW)→ Starting frontend server...$(NC)"
	@if pgrep -f "vite.*--port 5173" > /dev/null; then \
		echo "$(YELLOW)  Frontend already running$(NC)"; \
	else \
		cd frontend && nohup npx vite --host 0.0.0.0 --port 5173 > ../logs/frontend.log 2>&1 & \
		echo "$(GREEN)  ✓ Frontend started (PID: $$!)$(NC)"; \
	fi

backend: ## Start only the backend server (foreground)
	@echo "$(BLUE)Starting backend server...$(NC)"
	@./scripts/run_backend.sh

frontend: ## Start only the frontend server (foreground)
	@echo "$(BLUE)Starting frontend server...$(NC)"
	@cd frontend && npm run dev

##@ Control

stop: ## Stop both backend and frontend servers
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║              Stopping Enterprise TRA Servers               ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@$(MAKE) stop-backend
	@$(MAKE) stop-frontend
	@echo ""
	@echo "$(GREEN)✓ All servers stopped$(NC)"

stop-backend: ## Stop the backend server
	@echo "$(YELLOW)→ Stopping backend server...$(NC)"
	@pkill -f "uvicorn backend.api.main:app" 2>/dev/null && echo "$(GREEN)  ✓ Backend stopped$(NC)" || echo "$(YELLOW)  Backend not running$(NC)"

stop-frontend: ## Stop the frontend server
	@echo "$(YELLOW)→ Stopping frontend server...$(NC)"
	@pkill -f "vite.*--port 5173" 2>/dev/null && echo "$(GREEN)  ✓ Frontend stopped$(NC)" || echo "$(YELLOW)  Frontend not running$(NC)"

restart: ## Restart both servers
	@echo "$(BLUE)Restarting servers...$(NC)"
	@$(MAKE) stop
	@sleep 1
	@$(MAKE) start

##@ Status & Health

status: ## Show server status
	@echo "$(BLUE)Server Status:$(NC)"
	@echo ""
	@if pgrep -f "uvicorn backend.api.main:app" > /dev/null; then \
		echo "  Backend:  $(GREEN)✓ Running$(NC) (PID: $$(pgrep -f 'uvicorn backend.api.main:app'))"; \
	else \
		echo "  Backend:  $(RED)✗ Not running$(NC)"; \
	fi
	@if pgrep -f "vite.*--port 5173" > /dev/null; then \
		echo "  Frontend: $(GREEN)✓ Running$(NC) (PID: $$(pgrep -f 'vite.*--port 5173'))"; \
	else \
		echo "  Frontend: $(RED)✗ Not running$(NC)"; \
	fi

health: ## Check health of running services
	@echo "$(BLUE)Health Check:$(NC)"
	@echo ""
	@echo "$(YELLOW)→ Backend Health:$(NC)"
	@curl -s http://localhost:8000/api/health | jq '.' 2>/dev/null || echo "  $(RED)✗ Backend not responding$(NC)"
	@echo ""
	@echo "$(YELLOW)→ Frontend Server:$(NC)"
	@curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:5173 || echo "  $(RED)✗ Frontend not responding$(NC)"

logs: ## Show logs from both servers
	@echo "$(BLUE)Recent Logs:$(NC)"
	@echo ""
	@echo "$(YELLOW)=== Backend Logs (last 20 lines) ===$(NC)"
	@tail -20 logs/backend.log 2>/dev/null || echo "$(YELLOW)No backend logs found$(NC)"
	@echo ""
	@echo "$(YELLOW)=== Frontend Logs (last 20 lines) ===$(NC)"
	@tail -20 logs/frontend.log 2>/dev/null || echo "$(YELLOW)No frontend logs found$(NC)"

logs-backend: ## Show backend logs (tail -f)
	@echo "$(BLUE)Backend Logs (Ctrl+C to exit):$(NC)"
	@tail -f logs/backend.log

logs-frontend: ## Show frontend logs (tail -f)
	@echo "$(BLUE)Frontend Logs (Ctrl+C to exit):$(NC)"
	@tail -f logs/frontend.log

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@echo ""
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend: ## Run backend tests
	@echo "$(YELLOW)→ Running backend tests...$(NC)"
	@./scripts/test_backend.sh

test-frontend: ## Run frontend tests
	@echo "$(YELLOW)→ Running frontend tests...$(NC)"
	@node scripts/test_frontend.js

##@ Build

build: ## Build frontend for production
	@echo "$(BLUE)Building frontend for production...$(NC)"
	@cd frontend && npm run build
	@echo "$(GREEN)✓ Build complete! Output in frontend/dist/$(NC)"

preview: ## Preview production build
	@echo "$(BLUE)Starting production preview...$(NC)"
	@cd frontend && npm run preview

##@ Cleanup

clean: ## Clean up logs and temporary files
	@echo "$(YELLOW)→ Cleaning up...$(NC)"
	@rm -f logs/*.log
	@rm -rf frontend/dist
	@rm -rf sessions/*
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean ## Clean everything including node_modules
	@echo "$(YELLOW)→ Removing node_modules...$(NC)"
	@rm -rf frontend/node_modules
	@echo "$(GREEN)✓ Deep cleanup complete$(NC)"

##@ Utilities

open: ## Open application in browser
	@echo "$(BLUE)Opening application...$(NC)"
	@open http://localhost:5173/enterprise_tra_home_clean.html 2>/dev/null || \
	xdg-open http://localhost:5173/enterprise_tra_home_clean.html 2>/dev/null || \
	echo "$(YELLOW)Please open: http://localhost:5173/enterprise_tra_home_clean.html$(NC)"

open-docs: ## Open API documentation in browser
	@echo "$(BLUE)Opening API docs...$(NC)"
	@open http://localhost:8000/docs 2>/dev/null || \
	xdg-open http://localhost:8000/docs 2>/dev/null || \
	echo "$(YELLOW)Please open: http://localhost:8000/docs$(NC)"

ps: ## Show all related processes
	@echo "$(BLUE)Related Processes:$(NC)"
	@echo ""
	@echo "$(YELLOW)Backend:$(NC)"
	@ps aux | grep -E "(uvicorn|backend)" | grep -v grep || echo "  None"
	@echo ""
	@echo "$(YELLOW)Frontend:$(NC)"
	@ps aux | grep -E "(vite|frontend)" | grep -v grep || echo "  None"

env-check: ## Check environment and dependencies
	@echo "$(BLUE)Environment Check:$(NC)"
	@echo ""
	@echo "$(YELLOW)→ Python version:$(NC)"
	@python3 --version
	@echo ""
	@echo "$(YELLOW)→ Node version:$(NC)"
	@node --version
	@echo ""
	@echo "$(YELLOW)→ NPM version:$(NC)"
	@npm --version
	@echo ""
	@echo "$(YELLOW)→ AWS credentials:$(NC)"
	@aws sts get-caller-identity 2>/dev/null || echo "  $(RED)✗ AWS credentials not configured$(NC)"
	@echo ""
	@echo "$(YELLOW)→ DynamoDB table:$(NC)"
	@aws dynamodb describe-table --table-name tra-system --query "Table.TableStatus" 2>/dev/null || echo "  $(RED)✗ Cannot access DynamoDB table$(NC)"

##@ Documentation

docs: ## Show documentation structure
	@echo "$(BLUE)Documentation Structure:$(NC)"
	@echo ""
	@echo "$(YELLOW)Main:$(NC)"
	@echo "  • README.md"
	@echo "  • Makefile"
	@echo ""
	@echo "$(YELLOW)docs/ (organized by category):$(NC)"
	@echo "  • README.md (documentation index)"
	@echo "  • getting-started/ (setup guides)"
	@echo "  • backend/ (optimization, GSI)"
	@echo "  • frontend/ (testing, refactoring)"
	@echo "  • infrastructure/ (IaC docs)"
	@echo "  • testing/ (test results)"
	@echo "  • project/ (summaries)"
	@echo ""
	@echo "$(GREEN)View full index:$(NC) docs/README.md"

##@ Quick Start

quickstart: install start open ## Complete setup: install, start, and open

##@ Advanced

shell-backend: ## Open Python shell with backend context
	@echo "$(BLUE)Opening Python shell...$(NC)"
	@python3 -c "from backend.api.main import *; import IPython; IPython.embed()"

db-status: ## Check DynamoDB table status
	@echo "$(BLUE)DynamoDB Status:$(NC)"
	@aws dynamodb describe-table --table-name tra-system --query "Table.{TableName:TableName,Status:TableStatus,ItemCount:ItemCount,TableSize:TableSizeBytes,GSI:GlobalSecondaryIndexes[*].{Name:IndexName,Status:IndexStatus}}" --output json | jq '.'

s3-status: ## Check S3 bucket status
	@echo "$(BLUE)S3 Bucket Status:$(NC)"
	@aws s3 ls s3://bhp-tra-agent-docs-poc --summarize --human-readable --recursive | tail -3

##@ Default

.DEFAULT_GOAL := help
