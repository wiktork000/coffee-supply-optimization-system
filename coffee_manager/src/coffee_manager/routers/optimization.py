from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from coffee_manager.auth import get_current_user
from coffee_manager.config import settings
from coffee_manager.database import get_db
from coffee_manager.models import (
    Building,
    Distributor,
    DistributorDailyPrice,
    OptimizationCorrection,
    OptimizationInventoryLevel,
    OptimizationOrderItem,
    OptimizationResult,
    OptimizationScenario,
    OptimizationScenarioBuilding,
    OptimizationScenarioDistributor,
    User,
)
from coffee_manager.schemas import (
    CorrectionItem,
    CorrectionRequest,
    CorrectionResponse,
    CostBreakdown,
    InventoryLevel,
    OptimizationResponse,
    ScenarioCreateRequest,
)
from coffee_manager.schemas import OrderItem as OrderItemSchema

router = APIRouter(prefix="/optimization", tags=["Optimization"])


def _distributors_payload(
    distributors, building_ids: list[str], horizon_days: int
) -> list[dict]:
    return [
        {
            "id": str(d.id),
            "daily_prices": [
                {
                    "day": p.day,
                    "base_price": float(p.base_price),
                    "availability_kg": float(p.availability_kg),
                    "discount_tiers": [
                        {
                            "level": t.level,
                            "quantity_kg": float(t.quantity_kg),
                            "unit_price": float(t.unit_price),
                        }
                        for t in p.discount_tiers
                    ],
                }
                for p in d.daily_prices
                if p.day <= horizon_days
            ],
            "delivery_params": [
                {
                    "building_id": str(p.building_id),
                    "lead_time_days": p.lead_time_days,
                    "fixed_cost_pln": float(p.fixed_cost_pln),
                }
                for p in d.delivery_params
                if str(p.building_id) in building_ids
            ],
        }
        for d in distributors
    ]


def _buildings_payload(buildings, horizon_days: int) -> list[dict]:
    return [
        {
            "id": str(b.id),
            "max_capacity_kg": float(b.max_capacity_kg),
            "initial_inventory_kg": float(b.current_inventory_kg),
            "daily_demand": [
                {"day": dd.day, "demand_kg": float(dd.demand_kg)}
                for dd in b.daily_demand
                if dd.day <= horizon_days
            ],
        }
        for b in buildings
    ]


def _parse_historical_arrivals(historical_orders: dict | None) -> list[dict]:
    if not historical_orders:
        return []
    arrivals = []
    for k, v in historical_orders.items():
        parts = k.split(":")
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"historical_orders key must be 'distributor_id:building_id', got {k!r}",
            )
        arrivals.append(
            {
                "distributor_id": parts[0],
                "building_id": parts[1],
                "day": 1,
                "quantity_kg": v,
            }
        )
    return arrivals


def _to_response(result: OptimizationResult) -> OptimizationResponse:
    cost_breakdown = None
    if result.purchase_base is not None:
        cost_breakdown = CostBreakdown(
            purchase_base=float(result.purchase_base),
            purchase_discount=float(result.purchase_discount or 0),
            fixed_delivery=float(result.fixed_delivery or 0),
            total=float(result.total or 0),
        )
    return OptimizationResponse(
        scenario_id=result.scenario_id,
        result_id=result.id,
        status=result.status,
        total_cost_pln=(
            float(result.total_cost_pln) if result.total_cost_pln is not None else None
        ),
        solver_message=result.solver_message,
        orders=[
            OrderItemSchema(
                distributor_id=i.distributor_id,
                building_id=i.building_id,
                day=i.day,
                threshold_level=i.threshold_level,
                quantity_kg=float(i.quantity_kg),
            )
            for i in result.order_items
        ],
        inventory_levels=[
            InventoryLevel(
                building_id=i.building_id,
                day=i.day,
                level_kg=float(i.level_kg),
            )
            for i in result.inventory_levels
        ],
        cost_breakdown=cost_breakdown,
    )


def _load_result(db: Session, result_id: UUID) -> OptimizationResult:
    result = (
        db.query(OptimizationResult)
        .options(
            selectinload(OptimizationResult.order_items),
            selectinload(OptimizationResult.inventory_levels),
            selectinload(OptimizationResult.corrections),
        )
        .filter(OptimizationResult.id == result_id)
        .first()
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Optimization result not found",
        )
    return result


