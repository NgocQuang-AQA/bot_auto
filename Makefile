# Bot Slack Service Makefile
# This Makefile provides convenient commands for development, testing, and deployment

.PHONY: help install dev test lint format build deploy clean docker-build docker-run docker-stop

# Default target
help: ## Show this help message
	@echo "Bot Slack Service - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make install     # Install dependencies"
	@echo "  make dev         # Start development server"
	@echo "  make test        # Run all tests"
	@echo "  make deploy-staging  # Deploy to staging"

# ===========================================
# DEVELOPMENT COMMANDS
# ===========================================

install: ## Install Python dependencies
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt 2>/dev/null || echo "No dev requirements found"
	@echo "✅ Dependencies installed"

install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip install pytest pytest-cov pytest-flask flake8 black isort safety bandit
	@echo "✅ Development dependencies installed"

dev: ## Start development server
	@echo "🚀 Starting development server..."
	python run.py --mode dev

dev-docker: ## Start development server with Docker
	@echo "🐳 Starting development server with Docker..."
	docker-compose -f deployment/docker-compose.yml -f deployment/docker-compose.override.yml up --build

shell: ## Start Python shell with app context
	@echo "🐍 Starting Python shell..."
	python -c "from app.main import create_app; app = create_app(); app.app_context().push(); print('App context loaded. Use app variable.')"

# ===========================================
# TESTING COMMANDS
# ===========================================

test: ## Run all tests
	@echo "🧪 Running all tests..."
	python -m pytest test_api.py -v

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	python -m pytest test_api.py::TestSlackBotAPI -v

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	python -m pytest test_api.py::TestIntegration -v

test-coverage: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	python -m pytest test_api.py -v --cov=app --cov=services --cov=utils --cov-report=html --cov-report=term
	@echo "📋 Coverage report generated in htmlcov/index.html"

test-watch: ## Run tests in watch mode
	@echo "👀 Running tests in watch mode..."
	python -m pytest test_api.py -v --tb=short -x --looponfail

# ===========================================
# CODE QUALITY COMMANDS
# ===========================================

lint: ## Run code linting
	@echo "🔍 Running code linting..."
	flake8 app/ services/ utils/ --max-line-length=88 --exclude=__pycache__
	@echo "✅ Linting completed"

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	black app/ services/ utils/
	isort app/ services/ utils/
	@echo "✅ Code formatted"

format-check: ## Check code formatting without making changes
	@echo "🔍 Checking code formatting..."
	black --check app/ services/ utils/
	isort --check-only app/ services/ utils/

type-check: ## Run type checking (if mypy is installed)
	@echo "🔍 Running type checking..."
	mypy app/ services/ utils/ 2>/dev/null || echo "mypy not installed, skipping type check"

quality: lint format-check type-check ## Run all code quality checks

# ===========================================
# SECURITY COMMANDS
# ===========================================

security: ## Run security checks
	@echo "🔒 Running security checks..."
	safety check -r requirements.txt
	bandit -r app/ services/ utils/ -f json -o bandit-report.json || true
	@echo "📋 Security report generated: bandit-report.json"

security-deps: ## Check dependencies for vulnerabilities
	@echo "🔒 Checking dependencies for vulnerabilities..."
	safety check -r requirements.txt

security-code: ## Run static code security analysis
	@echo "🔒 Running static code security analysis..."
	bandit -r app/ services/ utils/

# ===========================================
# DOCKER COMMANDS
# ===========================================

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	@if exist "build-docker.ps1" ( \
		powershell -ExecutionPolicy Bypass -File build-docker.ps1; \
	) else ( \
		docker build -t bot-slack:latest -f deployment/Dockerfile .; \
	)
	@echo "✅ Docker image built: bot-slack:latest"

docker-build-windows: ## Build Docker image using Windows batch script
	@echo "🐳 Building Docker image using Windows batch script..."
	@if exist "build-docker.bat" ( \
		build-docker.bat; \
	) else ( \
		echo "build-docker.bat not found. Use 'make docker-build' instead."; \
	)

