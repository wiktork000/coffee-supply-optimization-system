"""Tests for /optimization endpoints. The optimizer HTTP call is mocked."""

import uuid
from unittest.mock import patch

import httpx

from coffee_manager.routers import optimization as optimization_module


def _building(client, headers, name="HQ"):
    return client.post(
        "/buildings",
        json={
            "name": name,
            "max_capacity_kg": 500,
            "initial_inventory_kg": 100,
            "daily_demand": [{"day": 1, "demand_kg": 10}, {"day": 2, "demand_kg": 12}],
        },
        headers=headers,
    ).json()


def _distributor(client, headers, building_id, name="Acme"):
    return client.post(
        "/distributors",
        json={
            "username": name,
            "contact_email": f"{name.lower()}@example.com",
            "contact_phone": f"+48-{name}",
            "daily_prices": [
                {
                    "day": 1,
                    "base_price": 20.0,
                    "availability_kg": 1000,
                    "discount_tiers": [
                        {"level": 1, "quantity_kg": 100, "unit_price": 18.0}
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
                {"building_id": building_id, "lead_time_days": 1, "fixed_cost_pln": 50}
            ],
        },
        headers=headers,
    ).json()


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "err",
                request=httpx.Request("POST", "http://x"),
                response=self,  # type: ignore[arg-type]
            )


def _ok_optimizer_payload(distributor_id, building_id):
    return {
        "status": "Optimal",
        "total_cost_pln": 999.5,
        "solver_message": "solved",
        "cost_breakdown": {
            "purchase_base": 500,
            "purchase_discount": 100,
            "fixed_delivery": 50,
            "total": 650,
        },
        "orders": [
            {
                "distributor_id": distributor_id,
                "building_id": building_id,
                "day": 1,
                "threshold_level": 0,
                "quantity_kg": 25,
            }
        ],
        "inventory_levels": [
            {"building_id": building_id, "day": 1, "level_kg": 115},
            {"building_id": building_id, "day": 2, "level_kg": 103},
        ],
    }


def test_list_optimizations_empty(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get("/optimization", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_run_optimization_happy_path(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    d = _distributor(client, headers, b["id"])

    fake_payload = _ok_optimizer_payload(d["id"], b["id"])
    with patch.object(
        optimization_module.httpx, "post", return_value=_FakeResponse(200, fake_payload)
    ):
        resp = client.post(
            "/optimization",
            json={
                "name": "scenario-1",
                "planning_horizon_days": 2,
                "distributor_ids": [d["id"]],
                "building_ids": [b["id"]],
            },
            headers=headers,
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "Optimal"
    assert body["total_cost_pln"] == 999.5
    assert body["cost_breakdown"]["total"] == 650
    assert len(body["orders"]) == 1
    assert body["orders"][0]["quantity_kg"] == 25
    assert len(body["inventory_levels"]) == 2

    # Persisted: list_optimizations should now return it.
    listing = client.get("/optimization", headers=headers).json()
    assert len(listing) == 1
    assert listing[0]["result_id"] == body["result_id"]


def test_run_optimization_unknown_distributor_404(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    resp = client.post(
        "/optimization",
        json={
            "name": "x",
            "planning_horizon_days": 1,
            "distributor_ids": [str(uuid.uuid4())],
            "building_ids": [b["id"]],
        },
        headers=headers,
    )
    assert resp.status_code == 404


def test_run_optimization_unknown_building_404(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    d = _distributor(client, headers, b["id"])
    resp = client.post(
        "/optimization",
        json={
            "name": "x",
            "planning_horizon_days": 1,
            "distributor_ids": [d["id"]],
            "building_ids": [str(uuid.uuid4())],
        },
        headers=headers,
    )
    assert resp.status_code == 404


def test_optimizer_http_error_returns_502(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    d = _distributor(client, headers, b["id"])
    with patch.object(
        optimization_module.httpx,
        "post",
        return_value=_FakeResponse(500, {}, text="boom"),
    ):
        resp = client.post(
            "/optimization",
            json={
                "name": "x",
                "planning_horizon_days": 1,
                "distributor_ids": [d["id"]],
                "building_ids": [b["id"]],
            },
            headers=headers,
        )
    assert resp.status_code == 502


def test_optimizer_unreachable_returns_503(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    d = _distributor(client, headers, b["id"])

    def _raise(*a, **kw):
        raise httpx.ConnectError("cannot connect")

    with patch.object(optimization_module.httpx, "post", side_effect=_raise):
        resp = client.post(
            "/optimization",
            json={
                "name": "x",
                "planning_horizon_days": 1,
                "distributor_ids": [d["id"]],
                "building_ids": [b["id"]],
            },
            headers=headers,
        )
    assert resp.status_code == 503


def _ok_correction_payload(distributor_id, building_id):
    return {
        "status": "Optimal",
        "total_cost_pln": 720.0,
        "solver_message": "solved",
        "final_orders": [
            {
                "distributor_id": distributor_id,
                "building_id": building_id,
                "day": 1,
                "threshold_level": 0,
                "quantity_kg": 30,
            }
        ],
        "corrections": [
            {
                "distributor_id": distributor_id,
                "building_id": building_id,
                "day": 1,
                "threshold_level": 0,
                "type": "increase",
                "quantity_kg": 5,
            }
        ],
        "inventory_levels": [
            {"building_id": building_id, "day": 1, "level_kg": 120},
            {"building_id": building_id, "day": 2, "level_kg": 108},
        ],
    }


def _seed_optimization(client, headers):
    """Create a building+distributor and run one optimization; return its bodies."""
    b = _building(client, headers)
    d = _distributor(client, headers, b["id"])
    with patch.object(
        optimization_module.httpx,
        "post",
        return_value=_FakeResponse(200, _ok_optimizer_payload(d["id"], b["id"])),
    ):
        opt = client.post(
            "/optimization",
            json={
                "name": "scenario-1",
                "planning_horizon_days": 2,
                "distributor_ids": [d["id"]],
                "building_ids": [b["id"]],
            },
            headers=headers,
        ).json()
    return b, d, opt


def test_run_correction_happy_path(client, auth_headers):
    headers, _ = auth_headers
    b, d, opt = _seed_optimization(client, headers)

    payload = _ok_correction_payload(d["id"], b["id"])
    with patch.object(
        optimization_module.httpx, "post", return_value=_FakeResponse(200, payload)
    ) as mock_post:
        resp = client.post(
            "/optimization/correction",
            json={"name": "correction-1", "previous_result_id": opt["result_id"]},
            headers=headers,
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "Optimal"
    assert body["total_cost_pln"] == 720.0
    assert body["scenario_id"] == opt["scenario_id"]
    assert body["result_id"] != opt["result_id"]
    assert len(body["orders"]) == 1
    assert len(body["corrections"]) == 1
    assert body["corrections"][0]["type"] == "increase"
    assert body["corrections"][0]["quantity_kg"] == 5

    # The optimizer was called on the correction endpoint with the right payload.
    called_url = mock_post.call_args.args[0]
    sent = mock_post.call_args.kwargs["json"]
    assert called_url.endswith("/optimize/correction")
    assert len(sent["previous_orders"]) == 1
    assert sent["correction_costs"] and sent["correction_limits"]
    # Costs/limits expanded across the 2-day horizon for the single d↔b pair.
    assert {c["day"] for c in sent["correction_costs"]} == {1, 2}

    # Persisted under the same scenario: now two results listed.
    listing = client.get("/optimization", headers=headers).json()
    assert len(listing) == 2


def test_run_correction_unknown_previous_result_404(client, auth_headers):
    headers, _ = auth_headers
    resp = client.post(
        "/optimization/correction",
        json={"name": "x", "previous_result_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert resp.status_code == 404


def test_run_correction_optimizer_http_error_returns_502(client, auth_headers):
    headers, _ = auth_headers
    _, _, opt = _seed_optimization(client, headers)
    with patch.object(
        optimization_module.httpx,
        "post",
        return_value=_FakeResponse(500, {}, text="boom"),
    ):
        resp = client.post(
            "/optimization/correction",
            json={"name": "x", "previous_result_id": opt["result_id"]},
            headers=headers,
        )
    assert resp.status_code == 502


def test_run_correction_optimizer_unreachable_returns_503(client, auth_headers):
    headers, _ = auth_headers
    _, _, opt = _seed_optimization(client, headers)

    def _raise(*a, **kw):
        raise httpx.ConnectError("cannot connect")

    with patch.object(optimization_module.httpx, "post", side_effect=_raise):
        resp = client.post(
            "/optimization/correction",
            json={"name": "x", "previous_result_id": opt["result_id"]},
            headers=headers,
        )
    assert resp.status_code == 503


def test_get_optimization_result_404(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get(f"/optimization/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


def test_get_optimization_result_roundtrip(client, auth_headers):
    headers, _ = auth_headers
    b = _building(client, headers)
    d = _distributor(client, headers, b["id"])
    fake_payload = _ok_optimizer_payload(d["id"], b["id"])
    with patch.object(
        optimization_module.httpx, "post", return_value=_FakeResponse(200, fake_payload)
    ):
        created = client.post(
            "/optimization",
            json={
                "name": "x",
                "planning_horizon_days": 2,
                "distributor_ids": [d["id"]],
                "building_ids": [b["id"]],
            },
            headers=headers,
        ).json()

    resp = client.get(f"/optimization/{created['result_id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["result_id"] == created["result_id"]
