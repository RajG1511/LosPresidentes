"""
test_api.py — Tests for Flask API endpoints
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as flask_app_module


@pytest.fixture
def client():
    flask_app_module.app.config["TESTING"] = True
    flask_app_module.app.config["SECRET_KEY"] = "test-secret"
    with flask_app_module.app.test_client() as client:
        yield client


def test_start_returns_200(client):
    res = client.post("/api/start")
    assert res.status_code == 200


def test_start_returns_node_and_player(client):
    res = client.post("/api/start")
    data = res.get_json()
    assert "node" in data
    assert "player" in data


def test_start_node_is_start_001(client):
    res = client.post("/api/start")
    data = res.get_json()
    assert data["node"]["node_id"] == "start_001"


def test_start_player_has_attributes(client):
    res = client.post("/api/start")
    data = res.get_json()
    attrs = data["player"]["attributes"]
    assert "rapport" in attrs
    assert "morale" in attrs
    assert attrs["morale"] == 8


def test_choose_advances_game(client):
    client.post("/api/start")
    res = client.post("/api/choose", json={"choice_index": 0})
    assert res.status_code == 200
    data = res.get_json()
    assert "node" in data
    assert data["node"]["node_id"] == "start_002"


def test_choose_returns_changes(client):
    client.post("/api/start")
    client.post("/api/choose", json={"choice_index": 0})  # → start_002
    res = client.post("/api/choose", json={"choice_index": 0})  # → branch_a_001 (stealth+1, morale-1)
    data = res.get_json()
    assert "changes" in data


def test_choose_invalid_index_returns_400(client):
    client.post("/api/start")
    res = client.post("/api/choose", json={"choice_index": 999})
    assert res.status_code == 400


def test_choose_missing_index_returns_400(client):
    client.post("/api/start")
    res = client.post("/api/choose", json={})
    assert res.status_code == 400


def test_get_state_returns_200(client):
    client.post("/api/start")
    res = client.get("/api/state")
    assert res.status_code == 200
    data = res.get_json()
    assert "node" in data
    assert "player" in data


def test_get_endings_returns_structure(client):
    client.post("/api/start")
    res = client.get("/api/endings")
    assert res.status_code == 200
    data = res.get_json()
    assert "discovered" in data
    assert "all_endings" in data
    assert "total" in data
    assert data["total"] == 5


def test_checkpoint_save_and_load(client):
    client.post("/api/start")
    client.post("/api/choose", json={"choice_index": 0})  # advance

    # Save checkpoint
    res = client.post("/api/checkpoint")
    assert res.status_code == 200
    cid = res.get_json()["checkpoint_id"]
    assert cid

    # Advance more
    client.post("/api/choose", json={"choice_index": 0})

    # Load checkpoint
    res = client.post("/api/load", json={"checkpoint_id": cid})
    assert res.status_code == 200
    data = res.get_json()
    assert data["player"]["current_node"] == "start_002"


def test_load_invalid_checkpoint_returns_404(client):
    client.post("/api/start")
    res = client.post("/api/load", json={"checkpoint_id": "fakeid"})
    assert res.status_code == 404


def test_index_returns_html(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"<!DOCTYPE html>" in res.data or b"html" in res.data.lower()
