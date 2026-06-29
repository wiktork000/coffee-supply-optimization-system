from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: UUID
    role: str


class DiscountTier(BaseModel):
    level: int = Field(ge=1)
    quantity_kg: float = Field(ge=0)
    unit_price: float = Field(ge=0)


class DailyPrice(BaseModel):
    day: int = Field(ge=1)
    base_price: float = Field(ge=0)
    availability_kg: float = Field(ge=0)
    discount_tiers: list[DiscountTier] = []


class DeliveryParams(BaseModel):
    building_id: str
    lead_time_days: int = Field(ge=0)
    fixed_cost_pln: float = Field(ge=0)
    correction_cost_per_kg: float = Field(ge=0, default=0.0)
    max_correction_kg: float = Field(ge=0, default=1000000.0)


class DistributorCreateRequest(BaseModel):
    username: str
    contact_email: str
    contact_phone: str
    daily_prices: list[DailyPrice]
    delivery_params: list[DeliveryParams]


class DistributorUpdateRequest(BaseModel):
    username: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    daily_prices: list[DailyPrice] | None = None
    delivery_params: list[DeliveryParams] | None = None


class DistributorResponse(BaseModel):
    id: UUID
    username: str
    contact_email: str
    contact_phone: str
    active: bool
    daily_prices: list[DailyPrice]
    delivery_params: list[DeliveryParams]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DailyDemand(BaseModel):
    day: int = Field(ge=1)
    demand_kg: float = Field(ge=0)


class OrderItem(BaseModel):
    distributor_id: UUID
    building_id: UUID
    day: int = Field(ge=1)
    threshold_level: int = Field(ge=0)
    quantity_kg: float = Field(ge=0)

    model_config = {"from_attributes": True}


class InventoryLevel(BaseModel):
    building_id: UUID
    day: int
    level_kg: float

    model_config = {"from_attributes": True}


class CorrectionRequest(BaseModel):
    name: str
    previous_result_id: UUID
    historical_orders: dict[str, Any] | None = None


class CorrectionItem(BaseModel):
    distributor_id: UUID
    building_id: UUID
    day: int = Field(ge=1)
    threshold_level: int = Field(ge=0)
    type: str  # 'increase' or 'decrease'
    quantity_kg: float = Field(ge=0)

    model_config = {"from_attributes": True}


class BuildingCreateRequest(BaseModel):
    name: str
    location: str | None = None
    max_capacity_kg: float = Field(ge=0)
    initial_inventory_kg: float = Field(ge=0, default=0.0)
    daily_demand: list[DailyDemand]


class BuildingResponse(BaseModel):
    id: UUID
    name: str
    location: str | None
    max_capacity_kg: float
    initial_inventory_kg: float
    current_inventory_kg: float
    daily_demand: list[DailyDemand]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreateRequest(BaseModel):
    label: str


class ApiKeyResponse(BaseModel):
    id: UUID
    key: str | None = None
    label: str
    distributor_id: UUID
    active: bool
    revoked_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScenarioCreateRequest(BaseModel):
    name: str
    planning_horizon_days: int = Field(ge=1, le=30, default=7)
    distributor_ids: list[str]
    building_ids: list[str]
    decay_rate: float = Field(ge=0, le=1, default=0.05)
    historical_orders: dict[str, Any] | None = None


class CostBreakdown(BaseModel):
    purchase_base: float
    purchase_discount: float
    fixed_delivery: float
    total: float


class OptimizationResponse(BaseModel):
    scenario_id: UUID
    result_id: UUID
    status: str
    total_cost_pln: float | None
    solver_message: str | None
    orders: list[OrderItem]
    inventory_levels: list[InventoryLevel]
    cost_breakdown: CostBreakdown | None

    model_config = {"from_attributes": True}


class CorrectionResponse(BaseModel):
    scenario_id: UUID
    result_id: UUID
    status: str
    total_cost_pln: float | None
    solver_message: str | None
    orders: list[OrderItem]
    corrections: list[CorrectionItem]
    inventory_levels: list[InventoryLevel]

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(confirmed|pending|cancelled)$")


class OrderRecord(BaseModel):
    id: UUID
    result_id: UUID
    scenario_id: UUID
    orders: list[OrderItem]
    total_cost_pln: float | None
    confirmed_by: UUID | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InventoryStatus(BaseModel):
    building_id: UUID
    building_name: str
    current_inventory_kg: float
    max_capacity_kg: float
    fill_percent: float

    model_config = {"from_attributes": True}
