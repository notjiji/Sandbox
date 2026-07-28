.PHONY: up down migrate migrate-down logs shell

up:
	docker compose up -d postgres redis

down:
	docker compose down

migrate:
	cd backend && alembic upgrade head

migrate-down:
	cd backend && alembic downgrade -1

logs:
	docker compose logs -f

shell:
	docker compose exec backend bash
