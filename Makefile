.PHONY: help build up down restart logs health test lint clean tunnel

help:
	@echo "EchoMCP — Management Commands"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all containers in background"
	@echo "  make down     - Stop all containers"
	@echo "  make restart  - Restart all containers"
	@echo "  make logs     - View follow container logs"
	@echo "  make health   - Query health status of all containers"
	@echo "  make test     - Run test suite"
	@echo "  make clean    - Remove build artifacts and temporary files"
	@echo "  make tunnel   - Start Cloudflare quick tunnel to MCP server"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f

health:
	@bash scripts/health.sh

test:
	@bash scripts/test.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

tunnel:
	@bash scripts/tunnel.sh
