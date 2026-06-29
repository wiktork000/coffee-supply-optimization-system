# Workflows

This page documents the end-to-end flows that span multiple components. Diagrams referenced below live in [`diagrams/`](diagrams/) as editable draw.io files.

## 1. Authentication

1. Client `POST /auth/login` with username + password.
2. `coffee_manager` returns a JWT (`LoginResponse`).
3. Client either sends `Authorization: Bearer <token>` on subsequent calls, or creates a long-lived `X-API-Key` via `POST /api-keys` for service-to-service use.

All `coffee_manager` routers depend on `get_current_user`, which accepts either mechanism.

## 2. Catalog / master data setup

Before optimization can produce useful plans, an admin must populate:

- **Buildings** (`POST /buildings`) — each with `max_capacity_kg`, `current_inventory_kg`, and a `daily_demand[]` schedule.
- **Distributors** (`POST /distributors`) — each with `daily_prices[]` (base price, availability, and tiered discounts) and `delivery_params[]` per building (lead time, fixed delivery cost).

These two collections plus the planning horizon define one optimization instance.

## 3. Optimization workflow

![Optimization sequence](diagrams/optimization-workflow.png)

*Source: [`diagrams/optimization-workflow.drawio`](diagrams/optimization-workflow.drawio).*

Sequence triggered by `POST /optimization`:

1. **Auth** — `get_current_user` validates JWT or API key.
2. **Load** — `coffee_manager` fetches the requested distributors (with daily prices, discount tiers, delivery params) and buildings (with daily demand) from PostgreSQL, eager-loading via `selectinload`.
3. **Validate** — 404 if any id is missing; 400 if `historical_orders` keys are not `distributor_id:building_id`.
4. **Build payload** — assembles the JSON the optimizer expects (`planning_days`, normalized distributors, buildings, `decay_rate`, optional `historical_arrivals`).
5. **Call optimizer** — `httpx.post(OPTIMIZER_URL + "/optimize", timeout=60)`. Failures map to 502 (HTTP error) or 503 (network error).
6. **Solve** — `coffee_optimizer.optimizer.run_optimization` loads the AMPL model, binds the data, calls CBC via `amplpy`, and returns `OptimizationResult` (status, orders, inventory trajectory, total cost).
7. **Persist** — `coffee_manager` writes an `OptimizationScenario`, the scenario↔distributor/building bridge rows, an `OptimizationResult`, plus child `OptimizationOrderItem` and `OptimizationInventoryLevel` rows, and commits.
8. **Respond** — reloads the result with `selectinload` and returns an `OptimizationResponse` (scenario id, result id, status, cost breakdown, orders, inventory levels).

### AMPL model (summary)

- **Sets:** `T` (days), `D` (distributors), `B` (buildings), `L` (discount tiers).
- **Decision variables:** `x0[d,b,t]` (base-price purchase), `x[d,b,t,l]` (tier-l purchase), `I[b,t]` (stock), `y_skl` / `y_rab` binaries (order indicator and tier indicator).
- **Objective:** minimize total cost = base purchase + tier purchases + fixed delivery cost.
- **Key constraints:** inventory balance with lead time `LT[d,b]` and decay `alpha`, capacity `V_max`, daily availability `S_avail`, and tier thresholds `Q[l]` linking quantities to the chosen tier binary.

## 4. Order lifecycle

![Order lifecycle](diagrams/order-workflow.png)

*Source: [`diagrams/order-workflow.drawio`](diagrams/order-workflow.drawio).*

1. Manager reviews an optimization result and decides to actually place an order.
2. `POST /orders` creates an order with status `confirmed`.
3. `PATCH /orders/{id}/status` advances the state machine:
   - `confirmed → shipped → delivered`
   - any state → `cancelled`
4. On `delivered`, building inventory is updated (manually via `PUT /inventory/{building_id}` or by application logic, depending on deployment).
5. Updated inventory and the daily demand schedule feed the next optimization run, closing the loop.

## 5. Health & observability

- Both services expose `GET /health`.
- `docker compose logs -f <service>` is the primary debugging channel today.

## 6. Testing flow

Each subproject has its own `tests/` directory. Every feature is covered by both unit tests and integration tests with the rest of the project, executed via Poetry:

```bash
cd coffee_manager   && poetry run pytest
cd coffee_optimizer && poetry run pytest
```
