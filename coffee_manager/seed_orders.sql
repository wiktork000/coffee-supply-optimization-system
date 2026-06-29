-- Seed dummy order history for the coordinator panel demo.
-- Apply once with:
--   docker compose exec -T db psql -U coffee_user -d coffee_db < coffee_manager/seed_orders.sql
--
-- Idempotent: re-running will not duplicate rows.

BEGIN;

INSERT INTO optimization_scenarios (id, name, planning_horizon_days, decay_rate) VALUES
  ('cc000000-0000-0000-0000-000000000001', 'Week 1 Planning', 7, 0.05),
  ('cc000000-0000-0000-0000-000000000002', 'Week 2 Planning', 7, 0.05),
  ('cc000000-0000-0000-0000-000000000003', 'Week 3 Planning', 7, 0.05)
ON CONFLICT (id) DO NOTHING;

INSERT INTO optimization_scenario_distributors (scenario_id, distributor_id) VALUES
  ('cc000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111'),
  ('cc000000-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222'),
  ('cc000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111'),
  ('cc000000-0000-0000-0000-000000000002', '22222222-2222-2222-2222-222222222222'),
  ('cc000000-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111'),
  ('cc000000-0000-0000-0000-000000000003', '22222222-2222-2222-2222-222222222222')
ON CONFLICT (scenario_id, distributor_id) DO NOTHING;

INSERT INTO optimization_scenario_buildings (scenario_id, building_id) VALUES
  ('cc000000-0000-0000-0000-000000000001', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
  ('cc000000-0000-0000-0000-000000000001', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'),
  ('cc000000-0000-0000-0000-000000000002', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
  ('cc000000-0000-0000-0000-000000000002', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'),
  ('cc000000-0000-0000-0000-000000000003', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
  ('cc000000-0000-0000-0000-000000000003', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')
ON CONFLICT (scenario_id, building_id) DO NOTHING;

INSERT INTO optimization_results (id, scenario_id, status, total_cost_pln, purchase_base, purchase_discount, fixed_delivery, total, solver_message) VALUES
  ('dd000000-0000-0000-0000-000000000001', 'cc000000-0000-0000-0000-000000000001', 'Optimal', 2340.00, 2800.00, 460.00, 200.00, 2540.00, 'Optimal solution found'),
  ('dd000000-0000-0000-0000-000000000002', 'cc000000-0000-0000-0000-000000000002', 'Optimal', 1820.50, 2100.00, 329.50, 150.00, 1920.50, 'Optimal solution found'),
  ('dd000000-0000-0000-0000-000000000003', 'cc000000-0000-0000-0000-000000000003', 'Optimal', 3150.75, 3700.00, 629.25, 280.00, 3350.75, 'Optimal solution found')
ON CONFLICT (id) DO NOTHING;

INSERT INTO orders (id, result_id, scenario_id, total_cost_pln, status) VALUES
  ('ee000000-0000-0000-0000-000000000001', 'dd000000-0000-0000-0000-000000000001', 'cc000000-0000-0000-0000-000000000001', 2340.00,  'confirmed'),
  ('ee000000-0000-0000-0000-000000000002', 'dd000000-0000-0000-0000-000000000002', 'cc000000-0000-0000-0000-000000000002', 1820.50,  'pending'),
  ('ee000000-0000-0000-0000-000000000003', 'dd000000-0000-0000-0000-000000000003', 'cc000000-0000-0000-0000-000000000003', 3150.75,  'cancelled')
ON CONFLICT (id) DO NOTHING;

INSERT INTO order_items (id, order_id, distributor_id, building_id, day, threshold_level, quantity_kg) VALUES
  -- Order 1 – confirmed, 3 deliveries
  ('ff000000-0000-0000-0000-000000000001', 'ee000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 2, 2,  50.000),
  ('ff000000-0000-0000-0000-000000000002', 'ee000000-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 1, 1,  60.000),
  ('ff000000-0000-0000-0000-000000000003', 'ee000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 3, 0,  30.000),
  -- Order 2 – pending, 2 deliveries
  ('ff000000-0000-0000-0000-000000000004', 'ee000000-0000-0000-0000-000000000002', '22222222-2222-2222-2222-222222222222', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 4, 0,  25.000),
  ('ff000000-0000-0000-0000-000000000005', 'ee000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 5, 2,  80.000),
  -- Order 3 – cancelled, 4 deliveries
  ('ff000000-0000-0000-0000-000000000006', 'ee000000-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 1, 0,  20.000),
  ('ff000000-0000-0000-0000-000000000007', 'ee000000-0000-0000-0000-000000000003', '22222222-2222-2222-2222-222222222222', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 2, 0,  15.000),
  ('ff000000-0000-0000-0000-000000000008', 'ee000000-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 4, 1,  35.000),
  ('ff000000-0000-0000-0000-000000000009', 'ee000000-0000-0000-0000-000000000003', '22222222-2222-2222-2222-222222222222', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 6, 0,  10.000)
ON CONFLICT (id) DO NOTHING;

COMMIT;