docker-build-dev: ## Build Docker image for development
	@echo "🐳 Building development Docker image..."
	@if exist "build-docker.ps1" ( \
		powershell -ExecutionPolicy Bypass -File build-docker.ps1 -Tag dev -Environment development -NoBuildCache; \
	) else ( \
		docker build --no-cache -t bot-slack:dev -f deployment/Dockerfile .; \
	)
	@echo "✅ Development Docker image built: bot-slack:dev"

docker-run: ## Run Docker container
	@echo "🐳 Running Docker container..."
	docker run -d --name bot-slack-container -p 5000:5000 --env-file .env bot-slack:latest
	@echo "✅ Container started: bot-slack-container"

docker-run-dev: ## Run Docker container in development mode
	@echo "🐳 Running Docker container in development mode..."
	docker run -d -p 5000:5000 -p 5678:5678 --env-file .env -e FLASK_DEBUG=true -e LOG_LEVEL=DEBUG --name bot-slack-dev bot-slack:dev
	@echo "✅ Development container started: bot-slack-dev"

docker-stop: ## Stop and remove Docker container
	@echo "🐳 Stopping Docker container..."
	docker stop bot-slack-container 2>/dev/null || true
	docker rm bot-slack-container 2>/dev/null || true
	@echo "✅ Container stopped and removed"

docker-stop-dev: ## Stop and remove development Docker container
	@echo "🐳 Stopping development Docker container..."
	docker stop bot-slack-dev 2>/dev/null || true
	docker rm bot-slack-dev 2>/dev/null || true
	@echo "✅ Development container stopped and removed"

docker-logs: ## Show Docker container logs
	@echo "📋 Showing container logs..."
	docker logs -f bot-slack-container

docker-logs-dev: ## Show development Docker container logs
	@echo "📋 Showing development container logs..."
	docker logs -f bot-slack-dev

docker-shell: ## Access Docker container shell
	@echo "🐚 Accessing container shell..."
	docker exec -it bot-slack-container /bin/bash

docker-shell-dev: ## Access development Docker container shell
	@echo "🐚 Accessing development container shell..."
	docker exec -it bot-slack-dev /bin/bash

docker-compose-up: ## Start services with docker-compose
	@echo "🐳 Starting services with docker-compose..."
	cd deployment && docker-compose up -d
	@echo "✅ Services started"

docker-compose-up-dev: ## Start development services with docker-compose
	@echo "🐳 Starting development services with docker-compose..."
	cd deployment && docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
	@echo "✅ Development services started"

docker-compose-down: ## Stop services with docker-compose
	@echo "🐳 Stopping services with docker-compose..."
	cd deployment && docker-compose down
	@echo "✅ Services stopped"

docker-images: ## List bot-slack Docker images
	@echo "📋 Listing bot-slack Docker images..."
	docker images bot-slack

docker-compose-logs: ## Show docker-compose logs
	@echo "📋 Showing docker-compose logs..."
	cd deployment && docker-compose logs -f

docker-clean: ## Clean up Docker resources
	@echo "🧹 Cleaning up Docker resources..."
	docker system prune -f
	docker volume prune -f
	@echo "✅ Docker cleanup completed"

# ===========================================
# DEPLOYMENT COMMANDS
# ===========================================

deploy-staging: ## Deploy to staging environment
	@echo "🚀 Deploying to staging..."
	./deployment/deploy.sh staging deploy

deploy-production: ## Deploy to production environment
	@echo "🚀 Deploying to production..."
	./deployment/deploy.sh production deploy

rollback-staging: ## Rollback staging deployment
	@echo "🔄 Rolling back staging..."
	./deployment/deploy.sh staging rollback

rollback-production: ## Rollback production deployment
	@echo "🔄 Rolling back production..."
	./deployment/deploy.sh production rollback

status-staging: ## Check staging deployment status
	@echo "📊 Checking staging status..."
	./deployment/deploy.sh staging status

status-production: ## Check production deployment status
	@echo "📊 Checking production status..."
	./deployment/deploy.sh production status

health-check: ## Perform health check
	@echo "🏥 Performing health check..."
	curl -f http://localhost:5000/health || echo "Health check failed"

backup: ## Create backup
	@echo "💾 Creating backup..."
	./deployment/deploy.sh production backup

# ===========================================
# ENVIRONMENT COMMANDS
# ===========================================

