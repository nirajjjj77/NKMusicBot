# Telegram Music Bot Makefile

.PHONY: help install setup run clean test docker docker-run docker-stop backup restore dev lint format

# Default target
help:
	@echo "🎵 Telegram Music Bot - Available Commands:"
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make install     - Install dependencies"
	@echo "  make setup       - Run setup script"
	@echo "  make dev         - Setup development environment"
	@echo ""
	@echo "🚀 Running:"
	@echo "  make run         - Start the bot"
	@echo "  make daemon      - Start bot as daemon (Linux)"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker      - Build Docker image"
	@echo "  make docker-run  - Run with Docker"
	@echo "  make docker-stop - Stop Docker container"
	@echo ""
	@echo "🔧 Maintenance:"
	@echo "  make clean       - Clean up files"
	@echo "  make backup      - Backup database"
	@echo "  make restore     - Restore from backup"
	@echo "  make logs        - Show bot logs"
	@echo ""
	@echo "🧪 Development:"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting"
	@echo "  make format      - Format code"

# Installation
install:
	@echo "📦 Installing dependencies..."
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

setup:
	@echo "🚀 Running setup script..."
	@python3 setup.py
	@chmod +x run.sh
	@echo "✅ Setup completed!"

dev: install
	@echo "🔧 Setting up development environment..."
	@pip install -r requirements-dev.txt 2>/dev/null || echo "No dev requirements found"
	@echo "✅ Development environment ready!"

# Running
run:
	@echo "🎵 Starting Telegram Music Bot..."
	@./run.sh

daemon:
	@echo "🔄 Starting bot as daemon..."
	@nohup python3 main.py > logs/bot.log 2>&1 &
	@echo "✅ Bot started in background (PID: $(shell pgrep -f "python3 main.py"))"

stop:
	@echo "⏹️ Stopping bot..."
	@pkill -f "python3 main.py" || echo "Bot not running"
	@echo "✅ Bot stopped!"

restart: stop
	@sleep 2
	@make daemon

# Docker
docker:
	@echo "🐳 Building Docker image..."
	@docker build -t telegram-music-bot .
	@echo "✅ Docker image built!"

docker-run:
	@echo "🐳 Starting bot with Docker..."
	@docker-compose up -d
	@echo "✅ Bot started with Docker!"

docker-stop:
	@echo "🐳 Stopping Docker containers..."
	@docker-compose down
	@echo "✅ Docker containers stopped!"

docker-logs:
	@echo "📋 Docker logs:"
	@docker-compose logs -f musicbot

# Maintenance
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf __pycache__/
	@rm -rf */__pycache__/
	@rm -rf */*/__pycache__/
	@rm -rf .pytest_cache/
	@rm -rf *.pyc
	@rm -rf */*.pyc
	@rm -rf */*/*.pyc
	@find downloads/ -name "*.mp3" -mtime +1 -delete 2>/dev/null || true
	@find downloads/ -name "*.webm" -mtime +1 -delete 2>/dev/null || true
	@echo "✅ Cleanup completed!"

backup:
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@cp musicbot.db backups/musicbot_$(shell date +%Y%m%d_%H%M%S).db
	@echo "✅ Database backed up to backups/"

restore:
	@echo "📥 Available backups:"
	@ls -la backups/*.db 2>/dev/null || echo "No backups found"
	@read -p "Enter backup filename: " backup && cp backups/$$backup musicbot.db
	@echo "✅ Database restored!"

logs:
	@echo "📋 Bot logs (last 50 lines):"
	@tail -50 logs/bot.log 2>/dev/null || tail -50 bot.log 2>/dev/null || echo "No logs found"

# Development
test:
	@echo "🧪 Running tests..."
	@python3 -m pytest tests/ -v 2>/dev/null || echo "No tests found or pytest not installed"

lint:
	@echo "🔍 Running linting..."
	@python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics 2>/dev/null || echo "flake8 not installed"
	@python3 -m pylint *.py 2>/dev/null || echo "pylint not installed"

format:
	@echo "✨ Formatting code..."
	@python3 -m black . 2>/dev/null || echo "black not installed"
	@python3 -m isort . 2>/dev/null || echo "isort not installed"

# Status
status:
	@echo "📊 Bot Status:"
	@echo "Python: $(shell python3 --version)"
	@echo "FFmpeg: $(shell ffmpeg -version 2>/dev/null | head -1 || echo 'Not installed')"
	@echo "Bot Process: $(shell pgrep -f "python3 main.py" > /dev/null && echo 'Running ✅' || echo 'Stopped ❌')"
	@echo "Database: $(shell [ -f musicbot.db ] && echo 'Found ✅' || echo 'Not found ❌')"
	@echo "Config: $(shell [ -f .env ] && echo 'Found ✅' || echo 'Not found ❌')"

# Update
update:
	@echo "🔄 Updating bot..."
	@git pull origin main || echo "Not a git repository"
	@pip install -r requirements.txt --upgrade
	@echo "✅ Bot updated!"

# Quick commands
start: run
build: docker
up: docker-run
down: docker-stop