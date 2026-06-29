# API Reference

The system exposes two HTTP APIs. Full machine-readable spec for the public surface is in [`/swagger.yaml`](../swagger.yaml). This page is the human-readable summary.

- **`coffee_manager`** — base URL `http://localhost:8000` — the API consumed by the frontend.
- **`coffee_optimizer`** — base URL `http://localhost:8001` — internal-only; called by `coffee_manager`.

## Authentication

`coffee_manager` accepts two credential types on protected endpoints:

| Mechanism | Header | Obtained via |
|---|---|---|
| JWT | `Authorization: Bearer <token>` | `POST /auth/login` |
| API key | `X-API-Key: <key>` | `POST /api-keys` (returned once at creation) |

`/health` and `/auth/login` are public.

## `coffee_manager` endpoints

### System / auth

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness probe |
| POST | `/auth/login` | Exchange username + password for a JWT |
| POST | `/auth/register` | Create a user |

### API keys

| Method | Path | Purpose |
|---|---|---|
| GET | `/api-keys` | List API keys for the current user |
| POST | `/api-keys` | Create a new key (plaintext returned once) |
| DELETE | `/api-keys/{key_id}` | Revoke a key |

### Buildings

| Method | Path | Purpose |
|---|---|---|
| GET | `/buildings` | List buildings (with daily demand) |
| POST | `/buildings` | Create a building |
| GET | `/buildings/{building_id}` | Get a building |
| PUT | `/buildings/{building_id}` | Update a building |
| DELETE | `/buildings/{building_id}` | Delete a building |

### Distributors

| Method | Path | Purpose |
|---|---|---|
| GET | `/distributors` | List distributors (with daily prices, discount tiers, delivery params) |
| POST | `/distributors` | Create a distributor |
| GET | `/distributors/{distributor_id}` | Get one |
| PUT | `/distributors/{distributor_id}` | Update one |
| DELETE | `/distributors/{distributor_id}` | Delete one |

### Inventory

| Method | Path | Purpose |
|---|---|---|
| GET | `/inventory` | Current stock per building |
| PUT | `/inventory/{building_id}` | Adjust stock for a building |

### Orders

| Method | Path | Purpose |
|---|---|---|
| GET | `/orders?status=…` | List orders, optionally filtered by status |
| POST | `/orders` | Create an order (initial status `confirmed`) |
| GET | `/orders/{order_id}` | Get an order |
| PATCH | `/orders/{order_id}/status` | Transition status (`confirmed → shipped → delivered`, or `cancelled`) |

### Optimization

| Method | Path | Purpose |
|---|---|---|
| GET | `/optimization` | List past optimization runs |
| POST | `/optimization` | Run a new optimization scenario |
| GET | `/optimization/{result_id}` | Fetch a stored result |

`POST /optimization` request body (`ScenarioCreateRequest`):

```json
{
  "name": "weekly-plan-2026-05-13",
  "planning_horizon_days": 7,
  "decay_rate": 0.05,
  "distributor_ids": ["..."],
  "building_ids": ["..."],
  "historical_orders": { "distributor_id:building_id": 12.0 }
}
```

Response (`OptimizationResponse`): scenario id, result id, status, cost breakdown, and per-day `orders[]` + `inventory_levels[]`.

Error mapping for the optimizer call:

| Status | Cause |
|---|---|
| 400 | Malformed `historical_orders` key |
| 404 | Unknown distributor/building id |
| 502 | Optimizer returned non-2xx |
| 503 | Optimizer unreachable (network error) |

## `coffee_optimizer` endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness probe |
| POST | `/optimize` | Solve an instance of the MILP and return orders + inventory trajectory |

### `POST /optimize`

**Request** (`OptimizationRequest`, in `coffee_optimizer.models`):

- `planning_days: list[int]` — days in the horizon (1-indexed).
- `decay_rate: float` ∈ [0, 1] — daily inventory decay α.
- `distributors[]` — id, `daily_prices[]` (`day, base_price, availability_kg, discount_tiers[]`), `delivery_params[]` (`building_id, lead_time_days, fixed_cost_pln`).
- `buildings[]` — id, `max_capacity_kg`, `initial_inventory_kg`, `daily_demand[]`.
- `historical_arrivals[]` — pending shipments arriving inside the horizon.

**Response** (`OptimizationResult`):

- `status`: `Optimal | Infeasible | Unbounded | Not Solved`.
- `total_cost_pln`, `solver_message`.
- `orders[]` — `(distributor_id, building_id, day, threshold_level, quantity_kg)`.
- `inventory_levels[]` — `(building_id, day, level_kg)` for each day in the horizon.

The model uses CBC via amplpy. Definition lives in `coffee_optimizer/optimizer.py`.