env-setup: ## Setup environment file
	@echo "⚙️ Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Created .env file from .env.example"; \
		echo "⚠️ Please edit .env file with your configuration"; \
	else \
		echo "✅ .env file already exists"; \
	fi

env-validate: ## Validate environment configuration
	@echo "✅ Validating environment configuration..."
	@python -c "from config.settings import *; print('Environment configuration is valid')"

requirements-update: ## Update requirements.txt
	@echo "📦 Updating requirements.txt..."
	pip freeze > requirements.txt
	@echo "✅ Requirements updated"

requirements-check: ## Check for outdated packages
	@echo "🔍 Checking for outdated packages..."
	pip list --outdated

# ===========================================
# UTILITY COMMANDS
# ===========================================

clean: ## Clean up temporary files
	@echo "🧹 Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf bandit-report.json
	@echo "✅ Cleanup completed"

logs: ## Show application logs
	@echo "📋 Showing application logs..."
	tail -f logs/app.log 2>/dev/null || echo "No log file found"

monitor: ## Monitor application (requires htop)
	@echo "📊 Monitoring application..."
	htop -p $(pgrep -f "python.*run.py" | tr '\n' ',')

ports: ## Show ports in use
	@echo "🔌 Showing ports in use..."
	netstat -tulpn | grep :5000 || echo "Port 5000 is not in use"

size: ## Show project size
	@echo "📏 Project size:"
	du -sh .
	echo ""
	echo "📁 Directory breakdown:"
	du -sh */ 2>/dev/null || true

# ===========================================
# CI/CD COMMANDS
# ===========================================

ci-build: docker-build ## CI: Build step

ci-test: test-coverage security ## CI: Test step

ci-deploy: ## CI: Deploy step (requires environment)
	@echo "🚀 CI Deploy step..."
	@if [ "$(ENV)" = "staging" ]; then \
		make deploy-staging; \
	elif [ "$(ENV)" = "production" ]; then \
		make deploy-production; \
	else \
		echo "❌ ENV variable must be set to 'staging' or 'production'"; \
		exit 1; \
	fi

ci-full: clean install ci-test ci-build ## CI: Full pipeline

# ===========================================
# DOCUMENTATION COMMANDS
# ===========================================

docs-serve: ## Serve documentation locally
	@echo "📚 Serving documentation..."
	@if command -v python -m http.server >/dev/null 2>&1; then \
		cd docs && python -m http.server 8080; \
	else \
		echo "Python HTTP server not available"; \
	fi

docs-build: ## Build documentation (if using Sphinx or similar)
	@echo "📚 Building documentation..."
	@echo "Documentation build not configured yet"

# ===========================================
# MAINTENANCE COMMANDS
# ===========================================

update: ## Update all dependencies
	@echo "🔄 Updating dependencies..."
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	make requirements-update
	@echo "✅ Dependencies updated"

check-health: ## Check application health
	@echo "🏥 Checking application health..."
	@python -c "import requests; r = requests.get('http://localhost:5000/health'); print(f'Status: {r.status_code}'); print(f'Response: {r.text}')" 2>/dev/null || echo "❌ Health check failed - is the server running?"

check-deps: ## Check dependency tree
	@echo "🌳 Checking dependency tree..."
	pipdeptree 2>/dev/null || pip install pipdeptree && pipdeptree

info: ## Show project information
	@echo "ℹ️ Bot Slack Service Information"
	@echo "================================"
	@echo "Python Version: $(shell python --version)"
	@echo "Pip Version: $(shell pip --version)"
	@echo "Docker Version: $(shell docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Git Branch: $(shell git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo "Git Commit: $(shell git rev-parse --short HEAD 2>/dev/null || echo 'Not a git repository')"
	@echo "Project Size: $(shell du -sh . | cut -f1)"
	@echo "Last Modified: $(shell stat -c %y . 2>/dev/null || stat -f %Sm .)"

# ===========================================
# ALIASES
# ===========================================

run: dev ## Alias for dev
start: dev ## Alias for dev
stop: docker-stop ## Alias for docker-stop
restart: docker-stop docker-run ## Restart Docker container
build: docker-build ## Alias for docker-build
up: docker-compose-up ## Alias for docker-compose-up
down: docker-compose-down ## Alias for docker-compose-down