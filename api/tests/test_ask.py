"""Tests for /api/ask response shape and correctness."""
from __future__ import annotations

import pytest


def test_ask_awd_understeer(client):
    resp = client.post("/api/ask", json={
        "question": "My AWD S1 car understeers on throttle exit",
        "drivetrain": "AWD",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["safety"]["refused"] is False
    assert data["likely_cause"]
    assert isinstance(data["try_in_order"], list)
    assert len(data["try_in_order"]) >= 1
    assert isinstance(data["watch_for"], list)
    assert isinstance(data["evidence"], list)


def test_ask_rwd_oversteer(client):
    resp = client.post("/api/ask", json={
        "question": "RWD car has oversteer when I get on throttle",
        "drivetrain": "RWD",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["safety"]["refused"] is False


def test_ask_with_car_name(client):
    resp = client.post("/api/ask", json={
        "question": "Ferrari 512 S understeers on exit in S2 class",
        "car": "Ferrari 512 S",
        "drivetrain": "AWD",
        "class_target": "S2",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data


def test_ask_with_discipline(client):
    resp = client.post("/api/ask", json={
        "question": "My AWD car understeers on dirt",
        "discipline": "dirt",
    })
    assert resp.status_code == 200


def test_ask_response_no_stack_trace(client):
    resp = client.post("/api/ask", json={
        "question": "My car has wheelspin and traction issues"
    })
    assert resp.status_code == 200
    import json
    text = json.dumps(resp.json())
    assert "Traceback" not in text
    assert "Exception" not in text
    assert "/private/data" not in text


def test_ask_safety_mode_is_deterministic(client):
    resp = client.post("/api/ask", json={"question": "My AWD car understeers"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["safety"]["mode"] == "deterministic"


def test_cars_search(client):
    resp = client.get("/api/cars/search?q=Ferrari")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "total" in data


def test_cars_search_empty(client):
    resp = client.get("/api/cars/search?q=")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_settings_search(client):
    resp = client.get("/api/settings/search?q=understeer")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
