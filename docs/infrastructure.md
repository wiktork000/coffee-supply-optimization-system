# Infrastructure

System overview of the Coffee Ordering System and how its components are deployed.

![Architektura](diagrams/architecture.png)

*Source: [`diagrams/architecture.drawio`](diagrams/architecture.drawio). For the full UML breakdown (component / deployment / class diagrams) see [`architecture.md`](architecture.md).*

## Components

| Component | Tech | Port | Container | Role |
|---|---|---|---|---|
| Frontend | Vite + React (dev server) | 5173 | `coffee_manager_frontend` | UI for office managers |
| `coffee_manager` API | Python · FastAPI · SQLAlchemy · Poetry | 8000 | `coffee_manager_api` | Business API: auth, buildings, distributors, inventory, orders, optimization orchestration |
| `coffee_optimizer` API | Python · FastAPI · amplpy · CBC | 8001 | `coffee_optimizer_api` | Stateless service that builds an AMPL MILP from the request payload and returns the optimal order plan |
| PostgreSQL | PostgreSQL 15 (alpine) | 5432 | `coffee_postgres_db` | Persists all domain state |

All four run under a single `docker-compose.yml` at the repo root.

## Networking

- The frontend talks to `coffee_manager` over HTTP/REST (JSON).
- `coffee_manager` talks to `coffee_optimizer` over HTTP using `httpx` (60 s timeout) at `${OPTIMIZER_URL}/optimize`.
- `coffee_manager` talks to PostgreSQL using SQLAlchemy ORM with eager loading (`selectinload`) for related collections.
- `coffee_optimizer` is stateless — it does not touch the database. It receives a self-contained payload and returns the solver result.

## Persistence

- Postgres data lives in the `postgres_data` named volume.
- `coffee_manager/database/schema.sql` and `seed.sql` are mounted into `/docker-entrypoint-initdb.d/` and applied on first DB start.
- `frontend_node_modules` named volume isolates host/container `node_modules`.

## Configuration

- `.env` at repo root provides Postgres credentials, JWT secret, and `OPTIMIZER_URL`.
- `coffee_manager.config.settings` reads env vars; `OPTIMIZER_URL` is used by `routers/optimization.py`.
- In-compose hostnames: backend reaches the DB at `db:5432` and the optimizer at `optimizer:8001`.

## Build & run

```bash
docker compose up --build         # bring up db + manager + optimizer + frontend
docker compose logs -f backend    # tail manager logs
```

Poetry is used inside each Python image to install dependencies from `pyproject.toml` / `poetry.lock`.

## Health

- `GET /health` on `coffee_manager` (port 8000)
- `GET /health` on `coffee_optimizer` (port 8001)
