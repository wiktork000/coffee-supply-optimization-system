from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from coffee_manager.auth import get_current_user, get_distributor_by_api_key
from coffee_manager.database import get_db
from coffee_manager.models import (
    ApiKey,
    Building,
    DeliveryParam,
    Distributor,
    DistributorDailyPrice,
    DistributorDiscountTier,
    OptimizationOrderItem,
    OrderItem,
    User,
)
from coffee_manager.schemas import (
    BuildingResponse,
    DailyDemand,
    DailyPrice,
    DeliveryParams,
    DiscountTier,
    DistributorCreateRequest,
    DistributorResponse,
    DistributorUpdateRequest,
)

router = APIRouter(prefix="/distributors", tags=["Distributors"])


def _load_distributor(db: Session, distributor_id: UUID) -> Distributor:
    dist = (
        db.query(Distributor)
        .options(
            selectinload(Distributor.daily_prices).selectinload(
                DistributorDailyPrice.discount_tiers
            ),
            selectinload(Distributor.delivery_params),
        )
        .filter(Distributor.id == distributor_id)
        .first()
    )

    if not dist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Distributor not found",
        )

    return dist


def _building_to_response(building: Building) -> BuildingResponse:
    return BuildingResponse(
        id=building.id,
        name=building.name,
        location=building.location,
        max_capacity_kg=float(building.max_capacity_kg),
        initial_inventory_kg=float(building.initial_inventory_kg),
        current_inventory_kg=float(building.current_inventory_kg),
        daily_demand=[
            DailyDemand(day=d.day, demand_kg=float(d.demand_kg))
            for d in sorted(building.daily_demand, key=lambda x: x.day)
        ],
        created_at=building.created_at,
        updated_at=building.updated_at,
    )


def _to_response(dist: Distributor) -> DistributorResponse:
    daily_prices = [
        DailyPrice(
            day=p.day,
            base_price=float(p.base_price),
            availability_kg=float(p.availability_kg),
            discount_tiers=[
                DiscountTier(
                    level=t.level,
                    quantity_kg=float(t.quantity_kg),
                    unit_price=float(t.unit_price),
                )
                for t in sorted(p.discount_tiers, key=lambda x: x.level)
            ],
        )
        for p in sorted(dist.daily_prices, key=lambda x: x.day)
    ]

    delivery_params = [
        DeliveryParams(
            building_id=str(p.building_id),
            lead_time_days=p.lead_time_days,
            fixed_cost_pln=float(p.fixed_cost_pln),
            correction_cost_per_kg=float(p.correction_cost_per_kg),
            max_correction_kg=float(p.max_correction_kg),
        )
        for p in dist.delivery_params
    ]

    return DistributorResponse(
        id=dist.id,
        username=dist.username,
        contact_email=dist.contact_email,
        contact_phone=dist.contact_phone,
        active=dist.active,
        daily_prices=daily_prices,
        delivery_params=delivery_params,
        created_at=dist.created_at,
        updated_at=dist.updated_at,
    )


def _replace_prices(
    db: Session,
    dist: Distributor,
    daily_prices: list[DailyPrice],
) -> None:
    for p in dist.daily_prices:
        db.delete(p)

    db.flush()

    for price in daily_prices:
        daily_price = DistributorDailyPrice(
            distributor_id=dist.id,
            day=price.day,
            base_price=price.base_price,
            availability_kg=price.availability_kg,
        )
        db.add(daily_price)
        db.flush()

        for tier in price.discount_tiers:
            db.add(
                DistributorDiscountTier(
                    distributor_id=dist.id,
                    day=price.day,
                    level=tier.level,
                    quantity_kg=tier.quantity_kg,
                    unit_price=tier.unit_price,
                )
            )


