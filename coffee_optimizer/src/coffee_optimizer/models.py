from __future__ import annotations

from pydantic import BaseModel, Field


class DiscountTierData(BaseModel):
    level: int = Field(ge=1)
    quantity_kg: float = Field(ge=0, description="Quantity threshold [kg]")
    unit_price: float = Field(ge=0, description="Unit price at this tier [PLN/kg]")


class DailyPriceData(BaseModel):
    day: int = Field(ge=1)
    base_price: float = Field(ge=0, description="Price below first tier [PLN/kg]")
    availability_kg: float = Field(ge=0, description="Max available quantity [kg]")
    discount_tiers: list[DiscountTierData] = []


class DeliveryParamData(BaseModel):
    building_id: str
    lead_time_days: int = Field(ge=0)
    fixed_cost_pln: float = Field(ge=0)


class DistributorData(BaseModel):
    id: str
    daily_prices: list[DailyPriceData]
    delivery_params: list[DeliveryParamData]


class DailyDemandData(BaseModel):
    day: int = Field(ge=1)
    demand_kg: float = Field(ge=0)


class BuildingData(BaseModel):
    id: str
    max_capacity_kg: float = Field(ge=0)
    initial_inventory_kg: float = Field(ge=0, default=0.0)
    daily_demand: list[DailyDemandData]


class HistoricalArrival(BaseModel):
    distributor_id: str
    building_id: str
    day: int = Field(ge=1)
    quantity_kg: float = Field(ge=0)


class OptimizationRequest(BaseModel):
    planning_days: list[int] = Field(..., min_items=1)
    distributors: list[DistributorData] = Field(..., min_items=1)
    buildings: list[BuildingData] = Field(..., min_items=1)
    decay_rate: float = Field(ge=0, le=1, default=0.05)
    historical_arrivals: list[HistoricalArrival] = Field(default_factory=list)


class OrderItem(BaseModel):
    distributor_id: str
    building_id: str
    day: int
    threshold_level: int = Field(
        ge=0, description="0 = below first tier, >=1 = discount tier"
    )
    quantity_kg: float


class InventoryLevel(BaseModel):
    building_id: str
    day: int
    level_kg: float


class CostBreakdown(BaseModel):
    purchase_base: float
    purchase_discount: float
    fixed_delivery: float
    total: float


class OptimizationResult(BaseModel):
    status: str
    total_cost_pln: float | None = None
    solver_message: str | None = None
    orders: list[OrderItem] = []
    inventory_levels: list[InventoryLevel] = []
    cost_breakdown: CostBreakdown | None = None


class PlannedOrderItem(BaseModel):
    distributor_id: str
    building_id: str
    day: int = Field(ge=1)
    threshold_level: int = Field(
        ge=0,
        description="0 = below first tier, >=1 = discount tier",
    )
    quantity_kg: float = Field(ge=0)


class CorrectionLimitData(BaseModel):
    distributor_id: str
    building_id: str
    day: int = Field(ge=1)
    max_correction_kg: float = Field(ge=0)


class CorrectionCostData(BaseModel):
    distributor_id: str
    building_id: str
    day: int = Field(ge=1)
    cost_per_kg: float = Field(ge=0)


class CorrectionOptimizationRequest(OptimizationRequest):
    previous_orders: list[PlannedOrderItem] = []
    correction_limits: list[CorrectionLimitData] = []
    correction_costs: list[CorrectionCostData] = []


class CorrectionItem(BaseModel):
    distributor_id: str
    building_id: str
    day: int
    threshold_level: int = Field(
        ge=0,
        description="0 = below first tier, >=1 = discount tier",
    )
    type: str
    quantity_kg: float


class CorrectionOptimizationResult(BaseModel):
    status: str
    total_cost_pln: float | None = None
    solver_message: str | None = None
    final_orders: list[OrderItem] = []
    corrections: list[CorrectionItem] = []
    inventory_levels: list[InventoryLevel] = []
    cost_breakdown: CostBreakdown | None = None
