from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from coffee_optimizer.main import app
from coffee_optimizer.models import (
    BuildingData,
    DailyDemandData,
    DailyPriceData,
    DeliveryParamData,
    DiscountTierData,
    DistributorData,
    OptimizationRequest,
    OptimizationResult,
)
from coffee_optimizer.optimizer import _build_ampl_data

_DAYS = [1, 2, 3]

SAMPLE_REQUEST = OptimizationRequest(
    planning_days=_DAYS,
    distributors=[
        DistributorData(
            id="D1",
            daily_prices=[
                DailyPriceData(
                    day=d,
                    base_price=12.0,
                    availability_kg=100.0,
                    discount_tiers=[
                        DiscountTierData(level=1, quantity_kg=30.0, unit_price=10.0),
                        DiscountTierData(level=2, quantity_kg=60.0, unit_price=8.0),
                    ],
                )
                for d in _DAYS
            ],
            delivery_params=[
                DeliveryParamData(
                    building_id="B1", lead_time_days=1, fixed_cost_pln=50.0
                ),
            ],
        )
    ],
    buildings=[
        BuildingData(
            id="B1",
            max_capacity_kg=150.0,
            initial_inventory_kg=20.0,
            daily_demand=[DailyDemandData(day=d, demand_kg=15.0) for d in _DAYS],
        )
    ],
    decay_rate=0.05,
)


class TestBuildAmplData:
    def test_sets(self):
        data = _build_ampl_data(SAMPLE_REQUEST)
        assert data["T"] == [1, 2, 3]
        assert data["D"] == ["D1"]
        assert data["B"] == ["B1"]
        assert data["L"] == [1, 2]

    def test_scalar_params(self):
        data = _build_ampl_data(SAMPLE_REQUEST)
        assert data["alpha"] == 0.05

    def test_building_params(self):
        data = _build_ampl_data(SAMPLE_REQUEST)
        assert data["V_max"]["B1"] == 150.0
        assert data["I0"]["B1"] == 20.0

    def test_discount_thresholds(self):
        data = _build_ampl_data(SAMPLE_REQUEST)
        assert data["Q"][("D1", 1)] == 30.0
        assert data["Q"][("D1", 2)] == 60.0

    def test_prices(self):
        data = _build_ampl_data(SAMPLE_REQUEST)
        assert data["P0"][("D1", 1)] == 12.0
        assert data["P"][("D1", 1, 1)] == 10.0
        assert data["P"][("D1", 1, 2)] == 8.0

    def test_demand(self):
        data = _build_ampl_data(SAMPLE_REQUEST)
        assert data["Demand"][("B1", 1)] == 15.0

    def test_delivery_params(self):
        data = _build_ampl_data(SAMPLE_REQUEST)
        assert data["C_fix"][("D1", "B1")] == 50.0
        assert data["LT"][("D1", "B1")] == 1

    def test_missing_tier_falls_back_to_base_price(self):
        req = OptimizationRequest(
            planning_days=[1],
            distributors=[
                DistributorData(
                    id="D1",
                    daily_prices=[
                        DailyPriceData(
                            day=1,
                            base_price=10.0,
                            availability_kg=100.0,
                            discount_tiers=[
                                DiscountTierData(
                                    level=1, quantity_kg=30.0, unit_price=9.0
                                ),
                                # level 2 intentionally missing
                            ],
                        )
                    ],
                    delivery_params=[
                        DeliveryParamData(
                            building_id="B1", lead_time_days=1, fixed_cost_pln=0.0
                        )
                    ],
                ),
                DistributorData(
                    id="D2",
                    daily_prices=[
                        DailyPriceData(
                            day=1,
                            base_price=11.0,
                            availability_kg=100.0,
                            discount_tiers=[
                                DiscountTierData(
                                    level=2, quantity_kg=60.0, unit_price=7.0
                                ),
                                # level 1 intentionally missing
                            ],
                        )
                    ],
                    delivery_params=[
                        DeliveryParamData(
                            building_id="B1", lead_time_days=1, fixed_cost_pln=0.0
                        )
                    ],
                ),
            ],
            buildings=[
                BuildingData(
                    id="B1",
                    max_capacity_kg=200.0,
                    daily_demand=[DailyDemandData(day=1, demand_kg=10.0)],
                )
            ],
        )
        data = _build_ampl_data(req)
        assert data["L"] == [1, 2]
        assert data["P"][("D1", 1, 2)] == 10.0  # fallback to D1's base price
        assert data["P"][("D2", 1, 1)] == 11.0  # fallback to D2's base price

    def test_no_tiers_raises(self):
        req = OptimizationRequest(
            planning_days=[1],
            distributors=[
                DistributorData(
                    id="D1",
                    daily_prices=[
                        DailyPriceData(day=1, base_price=10.0, availability_kg=100.0)
                    ],
                    delivery_params=[
                        DeliveryParamData(
                            building_id="B1", lead_time_days=1, fixed_cost_pln=0.0
                        )
                    ],
                )
            ],
            buildings=[
                BuildingData(
                    id="B1",
                    max_capacity_kg=100.0,
                    daily_demand=[DailyDemandData(day=1, demand_kg=10.0)],
                )
            ],
        )
        with pytest.raises(ValueError, match="discount tier"):
            _build_ampl_data(req)

    def test_historical_arrivals_mapped(self):
        from coffee_optimizer.models import HistoricalArrival

        req = SAMPLE_REQUEST.model_copy(
            update={
                "historical_arrivals": [
                    HistoricalArrival(
                        distributor_id="D1", building_id="B1", day=1, quantity_kg=25.0
                    )
                ]
            }
        )
        data = _build_ampl_data(req)
        assert data["H_arrival"][("D1", "B1", 1)] == 25.0


class TestOptimizeEndpoint:
    def test_health(self):
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["service"] == "coffee-optimizer"

    def test_optimize_returns_solver_result(self):
        mock_result = OptimizationResult(
            status="Optimal",
            total_cost_pln=1234.5,
            orders=[],
            inventory_levels=[],
        )
        with patch("coffee_optimizer.main.run_optimization", return_value=mock_result):
            client = TestClient(app)
            resp = client.post("/optimize", json=SAMPLE_REQUEST.model_dump())
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "Optimal"
        assert body["total_cost_pln"] == 1234.5

    def test_optimize_invalid_request_returns_422(self):
        client = TestClient(app)
        resp = client.post("/optimize", json={"planning_days": []})
        assert resp.status_code == 422
