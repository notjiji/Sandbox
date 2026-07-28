.PHONY: up down build migrate migrate-down logs shell backend-logs monitoring

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose exec backend alembic upgrade head

migrate-down:
	docker compose exec backend alembic downgrade -1

logs:
	docker compose logs -f

backend-logs:
	docker compose logs -f backend celery-worker celery-beat

shell:
	docker compose exec backend bash

monitoring:
	@echo "Grafana:  http://localhost:$${GRAFANA_PORT:-3000}"
	@echo "Prometheus: http://localhost:9090"
	@echo "Loki:     http://localhost:3100"
