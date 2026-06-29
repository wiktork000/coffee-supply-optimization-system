.PHONY: build run stop restart logs ps clean rebuild db-init db-seed db-reset

build:
	docker compose build

run:
	docker compose up -d
	@echo "Waiting for DB to be ready..."
	@until docker exec coffee_postgres_db pg_isready -U coffee_user -d coffee_db -q; do sleep 1; done
	$(MAKE) db-init

stop:
	docker compose down

restart:
	docker compose down
	docker compose up -d
	@echo "Waiting for DB to be ready..."
	@until docker exec coffee_postgres_db pg_isready -U coffee_user -d coffee_db -q; do sleep 1; done
	$(MAKE) db-init

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v

rebuild:
	docker compose build --no-cache
	docker compose up -d

db-init:
	@echo "Waiting for backend to be ready..."
	@until curl -sf http://localhost:8000/health > /dev/null 2>&1; do sleep 1; done
	@docker exec -i coffee_manager_api python3 - < coffee_manager/scripts/create_admin.py

db-seed:
	docker exec -i coffee_postgres_db psql -U coffee_user -d coffee_db -f /docker-entrypoint-initdb.d/02-seed.sql
	docker exec -i coffee_postgres_db psql -U coffee_user -d coffee_db < coffee_manager/seed_orders.sql

db-reset:
	docker compose down
	docker volume rm coffeeorderingsystem_postgres_data 2>/dev/null || true
	docker compose up -d
	@echo "Waiting for DB to be ready..."
	@until docker exec coffee_postgres_db pg_isready -U coffee_user -d coffee_db -q; do sleep 1; done
	$(MAKE) db-init