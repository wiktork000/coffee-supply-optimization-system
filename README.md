# Coffee Supply Optimization System

A full-stack system for managing coffee supply in a multi-location office environment.

The application allows an office coordinator to manage buildings, distributors, inventory and orders, while distributors can update their own price lists through a self-service portal. The system also includes a separate optimization service that computes an order plan using a MILP model.

This project was developed as an academic team project and focuses on backend/frontend integration, relational data storage, containerized services and optimization-based decision support.

## Key Features

* Coordinator panel for managing buildings, distributors, inventory, orders and optimization scenarios.
* Distributor portal with API key based login and self-service price list management.
* FastAPI backend responsible for authentication, catalog management, order handling and optimization orchestration.
* Separate FastAPI optimization service using AMPL and CBC.
* PostgreSQL database with persistent domain data and optimization results.
* Docker Compose setup for running the full system locally.

## Architecture

| Component          | Role                                                                                             | Technology                                         |
| ------------------ | ------------------------------------------------------------------------------------------------ | -------------------------------------------------- |
| Frontend SPA       | Coordinator and distributor UI                                                                   | React, Vite, TypeScript                            |
| `coffee_manager`   | Main business service: authentication, CRUD, orders, distributor API, optimization orchestration | Python 3.12, FastAPI, SQLAlchemy, Pydantic, Poetry |
| `coffee_optimizer` | Stateless optimization service building and solving a MILP model                                 | Python 3.12, FastAPI, AMPL, CBC                    |
| PostgreSQL         | Persistent storage for domain data and optimization results                                      | PostgreSQL 15                                      |

Main communication flow:

```text
Browser → React frontend → coffee_manager API → PostgreSQL
                                      ↓
                              coffee_optimizer API
```

The manager API exposes REST endpoints and OpenAPI documentation. Distributor self-service endpoints use the `X-API-Key` header.



## My Role and Contributions

My main responsibility was the distributor-facing part of the system and its integration with the backend.

I designed and implemented the distributor portal, including:

* API key based distributor login,
* distributor self-service panel,
* price list editing,
* weekly price creation for the planning horizon,
* discount tier management,
* delivery parameter management per building,
* saving distributor updates through authenticated backend requests.

I also worked on the backend/frontend integration for the distributor workflow. This included extending the self-service API, connecting the distributor panel to real backend data instead of mock data, handling `X-API-Key` authentication, validating real `building_id` values and ensuring that delivery parameters are saved consistently in the database.

Besides the distributor portal itself, I contributed to project integration work: debugging backend/frontend communication, fixing local development issues, improving the API client usage on the frontend, testing end-to-end flows manually and coordinating changes with the rest of the team after merging the coordinator panel branch.

The final distributor workflow supports the following scenario:

1. The coordinator creates a distributor.
2. The coordinator generates an API key for that distributor.
3. The distributor logs in with the generated API key.
4. The distributor edits prices, availability, discount tiers and delivery parameters.
5. The changes are saved through the backend and persisted in PostgreSQL.



### Run with Docker Compose

```bash
docker compose up --build
```

Default local services:

* Frontend: `http://localhost:5173`
* Manager API: `http://localhost:8000`
* Manager API docs: `http://localhost:8000/docs`
* Optimizer API: `http://localhost:8001`
* PostgreSQL: `localhost:5432`


## Tech Stack

**Frontend:** React, Vite, TypeScript, Tremor UI
**Backend:** Python 3.12, FastAPI, SQLAlchemy, Pydantic, Poetry
**Optimization:** Python 3.12, FastAPI, AMPL, CBC
**Database:** PostgreSQL 15
**Infrastructure:** Docker, Docker Compose, GitHub Actions
