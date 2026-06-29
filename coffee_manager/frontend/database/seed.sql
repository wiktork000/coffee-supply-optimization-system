-- Seed data for showcasing the Coffee Ordering System endpoints.
-- Idempotent: re-running will not duplicate rows.
--
-- Apply with:
--   docker compose exec -T db psql -U coffee_user -d coffee_db < coffee_manager/database/seed.sql
--
-- Users and API keys are NOT seeded here (passwords/keys need bcrypt hashes).
-- Create them via the API:
--   POST /auth/register            (creates a user; returns JWT)
--   POST /distributors/{id}/api-keys  (creates an API key for distributor self-service)

BEGIN;

-- ---------------------------------------------------------------------------
-- Distributors
-- ---------------------------------------------------------------------------
INSERT INTO distributors (id, username, contact_email, contact_phone, active) VALUES
  ('11111111-1111-1111-1111-111111111111', 'arabica_traders', 'sales@arabica.example',  '+48111111111', true),
  ('22222222-2222-2222-2222-222222222222', 'robusta_supply',  'orders@robusta.example', '+48222222222', true)
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Buildings
-- ---------------------------------------------------------------------------
INSERT INTO buildings (id, name, location, max_capacity_kg, initial_inventory_kg, current_inventory_kg) VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'HQ Warsaw',  'Warsaw, ul. Koszykowa 75', 200.00, 30.00, 30.00),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Office Krk', 'Krakow, ul. Wielicka 28',  150.00, 20.00, 20.00)
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Distributor daily prices (days 1..7 for the planning horizon)
-- ---------------------------------------------------------------------------
INSERT INTO distributor_daily_prices (distributor_id, day, base_price, availability_kg) VALUES
  -- Arabica Traders
  ('11111111-1111-1111-1111-111111111111', 1, 55.00, 120.00),
  ('11111111-1111-1111-1111-111111111111', 2, 55.00, 120.00),
  ('11111111-1111-1111-1111-111111111111', 3, 56.50, 100.00),
  ('11111111-1111-1111-1111-111111111111', 4, 54.00, 150.00),
  ('11111111-1111-1111-1111-111111111111', 5, 55.00, 120.00),
  ('11111111-1111-1111-1111-111111111111', 6, 57.00,  80.00),
  ('11111111-1111-1111-1111-111111111111', 7, 55.00, 120.00),
  -- Robusta Supply
  ('22222222-2222-2222-2222-222222222222', 1, 42.00, 200.00),
  ('22222222-2222-2222-2222-222222222222', 2, 42.00, 200.00),
  ('22222222-2222-2222-2222-222222222222', 3, 41.50, 200.00),
  ('22222222-2222-2222-2222-222222222222', 4, 43.00, 180.00),
  ('22222222-2222-2222-2222-222222222222', 5, 42.50, 200.00),
  ('22222222-2222-2222-2222-222222222222', 6, 42.00, 200.00),
  ('22222222-2222-2222-2222-222222222222', 7, 41.00, 220.00)
