import uuid


def _building(client, headers, name="HQ"):
    payload = {
        "name": name,
        "location": "Warsaw",
        "max_capacity_kg": 500,
        "initial_inventory_kg": 0,
        "daily_demand": [{"day": 1, "demand_kg": 10}],
    }
    return client.post("/buildings", json=payload, headers=headers).json()


def _distributor_payload(building_id, username="Acme"):
    return {
        "username": username,
        "contact_email": f"{username.lower()}@example.com",
        "contact_phone": "+48-100-200-300",
        "daily_prices": [
            {
                "day": 1,
                "base_price": 20.0,
                "availability_kg": 1000,
                "discount_tiers": [
                    {"level": 1, "quantity_kg": 100, "unit_price": 18.0},
                    {"level": 2, "quantity_kg": 500, "unit_price": 15.0},
                ],
            },
            {
                "day": 2,
                "base_price": 21.0,
                "availability_kg": 1000,
                "discount_tiers": [],
            },
        ],
        "delivery_params": [
            {
                "building_id": building_id,
                "lead_time_days": 2,
                "fixed_cost_pln": 50.0,
            }
        ],
    }


def test_list_distributors_empty(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get("/distributors", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_distributor_with_prices(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    resp = client.post(
        "/distributors", json=_distributor_payload(b["id"]), headers=headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "Acme"
    assert len(body["daily_prices"]) == 2
    assert body["daily_prices"][0]["day"] == 1
    assert len(body["daily_prices"][0]["discount_tiers"]) == 2
    assert body["daily_prices"][0]["discount_tiers"][0]["level"] == 1
    assert len(body["delivery_params"]) == 1


def test_get_distributor_404(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get(f"/distributors/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


def test_update_distributor_partial(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    created = client.post(
        "/distributors", json=_distributor_payload(b["id"]), headers=headers
    ).json()
    resp = client.put(
        f"/distributors/{created['id']}",
        json={"contact_email": "new@example.com"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["contact_email"] == "new@example.com"
    # Prices unchanged.
    assert len(resp.json()["daily_prices"]) == 2


def test_update_distributor_replaces_prices(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    created = client.post(
        "/distributors", json=_distributor_payload(b["id"]), headers=headers
    ).json()
    resp = client.put(
        f"/distributors/{created['id']}",
        json={
            "daily_prices": [
                {
                    "day": 3,
                    "base_price": 30.0,
                    "availability_kg": 500,
                    "discount_tiers": [],
                }
            ]
        },
        headers=headers,
    )
    assert resp.status_code == 200
    prices = resp.json()["daily_prices"]
    assert len(prices) == 1
    assert prices[0]["day"] == 3


def test_delete_distributor(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    created = client.post(
        "/distributors", json=_distributor_payload(b["id"]), headers=headers
    ).json()
    assert (
        client.delete(f"/distributors/{created['id']}", headers=headers).status_code
        == 204
    )
    assert (
        client.get(f"/distributors/{created['id']}", headers=headers).status_code == 404
    )


def test_delete_distributor_404(client, auth_headers):
    headers, _ = auth_headers
    assert (
        client.delete(f"/distributors/{uuid.uuid4()}", headers=headers).status_code
        == 404
    )


def test_self_prices_requires_api_key(client):
    # No X-Api-Key header.
    resp = client.get("/distributors/self/prices")
    assert resp.status_code == 401
