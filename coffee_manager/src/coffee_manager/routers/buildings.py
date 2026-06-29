from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from coffee_manager.auth import get_current_user
from coffee_manager.database import get_db
from coffee_manager.models import (
    Building,
    BuildingDailyDemand,
    OptimizationInventoryLevel,
    OptimizationOrderItem,
    OrderItem,
    User,
)
from coffee_manager.schemas import BuildingCreateRequest, BuildingResponse, DailyDemand

router = APIRouter(prefix="/buildings", tags=["Buildings"])


def _load_building(db: Session, building_id: UUID) -> Building:
    building = (
        db.query(Building)
        .options(selectinload(Building.daily_demand))
        .filter(Building.id == building_id)
        .first()
    )
    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    return building


def _to_response(b: Building) -> BuildingResponse:
    return BuildingResponse(
        id=b.id,
        name=b.name,
        location=b.location,
        max_capacity_kg=float(b.max_capacity_kg),
        initial_inventory_kg=float(b.initial_inventory_kg),
        current_inventory_kg=float(b.current_inventory_kg),
        daily_demand=[
            DailyDemand(day=d.day, demand_kg=float(d.demand_kg))
            for d in sorted(b.daily_demand, key=lambda x: x.day)
        ],
        created_at=b.created_at,
        updated_at=b.updated_at,
    )


def _replace_demand(
    db: Session, building: Building, daily_demand: list[DailyDemand]
) -> None:
    for d in building.daily_demand:
        db.delete(d)
    db.flush()
    for demand in daily_demand:
        db.add(
            BuildingDailyDemand(
                building_id=building.id, day=demand.day, demand_kg=demand.demand_kg
            )
        )


@router.get("", response_model=list[BuildingResponse])
def list_buildings(
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    buildings = db.query(Building).options(selectinload(Building.daily_demand)).all()
    return [_to_response(b) for b in buildings]


@router.post("", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
def create_building(
    body: BuildingCreateRequest,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    building = Building(
        name=body.name,
        location=body.location,
        max_capacity_kg=body.max_capacity_kg,
        initial_inventory_kg=body.initial_inventory_kg,
        current_inventory_kg=body.initial_inventory_kg,
    )
    db.add(building)
    db.flush()
    for demand in body.daily_demand:
        db.add(
            BuildingDailyDemand(
                building_id=building.id, day=demand.day, demand_kg=demand.demand_kg
            )
        )
    db.commit()
    return _to_response(_load_building(db, building.id))


@router.get("/{building_id}", response_model=BuildingResponse)
def get_building(
    building_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    return _to_response(_load_building(db, building_id))


@router.put("/{building_id}", response_model=BuildingResponse)
def update_building(
    building_id: UUID,
    body: BuildingCreateRequest,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    building = _load_building(db, building_id)
    building.name = body.name
    building.location = body.location
    building.max_capacity_kg = body.max_capacity_kg
    building.initial_inventory_kg = body.initial_inventory_kg
    _replace_demand(db, building, body.daily_demand)
    db.commit()
    return _to_response(_load_building(db, building_id))


@router.delete("/{building_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_building(
    building_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    building = db.get(Building, building_id)
    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    db.query(OrderItem).filter(OrderItem.building_id == building_id).delete(
        synchronize_session=False
    )
    db.query(OptimizationOrderItem).filter(
        OptimizationOrderItem.building_id == building_id
    ).delete(synchronize_session=False)
    db.query(OptimizationInventoryLevel).filter(
        OptimizationInventoryLevel.building_id == building_id
    ).delete(synchronize_session=False)
    db.delete(building)
    db.commit()