ON CONFLICT (distributor_id, day) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Discount tiers (each (distributor, day) has 2 tiers)
-- ---------------------------------------------------------------------------
INSERT INTO distributor_discount_tiers (distributor_id, day, level, quantity_kg, unit_price) VALUES
  -- Arabica Traders: 5% off >=20kg, 10% off >=50kg
  ('11111111-1111-1111-1111-111111111111', 1, 1, 20.00, 52.25), ('11111111-1111-1111-1111-111111111111', 1, 2, 50.00, 49.50),
  ('11111111-1111-1111-1111-111111111111', 2, 1, 20.00, 52.25), ('11111111-1111-1111-1111-111111111111', 2, 2, 50.00, 49.50),
  ('11111111-1111-1111-1111-111111111111', 3, 1, 20.00, 53.67), ('11111111-1111-1111-1111-111111111111', 3, 2, 50.00, 50.85),
  ('11111111-1111-1111-1111-111111111111', 4, 1, 20.00, 51.30), ('11111111-1111-1111-1111-111111111111', 4, 2, 50.00, 48.60),
  ('11111111-1111-1111-1111-111111111111', 5, 1, 20.00, 52.25), ('11111111-1111-1111-1111-111111111111', 5, 2, 50.00, 49.50),
  ('11111111-1111-1111-1111-111111111111', 6, 1, 20.00, 54.15), ('11111111-1111-1111-1111-111111111111', 6, 2, 50.00, 51.30),
  ('11111111-1111-1111-1111-111111111111', 7, 1, 20.00, 52.25), ('11111111-1111-1111-1111-111111111111', 7, 2, 50.00, 49.50),
  -- Robusta Supply: 4% off >=25kg, 8% off >=60kg
  ('22222222-2222-2222-2222-222222222222', 1, 1, 25.00, 40.32), ('22222222-2222-2222-2222-222222222222', 1, 2, 60.00, 38.64),
  ('22222222-2222-2222-2222-222222222222', 2, 1, 25.00, 40.32), ('22222222-2222-2222-2222-222222222222', 2, 2, 60.00, 38.64),
  ('22222222-2222-2222-2222-222222222222', 3, 1, 25.00, 39.84), ('22222222-2222-2222-2222-222222222222', 3, 2, 60.00, 38.18),
  ('22222222-2222-2222-2222-222222222222', 4, 1, 25.00, 41.28), ('22222222-2222-2222-2222-222222222222', 4, 2, 60.00, 39.56),
  ('22222222-2222-2222-2222-222222222222', 5, 1, 25.00, 40.80), ('22222222-2222-2222-2222-222222222222', 5, 2, 60.00, 39.10),
  ('22222222-2222-2222-2222-222222222222', 6, 1, 25.00, 40.32), ('22222222-2222-2222-2222-222222222222', 6, 2, 60.00, 38.64),
  ('22222222-2222-2222-2222-222222222222', 7, 1, 25.00, 39.36), ('22222222-2222-2222-2222-222222222222', 7, 2, 60.00, 37.72)
ON CONFLICT (distributor_id, day, level) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Delivery params (one row per distributor-building pair)
-- ---------------------------------------------------------------------------
INSERT INTO delivery_params (distributor_id, building_id, lead_time_days, fixed_cost_pln, correction_cost_per_kg, max_correction_kg) VALUES
  ('11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 1, 25.00, 2.00, 5.00),
  ('11111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 2, 40.00, 2.50, 5.00),
  ('22222222-2222-2222-2222-222222222222', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 2, 30.00, 1.80, 6.00),
  ('22222222-2222-2222-2222-222222222222', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 1, 20.00, 1.80, 6.00)
ON CONFLICT (distributor_id, building_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Building daily demand (days 1..7)
-- ---------------------------------------------------------------------------
INSERT INTO building_daily_demand (building_id, day, demand_kg) VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 1, 8.000),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 2, 9.000),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 3, 7.500),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 4, 10.000),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 5, 9.500),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 6, 4.000),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 7, 3.000),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 1, 5.000),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 2, 6.000),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 3, 5.500),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 4, 7.000),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 5, 6.500),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 6, 3.000),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 7, 2.500)
ON CONFLICT (building_id, day) DO NOTHING;

COMMIT;

-- ---------------------------------------------------------------------------
-- Reference IDs for quick API testing:
--
-- Distributors:
--   11111111-1111-1111-1111-111111111111  arabica_traders
--   22222222-2222-2222-2222-222222222222  robusta_supply
--
-- Buildings:
--   aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa  HQ Warsaw
--   bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb  Office Krk
--
-- Example POST /optimization body:
-- {
--   "name": "demo-week",
--   "planning_horizon_days": 7,
--   "decay_rate": 0.05,
--   "distributor_ids": [
--     "11111111-1111-1111-1111-111111111111",
--     "22222222-2222-2222-2222-222222222222"
--   ],
--   "building_ids": [
--     "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
--     "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
--   ]
-- }
-- ---------------------------------------------------------------------------