def _replace_delivery_params(
    db: Session,
    dist: Distributor,
    delivery_params: list[DeliveryParams],
) -> None:
    seen_buildings: set[UUID] = set()

    for param in delivery_params:
        try:
            building_id = UUID(param.building_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid building_id: {param.building_id}",
            )

        if building_id in seen_buildings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate delivery parameter for building: {param.building_id}",
            )

        if not db.get(Building, building_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Building not found: {param.building_id}",
            )

        seen_buildings.add(building_id)

    for p in dist.delivery_params:
        db.delete(p)

    db.flush()

    for param in delivery_params:
        db.add(
            DeliveryParam(
                distributor_id=dist.id,
                building_id=UUID(param.building_id),
                lead_time_days=param.lead_time_days,
                fixed_cost_pln=param.fixed_cost_pln,
                correction_cost_per_kg=param.correction_cost_per_kg,
                max_correction_kg=param.max_correction_kg,
            )
        )


@router.get("", response_model=list[DistributorResponse])
def list_distributors(
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
        .all()
    )

    return [_to_response(d) for d in distributors]


@router.post(
    "",
    response_model=DistributorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_distributor(
    body: DistributorCreateRequest,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    dist = Distributor(
        username=body.username,
        contact_email=body.contact_email,
        contact_phone=body.contact_phone,
    )

    db.add(dist)
    db.flush()

    _replace_prices(db, dist, body.daily_prices)
    _replace_delivery_params(db, dist, body.delivery_params)

    db.commit()

    return _to_response(_load_distributor(db, dist.id))


@router.get(
    "/self/prices",
    response_model=DistributorResponse,
    tags=["Distributors - Self Service"],
)
def get_own_prices(
    api_key: Annotated[ApiKey, Depends(get_distributor_by_api_key)],
    db: Session = Depends(get_db),
):
    return _to_response(_load_distributor(db, api_key.distributor_id))


@router.get(
    "/self/available-buildings",
    response_model=list[BuildingResponse],
    tags=["Distributors - Self Service"],
)
def get_own_available_buildings(
    _: Annotated[ApiKey, Depends(get_distributor_by_api_key)],
    db: Session = Depends(get_db),
):
    buildings = (
        db.query(Building)
        .options(selectinload(Building.daily_demand))
        .order_by(Building.name)
        .all()
    )

    return [_building_to_response(building) for building in buildings]


@router.put(
    "/self/prices",
    response_model=DistributorResponse,
    tags=["Distributors - Self Service"],
)
def update_own_prices(
    body: DistributorUpdateRequest,
    api_key: Annotated[ApiKey, Depends(get_distributor_by_api_key)],
    db: Session = Depends(get_db),
):
    dist = _load_distributor(db, api_key.distributor_id)

    _apply_update(db, dist, body)

    db.commit()

    return _to_response(_load_distributor(db, dist.id))


@router.get("/{distributor_id}", response_model=DistributorResponse)
def get_distributor(
    distributor_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    return _to_response(_load_distributor(db, distributor_id))


@router.put("/{distributor_id}", response_model=DistributorResponse)
def update_distributor(
    distributor_id: UUID,
    body: DistributorUpdateRequest,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    dist = _load_distributor(db, distributor_id)

    _apply_update(db, dist, body)

    db.commit()

    return _to_response(_load_distributor(db, distributor_id))


@router.delete("/{distributor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_distributor(
    distributor_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    dist = db.get(Distributor, distributor_id)

    if not dist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Distributor not found",
        )

    db.query(OrderItem).filter(OrderItem.distributor_id == distributor_id).delete(
        synchronize_session=False
    )
    db.query(OptimizationOrderItem).filter(
        OptimizationOrderItem.distributor_id == distributor_id
    ).delete(synchronize_session=False)
    db.delete(dist)
    db.commit()


def _apply_update(
    db: Session,
    dist: Distributor,
    body: DistributorUpdateRequest,
) -> None:
    if body.username is not None:
        dist.username = body.username

    if body.contact_email is not None:
        dist.contact_email = body.contact_email

    if body.contact_phone is not None:
        dist.contact_phone = body.contact_phone

    if body.daily_prices is not None:
        _replace_prices(db, dist, body.daily_prices)

    if body.delivery_params is not None:
        _replace_delivery_params(db, dist, body.delivery_params)
