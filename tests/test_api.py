"""Tests for FastAPI API endpoints."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_start_emergency():
    response = client.post("/api/emergency/start", json={
        "emergency_type": "chemical_spill",
        "severity": "high",
        "scenario": "default_demo",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


def test_get_status():
    response = client.get("/api/emergency/status")
    assert response.status_code == 200


def test_get_zones():
    response = client.get("/api/crowd/zones")
    assert response.status_code == 200


def test_get_traffic():
    response = client.get("/api/traffic/")
    assert response.status_code == 200


def test_get_routes():
    response = client.get("/api/routes/")
    assert response.status_code == 200


def test_get_plan():
    response = client.get("/api/routes/plan")
    assert response.status_code == 200


def test_get_agents():
    response = client.get("/api/agents/status")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data


def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "state" in data
    assert "zones" in data


def test_simulation_step():
    response = client.post("/api/simulation/step")
    assert response.status_code == 200


def test_block_road():
    response = client.post("/api/emergency/block-road", json={
        "road_id": "road_r4", "reason": "test",
    })
    assert response.status_code == 200


# ── User / Evacuee API Tests ───────────────────────────────────

def test_user_status():
    response = client.get("/api/user/status")
    assert response.status_code == 200
    data = response.json()
    assert "emergency_active" in data
    assert "mode" in data


def test_user_zones():
    response = client.get("/api/user/zones")
    assert response.status_code == 200
    data = response.json()
    assert "zones" in data
    assert len(data["zones"]) > 0
    # Verify no crowd counts or internal metrics exposed
    for z in data["zones"]:
        assert "zone_id" in z
        assert "zone_name" in z
        assert "crowd_count" not in z


def test_user_route():
    # Start emergency first
    client.post("/api/emergency/start", json={
        "emergency_type": "chemical_spill", "severity": "high", "scenario": "default_demo",
    })
    response = client.get("/api/user/route?zone_id=zone_z1")
    assert response.status_code == 200
    data = response.json()
    assert data["emergency_active"] is True
    assert data["zone_id"] == "zone_z1"
    assert "destination_exit_name" in data
    assert "route_summary" in data
    # Verify no internal agent state exposed
    assert "coordinator_reasoning" not in data
    assert "agents" not in data


def test_user_route_no_zone():
    response = client.get("/api/user/route")
    assert response.status_code == 200
    data = response.json()
    assert "Select your location" in data["message"]


def test_user_alerts():
    response = client.get("/api/user/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data


def test_user_location_resolve():
    response = client.post("/api/user/location", json={"lat": 17.4960, "lon": 78.3540})
    assert response.status_code == 200
    data = response.json()
    assert data["zone_id"] == "zone_z1"
    assert "Miyapur" in data["zone_name"]


def test_user_route_change_scenario():
    """Verify route changes for user when operator blocks a road."""
    # 1. Start emergency
    client.post("/api/emergency/start", json={
        "emergency_type": "chemical_spill", "severity": "high", "scenario": "default_demo",
    })
    # 2. Get initial user route for zone_z1
    r1 = client.get("/api/user/route?zone_id=zone_z1")
    v1 = r1.json()["route_version"]

    # 3. Operator blocks road_r4
    client.post("/api/emergency/block-road", json={"road_id": "road_r4", "reason": "damage"})

    # 4. Advance simulation (triggers agent replan)
    client.post("/api/emergency/step")

    # 5. Get updated route for user
    r2 = client.get("/api/user/route?zone_id=zone_z1")
    data2 = r2.json()

    # Route version should increment
    assert data2["route_version"] > v1


