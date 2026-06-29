import uuid


def _building(client, headers, capacity=500, init=100):
    return client.post(
        "/buildings",
        json={
            "name": "HQ",
            "max_capacity_kg": capacity,
            "initial_inventory_kg": init,
            "daily_demand": [{"day": 1, "demand_kg": 1}],
        },
        headers=headers,
    ).json()


def test_inventory_empty(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get("/inventory", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_inventory_lists_with_fill_percent(client, auth_headers):
    headers, _ = auth_headers
    _building(client, headers, capacity=200, init=50)
    resp = client.get("/inventory", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["building_name"] == "HQ"
    assert body[0]["current_inventory_kg"] == 50
    assert body[0]["max_capacity_kg"] == 200
    assert body[0]["fill_percent"] == 25.0


def test_update_inventory(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers, capacity=200, init=50)
    resp = client.put(f"/inventory/{b['id']}?current_kg=120", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["current_inventory_kg"] == 120
    after = client.get("/inventory", headers=headers).json()[0]
    assert after["current_inventory_kg"] == 120


def test_update_inventory_rejects_over_capacity(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers, capacity=200, init=0)
    resp = client.put(f"/inventory/{b['id']}?current_kg=999", headers=headers)
    assert resp.status_code == 422


def test_update_inventory_unknown_building(client, auth_headers):
    headers, _ = auth_headers
    resp = client.put(f"/inventory/{uuid.uuid4()}?current_kg=10", headers=headers)
    assert resp.status_code == 404
