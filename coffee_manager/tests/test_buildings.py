import uuid


def _make_payload(name="HQ", capacity=500, init=100, demand=None):
    return {
        "name": name,
        "location": "Warsaw",
        "max_capacity_kg": capacity,
        "initial_inventory_kg": init,
        "daily_demand": demand
        if demand is not None
        else [{"day": 1, "demand_kg": 10}, {"day": 2, "demand_kg": 12}],
    }


def test_list_buildings_empty(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get("/buildings", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_building(client, auth_headers):
    headers, _ = auth_headers
    resp = client.post("/buildings", json=_make_payload(), headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "HQ"
    assert body["max_capacity_kg"] == 500
    assert body["initial_inventory_kg"] == 100
    assert body["current_inventory_kg"] == 100  # mirrors initial on create
    assert len(body["daily_demand"]) == 2
    assert body["daily_demand"][0]["day"] == 1  # sorted


def test_get_building_404(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get(f"/buildings/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


def test_get_building_roundtrip(client, auth_headers):
    headers, _ = auth_headers
    created = client.post("/buildings", json=_make_payload(), headers=headers).json()
    resp = client.get(f"/buildings/{created['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_update_building_replaces_demand(client, auth_headers):
    headers, _ = auth_headers
    created = client.post("/buildings", json=_make_payload(), headers=headers).json()
    new_payload = _make_payload(
        name="HQ2", capacity=600, init=50, demand=[{"day": 1, "demand_kg": 99}]
    )
    resp = client.put(f"/buildings/{created['id']}", json=new_payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "HQ2"
    assert body["max_capacity_kg"] == 600
    assert len(body["daily_demand"]) == 1
    assert body["daily_demand"][0]["demand_kg"] == 99


def test_delete_building(client, auth_headers):
    headers, _ = auth_headers
    created = client.post("/buildings", json=_make_payload(), headers=headers).json()
    resp = client.delete(f"/buildings/{created['id']}", headers=headers)
    assert resp.status_code == 204
    assert client.get(f"/buildings/{created['id']}", headers=headers).status_code == 404


def test_delete_building_404(client, auth_headers):
    headers, _ = auth_headers
    resp = client.delete(f"/buildings/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404
