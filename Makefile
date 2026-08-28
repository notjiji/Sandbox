.PHONY: up down build migrate migrate-down seed logs shell backend-logs monitoring test prod-up prod-down prod-migrate prod-build

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

seed:
	docker compose exec backend python scripts/seed_demo.py

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

test:
	cd backend && pip install -q -r requirements-dev.txt && python -m pytest tests app -q

prod-build:
	docker compose -f docker-compose.prod.yml build

prod-migrate:
	docker compose -f docker-compose.prod.yml run --rm migrate

prod-up:
	docker compose -f docker-compose.prod.yml up -d

prod-down:
	docker compose -f docker-compose.prod.yml down
