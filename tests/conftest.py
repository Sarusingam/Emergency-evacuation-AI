"""
Pytest Configuration and Fixtures.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def demo_zones():
    """Sample zone data for testing."""
    return {
        "zone_a": {
            "id": "zone_a", "name": "Zone A", "crowd_count": 800,
            "area": 40000, "center_lat": 40.7145, "center_lon": -74.008,
            "radius": 200,
        },
        "zone_b": {
            "id": "zone_b", "name": "Zone B", "crowd_count": 1200,
            "area": 62500, "center_lat": 40.7145, "center_lon": -74.004,
            "radius": 250,
        },
        "zone_c": {
            "id": "zone_c", "name": "Zone C", "crowd_count": 500,
            "area": 32400, "center_lat": 40.711, "center_lon": -74.008,
            "radius": 180,
        },
        "zone_d": {
            "id": "zone_d", "name": "Zone D", "crowd_count": 2000,
            "area": 90000, "center_lat": 40.711, "center_lon": -74.004,
            "radius": 300,
        },
    }


@pytest.fixture
def demo_roads():
    """Sample road data for testing."""
    return {
        "road_r1": {
            "id": "road_r1", "name": "R1", "from_node": "zone_a",
            "to_node": "zone_b", "length": 500, "travel_time": 6.0,
            "capacity": 800, "congestion": 0.3, "risk": 0.2, "blocked": False,
        },
        "road_r2": {
            "id": "road_r2", "name": "R2", "from_node": "zone_a",
            "to_node": "zone_c", "length": 400, "travel_time": 5.0,
            "capacity": 600, "congestion": 0.2, "risk": 0.1, "blocked": False,
        },
        "road_r5": {
            "id": "road_r5", "name": "R5", "from_node": "zone_b",
            "to_node": "exit_east", "length": 350, "travel_time": 4.5,
            "capacity": 1000, "congestion": 0.2, "risk": 0.1, "blocked": False,
        },
        "road_r8": {
            "id": "road_r8", "name": "R8", "from_node": "zone_a",
            "to_node": "exit_north", "length": 250, "travel_time": 3.0,
            "capacity": 1500, "congestion": 0.2, "risk": 0.1, "blocked": False,
        },
    }


@pytest.fixture
def demo_exits():
    """Sample exit data for testing."""
    return {
        "exit_north": {
            "id": "exit_north", "name": "North Exit",
            "lat": 40.7165, "lon": -74.008,
            "capacity": 1500, "flow_rate": 200, "current_load": 0,
        },
        "exit_east": {
            "id": "exit_east", "name": "East Exit",
            "lat": 40.7145, "lon": -74.001,
            "capacity": 1000, "flow_rate": 150, "current_load": 0,
        },
    }


@pytest.fixture
def demo_vehicles():
    """Sample vehicle data for testing."""
    return {
        "bus_1": {
            "id": "bus_1", "type": "bus", "capacity": 50,
            "lat": 40.715, "lon": -74.007, "assigned_zone": None,
            "status": "available",
        },
        "ambulance_1": {
            "id": "ambulance_1", "type": "ambulance", "capacity": 8,
            "lat": 40.713, "lon": -74.006, "assigned_zone": None,
            "status": "available",
        },
    }
