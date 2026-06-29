from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from coffee_manager.auth import get_current_user
from coffee_manager.database import get_db
from coffee_manager.models import OptimizationResult, Order, OrderItem, User
from coffee_manager.schemas import OrderItem as OrderItemSchema
from coffee_manager.schemas import OrderRecord, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])


def _to_response(order: Order) -> OrderRecord:
    return OrderRecord(
        id=order.id,
        result_id=order.result_id,
        scenario_id=order.scenario_id,
        orders=[
            OrderItemSchema(
                distributor_id=i.distributor_id,
                building_id=i.building_id,
                day=i.day,
                threshold_level=i.threshold_level,
                quantity_kg=float(i.quantity_kg),
            )
            for i in order.items
        ],
        total_cost_pln=float(order.total_cost_pln)
        if order.total_cost_pln is not None
        else None,
        confirmed_by=order.confirmed_by,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("", response_model=list[OrderRecord])
def list_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    order_status: str | None = Query(None, alias="status"),
):
    q = db.query(Order).options(selectinload(Order.items))
    if order_status:
        q = q.filter(Order.status == order_status)
    return [_to_response(o) for o in q.all()]


@router.post("", response_model=OrderRecord, status_code=status.HTTP_201_CREATED)
def confirm_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    result_id: str = Query(...),
):
    result = (
        db.query(OptimizationResult)
        .options(selectinload(OptimizationResult.order_items))
        .filter(OptimizationResult.id == result_id)
        .first()
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Optimization result not found",
        )

    # Check if an order already exists for this scenario (e.g. from a previous result)
    existing_order = (
        db.query(Order).filter(Order.scenario_id == result.scenario_id).first()
    )

    if existing_order:
        # Update existing order with the new result
        order = existing_order
        order.result_id = result.id
        order.total_cost_pln = result.total_cost_pln
        order.confirmed_by = current_user.id
        order.status = "confirmed"
        # Delete old items to replace them with new ones
        db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()
    else:
        # Create a new order
        order = Order(
            result_id=result.id,
            scenario_id=result.scenario_id,
            total_cost_pln=result.total_cost_pln,
            confirmed_by=current_user.id,
            status="confirmed",
        )
        db.add(order)

    db.flush()
    for item in result.order_items:
        db.add(
            OrderItem(
                order_id=order.id,
                distributor_id=item.distributor_id,
                building_id=item.building_id,
                day=item.day,
                threshold_level=item.threshold_level,
                quantity_kg=item.quantity_kg,
            )
        )
    db.commit()
    order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order.id)
        .first()
    )
    return _to_response(order)


@router.get("/{order_id}", response_model=OrderRecord)
def get_order(
    order_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return _to_response(order)


@router.patch("/{order_id}/status", response_model=OrderRecord)
def update_order_status(
    order_id: UUID,
    body: OrderStatusUpdate,
    _: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    order.status = body.status
    db.commit()
    db.refresh(order)
    return _to_response(order)
