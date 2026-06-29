"""Pydantic schema validation tests."""

import pytest
from pydantic import ValidationError

from coffee_manager.schemas import (
    BuildingCreateRequest,
    DailyDemand,
    DailyPrice,
    DiscountTier,
    OrderStatusUpdate,
    ScenarioCreateRequest,
)


def test_discount_tier_rejects_negative():
    with pytest.raises(ValidationError):
        DiscountTier(level=1, quantity_kg=-1, unit_price=10)
    with pytest.raises(ValidationError):
        DiscountTier(level=0, quantity_kg=1, unit_price=10)


def test_daily_price_defaults_tiers_empty():
    p = DailyPrice(day=1, base_price=10, availability_kg=100)
    assert p.discount_tiers == []


def test_building_create_request_day_must_be_positive():
    with pytest.raises(ValidationError):
        BuildingCreateRequest(
            name="HQ",
            max_capacity_kg=100,
            daily_demand=[DailyDemand(day=0, demand_kg=5)],
        )


def test_order_status_update_pattern():
    OrderStatusUpdate(status="confirmed")
    OrderStatusUpdate(status="pending")
    OrderStatusUpdate(status="cancelled")
    with pytest.raises(ValidationError):
        OrderStatusUpdate(status="shipped")


def test_scenario_horizon_bounds():
    ScenarioCreateRequest(name="x", distributor_ids=[], building_ids=[])
    with pytest.raises(ValidationError):
        ScenarioCreateRequest(
            name="x", planning_horizon_days=0, distributor_ids=[], building_ids=[]
        )
    with pytest.raises(ValidationError):
        ScenarioCreateRequest(
            name="x", planning_horizon_days=31, distributor_ids=[], building_ids=[]
        )


def test_scenario_decay_rate_bounds():
    with pytest.raises(ValidationError):
        ScenarioCreateRequest(
            name="x", decay_rate=1.5, distributor_ids=[], building_ids=[]
        )
    with pytest.raises(ValidationError):
        ScenarioCreateRequest(
            name="x", decay_rate=-0.1, distributor_ids=[], building_ids=[]
        )
