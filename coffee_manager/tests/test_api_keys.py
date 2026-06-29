import uuid


def _building(client, headers):
    return client.post(
        "/buildings",
        json={
            "name": "HQ",
            "max_capacity_kg": 500,
            "initial_inventory_kg": 0,
            "daily_demand": [{"day": 1, "demand_kg": 1}],
        },
        headers=headers,
    ).json()


def _distributor(client, headers, building_id):
    return client.post(
        "/distributors",
        json={
            "username": "Acme",
            "contact_email": "acme@example.com",
            "contact_phone": "+48-1",
            "daily_prices": [
                {
                    "day": 1,
                    "base_price": 10,
                    "availability_kg": 100,
                    "discount_tiers": [],
                }
            ],
            "delivery_params": [
                {"building_id": building_id, "lead_time_days": 1, "fixed_cost_pln": 0}
            ],
        },
        headers=headers,
    ).json()


def test_list_api_keys_for_unknown_distributor_404(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get(f"/distributors/{uuid.uuid4()}/api-keys", headers=headers)
    assert resp.status_code == 404


def test_create_and_list_api_key(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    d = _distributor(client, headers, b["id"])

    create = client.post(
        f"/distributors/{d['id']}/api-keys",
        json={"label": "primary"},
        headers=headers,
    )
    assert create.status_code == 201
    key_body = create.json()
    assert key_body["label"] == "primary"
    assert key_body["active"] is True
    assert key_body["key"].startswith("cof_")
    assert key_body["distributor_id"] == d["id"]

    listing = client.get(f"/distributors/{d['id']}/api-keys", headers=headers)
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) == 1
    assert items[0].get("key") in (None, "")


def test_revoke_api_key(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    d = _distributor(client, headers, b["id"])
    created = client.post(
        f"/distributors/{d['id']}/api-keys",
        json={"label": "x"},
        headers=headers,
    ).json()
    resp = client.delete(f"/api-keys/{created['id']}", headers=headers)
    assert resp.status_code == 204
    listing = client.get(f"/distributors/{d['id']}/api-keys", headers=headers).json()
    assert listing[0]["active"] is False
    assert listing[0]["revoked_at"] is not None


def test_revoke_unknown_api_key_404(client, auth_headers):
    headers, _ = auth_headers
    resp = client.delete(f"/api-keys/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


def test_api_key_authenticates_self_prices(client, auth_headers):
    """End-to-end: created raw key should authenticate /distributors/self/prices."""
    headers, _ = auth_headers
    b = _building(client, headers)
    d = _distributor(client, headers, b["id"])
    raw = client.post(
        f"/distributors/{d['id']}/api-keys",
        json={"label": "primary"},
        headers=headers,
    ).json()["key"]

    resp = client.get("/distributors/self/prices", headers={"X-Api-Key": raw})
    assert resp.status_code == 200
    assert resp.json()["id"] == d["id"]


def test_revoked_api_key_rejected(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    d = _distributor(client, headers, b["id"])
    created = client.post(
        f"/distributors/{d['id']}/api-keys",
        json={"label": "primary"},
        headers=headers,
    ).json()
    raw = created["key"]
    client.delete(f"/api-keys/{created['id']}", headers=headers)

    resp = client.get("/distributors/self/prices", headers={"X-Api-Key": raw})
    assert resp.status_code == 401
