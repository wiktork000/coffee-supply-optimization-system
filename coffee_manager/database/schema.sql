CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'coordinator'
        CHECK (role IN ('coordinator', 'admin'))
);

CREATE TABLE distributors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    contact_email VARCHAR(100) NOT NULL UNIQUE,
    contact_phone VARCHAR(20) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT true,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE distributor_daily_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    day INTEGER NOT NULL CHECK (day >= 1),
    base_price NUMERIC(10,2)NOT NULL CHECK (base_price >= 0),
    availability_kg NUMERIC(10,2)NOT NULL CHECK (availability_kg >= 0),

    UNIQUE (distributor_id, day)
);

CREATE TABLE distributor_discount_tiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    distributor_id UUID NOT NULL,
    day INTEGER NOT NULL CHECK (day >= 1),
    level INTEGER NOT NULL CHECK (level >= 1),
    quantity_kg NUMERIC(10,2) NOT NULL CHECK (quantity_kg >= 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),

    UNIQUE (distributor_id, day, level),
    FOREIGN KEY (distributor_id, day) REFERENCES distributor_daily_prices(distributor_id, day) ON DELETE CASCADE
);

CREATE TABLE buildings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    location TEXT,
    max_capacity_kg NUMERIC(10,2)NOT NULL CHECK (max_capacity_kg >= 0),
    initial_inventory_kg NUMERIC(10,2)NOT NULL DEFAULT 0 CHECK (initial_inventory_kg >= 0),
    current_inventory_kg NUMERIC NOT NULL DEFAULT 0 CHECK (current_inventory_kg >= 0),
    
    CHECK (initial_inventory_kg <= max_capacity_kg),
    CHECK (current_inventory_kg <= max_capacity_kg),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE delivery_params (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    lead_time_days INTEGER NOT NULL DEFAULT 1 CHECK (lead_time_days >= 0),
    fixed_cost_pln NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (fixed_cost_pln >= 0),
    correction_cost_per_kg NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (correction_cost_per_kg >= 0),
    max_correction_kg NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (max_correction_kg >= 0),

    UNIQUE (distributor_id, building_id)
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,
    key_prefix VARCHAR(20) NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    label VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    revoked_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE building_daily_demand (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    day INTEGER NOT NULL CHECK (day >= 1),
    demand_kg NUMERIC(12, 3) NOT NULL CHECK (demand_kg >= 0),

    UNIQUE (building_id, day)
);


CREATE TABLE optimization_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    planning_horizon_days INTEGER NOT NULL DEFAULT 7
        CHECK (planning_horizon_days BETWEEN 1 AND 30),
    decay_rate NUMERIC(5, 4) NOT NULL DEFAULT 0.05
        CHECK (decay_rate >= 0 AND decay_rate <= 1),
    historical_orders JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE optimization_scenario_distributors (
    scenario_id UUID NOT NULL REFERENCES optimization_scenarios(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE CASCADE,

    PRIMARY KEY (scenario_id, distributor_id)
);

CREATE TABLE optimization_scenario_buildings (
    scenario_id UUID NOT NULL REFERENCES optimization_scenarios(id) ON DELETE CASCADE,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,

    PRIMARY KEY (scenario_id, building_id)
);


CREATE TABLE optimization_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id UUID NOT NULL REFERENCES optimization_scenarios(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL
        CHECK (status IN ('Optimal', 'Infeasible', 'Unbounded', 'Not Solved')),
    total_cost_pln NUMERIC(14, 2),
    purchase_base NUMERIC(14, 2),
    purchase_discount NUMERIC(14, 2),
    fixed_delivery NUMERIC(14, 2),
    total NUMERIC(14, 2),
    solver_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE optimization_order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    result_id UUID NOT NULL REFERENCES optimization_results(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE RESTRICT,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE RESTRICT,
    day INTEGER NOT NULL CHECK (day >= 1),
    threshold_level INTEGER NOT NULL DEFAULT 0 CHECK (threshold_level >= 0),
    quantity_kg NUMERIC(12, 3) NOT NULL CHECK (quantity_kg >= 0)
);

CREATE TABLE optimization_inventory_levels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    result_id UUID NOT NULL REFERENCES optimization_results(id) ON DELETE CASCADE,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE RESTRICT,
    day INTEGER NOT NULL CHECK (day >= 1),
    level_kg NUMERIC(12, 3) NOT NULL CHECK (level_kg >= 0),

    UNIQUE (result_id, building_id, day)
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    result_id UUID NOT NULL REFERENCES optimization_results(id) ON DELETE RESTRICT,
    scenario_id UUID NOT NULL REFERENCES optimization_scenarios(id) ON DELETE RESTRICT,
    total_cost_pln NUMERIC(14, 2),
    confirmed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'confirmed'
        CHECK (status IN ('confirmed', 'pending', 'cancelled')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    distributor_id UUID NOT NULL REFERENCES distributors(id) ON DELETE RESTRICT,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE RESTRICT,
    day INTEGER NOT NULL CHECK (day >= 1),
    threshold_level INTEGER NOT NULL DEFAULT 0 CHECK (threshold_level >= 0),
    quantity_kg NUMERIC(12, 3) NOT NULL CHECK (quantity_kg >= 0)
);


CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_distributors_updated_at
BEFORE UPDATE ON distributors
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_buildings_updated_at
BEFORE UPDATE ON buildings
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_api_keys_updated_at
BEFORE UPDATE ON api_keys
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_optimization_scenarios_updated_at
BEFORE UPDATE ON optimization_scenarios
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_optimization_results_updated_at
BEFORE UPDATE ON optimization_results
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_orders_updated_at
BEFORE UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();