def _to_correction_response(result: OptimizationResult) -> CorrectionResponse:
    return CorrectionResponse(
        scenario_id=result.scenario_id,
        result_id=result.id,
        status=result.status,
        total_cost_pln=(
            float(result.total_cost_pln) if result.total_cost_pln is not None else None
        ),
        solver_message=result.solver_message,
        orders=[
            OrderItemSchema(
                distributor_id=i.distributor_id,
                building_id=i.building_id,
                day=i.day,
                threshold_level=i.threshold_level,
                quantity_kg=float(i.quantity_kg),
            )
            for i in result.order_items
        ],
        corrections=[
            CorrectionItem(
                distributor_id=c.distributor_id,
                building_id=c.building_id,
                day=c.day,
                threshold_level=c.threshold_level,
                type=c.type,
                quantity_kg=float(c.quantity_kg),
            )
            for c in result.corrections
        ],
        inventory_levels=[
            InventoryLevel(
                building_id=i.building_id,
                day=i.day,
                level_kg=float(i.level_kg),
            )
            for i in result.inventory_levels
        ],
    )


@router.get("", response_model=list[OptimizationResponse])
def list_optimizations(
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    results = (
        db.query(OptimizationResult)
        .options(
            selectinload(OptimizationResult.order_items),
            selectinload(OptimizationResult.inventory_levels),
        )
        .all()
    )
    return [_to_response(r) for r in results]


@router.post("", response_model=OptimizationResponse)
def run_optimization(
    body: ScenarioCreateRequest,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    distributors = (
        db.query(Distributor)
        .options(
            selectinload(Distributor.daily_prices).selectinload(
                DistributorDailyPrice.discount_tiers
            ),
            selectinload(Distributor.delivery_params),
        )
        .filter(Distributor.id.in_(body.distributor_ids))
        .all()
    )
    if len(distributors) != len(body.distributor_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more distributors not found",
        )

    buildings = (
        db.query(Building)
        .options(selectinload(Building.daily_demand))
        .filter(Building.id.in_(body.building_ids))
        .all()
    )
    if len(buildings) != len(body.building_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more buildings not found",
        )

    planning_days = list(range(1, body.planning_horizon_days + 1))

    optimizer_payload = {
        "planning_days": planning_days,
        "decay_rate": body.decay_rate,
        "historical_arrivals": _parse_historical_arrivals(body.historical_orders),
        "distributors": _distributors_payload(
            distributors, body.building_ids, body.planning_horizon_days
        ),
        "buildings": _buildings_payload(buildings, body.planning_horizon_days),
    }

    try:
        response = httpx.post(
            f"{settings.OPTIMIZER_URL}/optimize", json=optimizer_payload, timeout=60.0
        )
        response.raise_for_status()
        opt_result = response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Optimizer error: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Optimizer unreachable: {e}",
        )

    scenario = OptimizationScenario(
        name=body.name,
        planning_horizon_days=body.planning_horizon_days,
        decay_rate=body.decay_rate,
        historical_orders=body.historical_orders,
    )
    db.add(scenario)
    db.flush()

    for d in distributors:
        db.add(
            OptimizationScenarioDistributor(
                scenario_id=scenario.id, distributor_id=d.id
            )
        )
    for b in buildings:
        db.add(OptimizationScenarioBuilding(scenario_id=scenario.id, building_id=b.id))

    cb = opt_result.get("cost_breakdown")
    result = OptimizationResult(
        scenario_id=scenario.id,
        status=opt_result["status"],
        total_cost_pln=opt_result.get("total_cost_pln"),
        purchase_base=cb["purchase_base"] if cb else None,
        purchase_discount=cb["purchase_discount"] if cb else None,
        fixed_delivery=cb["fixed_delivery"] if cb else None,
        total=cb["total"] if cb else None,
        solver_message=opt_result.get("solver_message"),
    )
    db.add(result)
    db.flush()

    for item in opt_result.get("orders", []):
        db.add(
            OptimizationOrderItem(
                result_id=result.id,
                distributor_id=item["distributor_id"],
                building_id=item["building_id"],
                day=item["day"],
                threshold_level=item.get("threshold_level", 0),
                quantity_kg=item["quantity_kg"],
            )
        )
    for level in opt_result.get("inventory_levels", []):
        db.add(
            OptimizationInventoryLevel(
                result_id=result.id,
                building_id=level["building_id"],
                day=level["day"],
                level_kg=level["level_kg"],
            )
        )

    db.commit()
    return _to_response(_load_result(db, result.id))


@router.post("/correction", response_model=CorrectionResponse)
def run_correction(
    body: CorrectionRequest,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    prev_result = _load_result(db, body.previous_result_id)
    scenario = (
        db.query(OptimizationScenario)
        .options(
            selectinload(OptimizationScenario.distributors),
            selectinload(OptimizationScenario.buildings),
        )
        .filter(OptimizationScenario.id == prev_result.scenario_id)
        .first()
    )
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found"
        )

    distributor_ids = [d.id for d in scenario.distributors]
    building_ids = [b.id for b in scenario.buildings]

    distributors = (
        db.query(Distributor)
        .options(
            selectinload(Distributor.daily_prices).selectinload(
                DistributorDailyPrice.discount_tiers
            ),
            selectinload(Distributor.delivery_params),
        )
        .filter(Distributor.id.in_(distributor_ids))
        .all()
    )
    buildings = (
        db.query(Building)
        .options(selectinload(Building.daily_demand))
        .filter(Building.id.in_(building_ids))
        .all()
    )

    planning_days = list(range(1, scenario.planning_horizon_days + 1))

    # Base historical arrivals from scenario
    historical_arrivals = _parse_historical_arrivals(scenario.historical_orders)

    # Override/merge with historical arrivals from request body if any
    if body.historical_orders:
        req_arrivals = _parse_historical_arrivals(body.historical_orders)
        # Create a map for merging: key is distributor_id:building_id
        arrivals_map = {
            f"{a['distributor_id']}:{a['building_id']}": a for a in historical_arrivals
        }
        for ra in req_arrivals:
            arrivals_map[f"{ra['distributor_id']}:{ra['building_id']}"] = ra
        historical_arrivals = list(arrivals_map.values())

    optimizer_payload = {
        "planning_days": planning_days,
        "decay_rate": float(scenario.decay_rate),
        "historical_arrivals": historical_arrivals,
        "distributors": _distributors_payload(
            distributors, building_ids, scenario.planning_horizon_days
        ),
        "buildings": _buildings_payload(buildings, scenario.planning_horizon_days),
    }

    optimizer_payload["previous_orders"] = [
        {
            "distributor_id": str(item.distributor_id),
            "building_id": str(item.building_id),
            "day": item.day,
            "threshold_level": item.threshold_level,
            "quantity_kg": round(float(item.quantity_kg), 3),
        }
        for item in prev_result.order_items
    ]

    correction_costs = []
    correction_limits = []
    for d in distributors:
        for p in d.delivery_params:
            if p.building_id not in building_ids:
                continue
            for day in planning_days:
                correction_costs.append(
                    {
                        "distributor_id": str(d.id),
                        "building_id": str(p.building_id),
                        "day": day,
                        "cost_per_kg": float(p.correction_cost_per_kg),
                    }
                )
                correction_limits.append(
                    {
                        "distributor_id": str(d.id),
                        "building_id": str(p.building_id),
                        "day": day,
                        "max_correction_kg": float(p.max_correction_kg),
                    }
                )
    optimizer_payload["correction_costs"] = correction_costs
    optimizer_payload["correction_limits"] = correction_limits

    try:
        response = httpx.post(
            f"{settings.OPTIMIZER_URL}/optimize/correction",
            json=optimizer_payload,
            timeout=60.0,
        )
        response.raise_for_status()
        opt_result = response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Optimizer error: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Optimizer unreachable: {e}",
        )

    new_result = OptimizationResult(
        scenario_id=scenario.id,
        status=opt_result["status"],
        total_cost_pln=opt_result.get("total_cost_pln"),
        solver_message=opt_result.get("solver_message"),
    )
    cb = opt_result.get("cost_breakdown")
    if cb:
        new_result.purchase_base = cb.get("purchase_base")
        new_result.purchase_discount = cb.get("purchase_discount")
        new_result.fixed_delivery = cb.get("fixed_delivery")
        new_result.total = cb.get("total")

    db.add(new_result)
    db.flush()

    new_orders = {}
    for item in opt_result.get("final_orders", []):
        oi = OptimizationOrderItem(
            result_id=new_result.id,
            distributor_id=item["distributor_id"],
            building_id=item["building_id"],
            day=item["day"],
            threshold_level=item.get("threshold_level", 0),
            quantity_kg=item["quantity_kg"],
        )
        db.add(oi)
        key = (
            item["distributor_id"],
            item["building_id"],
            item["day"],
            item.get("threshold_level", 0),
        )
        new_orders[key] = item["quantity_kg"]

    for level in opt_result.get("inventory_levels", []):
        db.add(
            OptimizationInventoryLevel(
                result_id=new_result.id,
                building_id=level["building_id"],
                day=level["day"],
                level_kg=level["level_kg"],
            )
        )

    old_orders = {}
    for item in prev_result.order_items:
        key = (
            str(item.distributor_id),
            str(item.building_id),
            item.day,
            item.threshold_level,
        )
        old_orders[key] = float(item.quantity_kg)

    all_keys = set(old_orders.keys()) | set(new_orders.keys())
    for key in all_keys:
        old_q = old_orders.get(key, 0.0)
        new_q = new_orders.get(key, 0.0)
        if abs(new_q - old_q) > 1e-3:
            diff = new_q - old_q
            corr = OptimizationCorrection(
                result_id=new_result.id,
                distributor_id=key[0],
                building_id=key[1],
                day=key[2],
                threshold_level=key[3],
                type="increase" if diff > 0 else "decrease",
                quantity_kg=abs(diff),
            )
            db.add(corr)

    db.commit()
    return _to_correction_response(_load_result(db, new_result.id))


@router.get("/{result_id}", response_model=OptimizationResponse)
def get_optimization_result(
    result_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    return _to_response(_load_result(db, result_id))
