from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from coffee_manager.auth import get_current_user
from coffee_manager.database import get_db
from coffee_manager.models import Building, User
from coffee_manager.schemas import InventoryStatus

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=list[InventoryStatus])
def get_inventory(
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    buildings = db.query(Building).all()
    return [
        InventoryStatus(
            building_id=b.id,
            building_name=b.name,
            current_inventory_kg=float(b.current_inventory_kg),
            max_capacity_kg=float(b.max_capacity_kg),
            fill_percent=(
                round(float(b.current_inventory_kg) / float(b.max_capacity_kg) * 100, 2)
                if float(b.max_capacity_kg) > 0
                else 0.0
            ),
        )
        for b in buildings
    ]


@router.put("/{building_id}")
def update_inventory(
    building_id: UUID,
    current_kg: float,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    building = db.get(Building, building_id)
    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    if current_kg > float(building.max_capacity_kg):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Inventory exceeds max capacity",
        )
    building.current_inventory_kg = current_kg
    db.commit()
    return {"building_id": str(building_id), "current_inventory_kg": current_kg}
