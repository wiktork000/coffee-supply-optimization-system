import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from coffee_manager.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(30), nullable=False, default="coordinator")


class Distributor(Base):
    __tablename__ = "distributors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False, unique=True)
    contact_email = Column(String(100), nullable=False, unique=True)
    contact_phone = Column(String(20), nullable=False, unique=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    daily_prices = relationship(
        "DistributorDailyPrice",
        back_populates="distributor",
        cascade="all, delete-orphan",
    )
    delivery_params = relationship(
        "DeliveryParam", back_populates="distributor", cascade="all, delete-orphan"
    )
    api_keys = relationship(
        "ApiKey", back_populates="distributor", cascade="all, delete-orphan"
    )


class DistributorDailyPrice(Base):
    __tablename__ = "distributor_daily_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    distributor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="CASCADE"),
        nullable=False,
    )
    day = Column(Integer, nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    availability_kg = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (UniqueConstraint("distributor_id", "day"),)

    distributor = relationship("Distributor", back_populates="daily_prices")
    discount_tiers = relationship(
        "DistributorDiscountTier",
        primaryjoin="and_(DistributorDailyPrice.distributor_id == foreign(DistributorDiscountTier.distributor_id), "
        "DistributorDailyPrice.day == foreign(DistributorDiscountTier.day))",
        cascade="all, delete-orphan",
        overlaps="daily_price",
    )


class DistributorDiscountTier(Base):
    __tablename__ = "distributor_discount_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    distributor_id = Column(UUID(as_uuid=True), nullable=False)
    day = Column(Integer, nullable=False)
    level = Column(Integer, nullable=False)
    quantity_kg = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("distributor_id", "day", "level"),
        ForeignKeyConstraint(
            ["distributor_id", "day"],
            ["distributor_daily_prices.distributor_id", "distributor_daily_prices.day"],
            ondelete="CASCADE",
        ),
    )


class Building(Base):
    __tablename__ = "buildings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    location = Column(Text)
    max_capacity_kg = Column(Numeric(10, 2), nullable=False)
    initial_inventory_kg = Column(Numeric(10, 2), nullable=False, default=0)
    current_inventory_kg = Column(Numeric, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    daily_demand = relationship(
        "BuildingDailyDemand", back_populates="building", cascade="all, delete-orphan"
    )
    delivery_params = relationship(
        "DeliveryParam", back_populates="building", cascade="all, delete-orphan"
    )


class DeliveryParam(Base):
    __tablename__ = "delivery_params"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    distributor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="CASCADE"),
        nullable=False,
    )
    building_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
    )
    lead_time_days = Column(Integer, nullable=False, default=1)
    fixed_cost_pln = Column(Numeric(10, 2), nullable=False, default=0.0)
    correction_cost_per_kg = Column(Numeric(10, 2), nullable=False, default=0.0)
    max_correction_kg = Column(Numeric(10, 2), nullable=False, default=0.0)

    __table_args__ = (UniqueConstraint("distributor_id", "building_id"),)

    distributor = relationship("Distributor", back_populates="delivery_params")
    building = relationship("Building", back_populates="delivery_params")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    distributor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="CASCADE"),
        nullable=False,
    )
    key_prefix = Column(String(20), nullable=False)
    key_hash = Column(Text, nullable=False, unique=True)
    label = Column(String(255), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    distributor = relationship("Distributor", back_populates="api_keys")


class BuildingDailyDemand(Base):
    __tablename__ = "building_daily_demand"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
    )
    day = Column(Integer, nullable=False)
    demand_kg = Column(Numeric(12, 3), nullable=False)

    __table_args__ = (UniqueConstraint("building_id", "day"),)

    building = relationship("Building", back_populates="daily_demand")


class OptimizationScenario(Base):
    __tablename__ = "optimization_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    planning_horizon_days = Column(Integer, nullable=False, default=7)
    decay_rate = Column(Numeric(5, 4), nullable=False, default=0.05)
    historical_orders = Column(JSONB)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    distributors = relationship(
        "Distributor",
        secondary="optimization_scenario_distributors",
        backref="scenarios",
    )
    buildings = relationship(
        "Building",
        secondary="optimization_scenario_buildings",
        backref="scenarios",
    )
    results = relationship("OptimizationResult", back_populates="scenario")


class OptimizationScenarioDistributor(Base):
    __tablename__ = "optimization_scenario_distributors"

    scenario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("optimization_scenarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    distributor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="CASCADE"),
        primary_key=True,
    )


class OptimizationScenarioBuilding(Base):
    __tablename__ = "optimization_scenario_buildings"

    scenario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("optimization_scenarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    building_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        primary_key=True,
    )


class OptimizationResult(Base):
    __tablename__ = "optimization_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("optimization_scenarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String(30), nullable=False)
    total_cost_pln = Column(Numeric(14, 2))
    purchase_base = Column(Numeric(14, 2))
    purchase_discount = Column(Numeric(14, 2))
    fixed_delivery = Column(Numeric(14, 2))
    total = Column(Numeric(14, 2))
    solver_message = Column(Text)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    scenario = relationship("OptimizationScenario", back_populates="results")
    order_items = relationship(
        "OptimizationOrderItem", back_populates="result", cascade="all, delete-orphan"
    )
    inventory_levels = relationship(
        "OptimizationInventoryLevel",
        back_populates="result",
        cascade="all, delete-orphan",
    )
    corrections = relationship(
        "OptimizationCorrection",
        back_populates="result",
        cascade="all, delete-orphan",
    )


class OptimizationOrderItem(Base):
    __tablename__ = "optimization_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("optimization_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    distributor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    building_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    day = Column(Integer, nullable=False)
    threshold_level = Column(Integer, nullable=False, default=0)
    quantity_kg = Column(Numeric(12, 3), nullable=False)

    result = relationship("OptimizationResult", back_populates="order_items")


class OptimizationInventoryLevel(Base):
    __tablename__ = "optimization_inventory_levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("optimization_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    building_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    day = Column(Integer, nullable=False)
    level_kg = Column(Numeric(12, 3), nullable=False)

    __table_args__ = (UniqueConstraint("result_id", "building_id", "day"),)

    result = relationship("OptimizationResult", back_populates="inventory_levels")


class OptimizationCorrection(Base):
    __tablename__ = "optimization_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("optimization_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    distributor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    building_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    day = Column(Integer, nullable=False)
    threshold_level = Column(Integer, nullable=False, default=0)
    type = Column(String(20), nullable=False)  # 'increase' or 'decrease'
    quantity_kg = Column(Numeric(12, 3), nullable=False)

    result = relationship("OptimizationResult", back_populates="corrections")


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("optimization_results.id", ondelete="RESTRICT"),
        nullable=False,
    )
    scenario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("optimization_scenarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    total_cost_pln = Column(Numeric(14, 2))
    confirmed_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    status = Column(String(30), nullable=False, default="confirmed")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    distributor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("distributors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    building_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    day = Column(Integer, nullable=False)
    threshold_level = Column(Integer, nullable=False, default=0)
    quantity_kg = Column(Numeric(12, 3), nullable=False)

    order = relationship("Order", back_populates="items")
