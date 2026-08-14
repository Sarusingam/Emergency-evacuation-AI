"""
Demo Map Data — Hyderabad Road Network Definition.

Provides the Hyderabad demonstration road network as node/edge data for
building the NetworkX graph. Maps directly to scenarios.yaml.
"""

from __future__ import annotations

from typing import Any


def get_demo_map_data() -> dict[str, Any]:
    """Get the default demo map data for Hyderabad.

    This matches the 'default_demo' scenario in scenarios.yaml.
    The data is provided programmatically for graph building and tests.

    Returns:
        Dict with 'nodes' and 'edges' for the Hyderabad road network.
    """
    nodes = {
        "zone_z1": {
            "id": "zone_z1",
            "type": "zone",
            "name": "Z1 - Miyapur",
            "lat": 17.4960,
            "lon": 78.3540,
        },
        "zone_z2": {
            "id": "zone_z2",
            "type": "zone",
            "name": "Z2 - Raidurg",
            "lat": 17.4430,
            "lon": 78.3770,
        },
        "zone_z3": {
            "id": "zone_z3",
            "type": "zone",
            "name": "Z3 - Nagole",
            "lat": 17.3690,
            "lon": 78.5620,
        },
        "zone_z4": {
            "id": "zone_z4",
            "type": "zone",
            "name": "Z4 - LB Nagar",
            "lat": 17.3500,
            "lon": 78.5520,
        },
        "zone_z5": {
            "id": "zone_z5",
            "type": "zone",
            "name": "Z5 - MGBS",
            "lat": 17.3780,
            "lon": 78.4800,
        },
        "zone_z6": {
            "id": "zone_z6",
            "type": "zone",
            "name": "Z6 - JBS",
            "lat": 17.4470,
            "lon": 78.4980,
        },
        "exit_north": {
            "id": "exit_north",
            "type": "exit",
            "name": "North Evacuation Point (Medchal / ORR)",
            "lat": 17.6300,
            "lon": 78.4800,
        },
        "exit_east": {
            "id": "exit_east",
            "type": "exit",
            "name": "East Evacuation Point (Ghatkesar / NH65)",
            "lat": 17.4400,
            "lon": 78.6800,
        },
        "exit_south": {
            "id": "exit_south",
            "type": "exit",
            "name": "South Evacuation Point (Shamshabad / ORR)",
            "lat": 17.2400,
            "lon": 78.4300,
        },
        "exit_west": {
            "id": "exit_west",
            "type": "exit",
            "name": "West Evacuation Point (Patancheru / NH65)",
            "lat": 17.5300,
            "lon": 78.2600,
        },
    }

    edges = [
        {
            "id": "road_r1",
            "name": "R1 - Miyapur to Raidurg (Hitec City Rd)",
            "from_node": "zone_z1",
            "to_node": "zone_z2",
            "length": 7500,
            "travel_time": 12.0,
            "capacity": 1500,
            "congestion": 0.3,
            "risk": 0.2,
        },
        {
            "id": "road_r2",
            "name": "R2 - Miyapur to JBS (Kukatpally / Balanagar)",
            "from_node": "zone_z1",
            "to_node": "zone_z6",
            "length": 12000,
            "travel_time": 18.0,
            "capacity": 1800,
            "congestion": 0.25,
            "risk": 0.1,
        },
        {
            "id": "road_r3",
            "name": "R3 - Raidurg to MGBS (Madhapur / Lakdikapul)",
            "from_node": "zone_z2",
            "to_node": "zone_z5",
            "length": 14000,
            "travel_time": 20.0,
            "capacity": 2000,
            "congestion": 0.4,
            "risk": 0.3,
        },
        {
            "id": "road_r4",
            "name": "R4 - JBS to MGBS (Tank Bund / Abids)",
            "from_node": "zone_z6",
            "to_node": "zone_z5",
            "length": 9000,
            "travel_time": 15.0,
            "capacity": 1600,
            "congestion": 0.45,
            "risk": 0.35,
        },
        {
            "id": "road_r5",
            "name": "R5 - MGBS to LB Nagar (Malakpet / Dilsukhnagar)",
            "from_node": "zone_z5",
            "to_node": "zone_z4",
            "length": 8500,
            "travel_time": 14.0,
            "capacity": 1800,
            "congestion": 0.3,
            "risk": 0.2,
        },
        {
            "id": "road_r6",
            "name": "R6 - Nagole to LB Nagar (Inner Ring Road)",
            "from_node": "zone_z3",
            "to_node": "zone_z4",
            "length": 3500,
            "travel_time": 6.0,
            "capacity": 1200,
            "congestion": 0.2,
            "risk": 0.1,
        },
        {
            "id": "road_r7",
            "name": "R7 - JBS to Nagole (Tarnaka / Uppal)",
            "from_node": "zone_z6",
            "to_node": "zone_z3",
            "length": 11000,
            "travel_time": 16.0,
            "capacity": 1500,
            "congestion": 0.25,
            "risk": 0.15,
        },
        {
            "id": "road_r8",
            "name": "R8 - Miyapur to West Evacuation Point",
            "from_node": "zone_z1",
            "to_node": "exit_west",
            "length": 8000,
            "travel_time": 10.0,
            "capacity": 2500,
            "congestion": 0.15,
            "risk": 0.1,
        },
        {
            "id": "road_r9",
            "name": "R9 - JBS to North Evacuation Point",
            "from_node": "zone_z6",
            "to_node": "exit_north",
            "length": 18000,
            "travel_time": 22.0,
            "capacity": 3000,
            "congestion": 0.2,
            "risk": 0.1,
        },
        {
            "id": "road_r10",
            "name": "R10 - Nagole to East Evacuation Point",
            "from_node": "zone_z3",
            "to_node": "exit_east",
            "length": 14000,
            "travel_time": 18.0,
            "capacity": 2500,
            "congestion": 0.2,
            "risk": 0.15,
        },
        {
            "id": "road_r11",
            "name": "R11 - LB Nagar to South Evacuation Point",
            "from_node": "zone_z4",
            "to_node": "exit_south",
            "length": 19000,
            "travel_time": 24.0,
            "capacity": 3000,
            "congestion": 0.25,
            "risk": 0.2,
        },
        {
            "id": "road_r12",
            "name": "R12 - MGBS to South Evacuation Point (Chandrayangutta)",
            "from_node": "zone_z5",
            "to_node": "exit_south",
            "length": 18000,
            "travel_time": 22.0,
            "capacity": 2500,
            "congestion": 0.35,
            "risk": 0.25,
        },
    ]

    return {"nodes": nodes, "edges": edges}
