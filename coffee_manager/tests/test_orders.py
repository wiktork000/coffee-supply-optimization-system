import uuid

from coffee_manager.models import (
    Building,
    Distributor,
    OptimizationOrderItem,
    OptimizationResult,
    OptimizationScenario,
)


def _seed_result(
    db, *, with_items: bool = True
) -> tuple[OptimizationResult, Building, Distributor]:
    scenario = OptimizationScenario(name="s1", planning_horizon_days=3, decay_rate=0.05)
    db.add(scenario)
    db.flush()
    result = OptimizationResult(
        scenario_id=scenario.id,
        status="Optimal",
        total_cost_pln=1234.5,
    )
    db.add(result)
    db.flush()
    building = Building(
        name="HQ", max_capacity_kg=500, initial_inventory_kg=0, current_inventory_kg=0
    )
    distributor = Distributor(username="Acme", contact_email="a@x", contact_phone="+1")
    db.add_all([building, distributor])
    db.flush()
    if with_items:
        db.add(
            OptimizationOrderItem(
                result_id=result.id,
                distributor_id=distributor.id,
                building_id=building.id,
                day=1,
                threshold_level=0,
                quantity_kg=10,
            )
        )
    db.commit()
    db.refresh(result)
    return result, building, distributor


def test_list_orders_empty(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get("/orders", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_confirm_orders_from_result(client, auth_headers, db):
    headers, _ = auth_headers
    result, building, distributor = _seed_result(db)

    resp = client.post(f"/orders?result_id={result.id}", headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "confirmed"
    assert body["result_id"] == str(result.id)
    assert len(body["orders"]) == 1
    assert body["orders"][0]["quantity_kg"] == 10
    assert body["total_cost_pln"] == 1234.5


def test_confirm_orders_unknown_result_404(client, auth_headers):
    headers, _ = auth_headers
    resp = client.post(f"/orders?result_id={uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


def test_get_order_roundtrip(client, auth_headers, db):
    headers, _ = auth_headers
    result, _, _ = _seed_result(db)
    created = client.post(f"/orders?result_id={result.id}", headers=headers).json()

    resp = client.get(f"/orders/{created['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_order_404(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get(f"/orders/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


def test_update_order_status(client, auth_headers, db):
    headers, _ = auth_headers
    result, _, _ = _seed_result(db)
    created = client.post(f"/orders?result_id={result.id}", headers=headers).json()

    resp = client.patch(
        f"/orders/{created['id']}/status",
        json={"status": "cancelled"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_update_order_status_rejects_invalid(client, auth_headers, db):
    headers, _ = auth_headers
    result, _, _ = _seed_result(db)
    created = client.post(f"/orders?result_id={result.id}", headers=headers).json()

    resp = client.patch(
        f"/orders/{created['id']}/status",
        json={"status": "shipped"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_list_orders_filters_by_status(client, auth_headers, db):
    headers, _ = auth_headers
    result, _, _ = _seed_result(db)
    o1 = client.post(f"/orders?result_id={result.id}", headers=headers).json()
    o2 = client.post(f"/orders?result_id={result.id}", headers=headers).json()
    client.patch(
        f"/orders/{o2['id']}/status",
        json={"status": "cancelled"},
        headers=headers,
    )
    confirmed = client.get("/orders?status=confirmed", headers=headers).json()
    cancelled = client.get("/orders?status=cancelled", headers=headers).json()
    assert {o["id"] for o in confirmed} == {o1["id"]}
    assert {o["id"] for o in cancelled} == {o2["id"]}
