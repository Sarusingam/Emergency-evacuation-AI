"""
Database Seeder — Populate demo data from scenario.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from simulation.scenario_manager import ScenarioManager

logger = logging.getLogger(__name__)


def seed_demo_data(session: Session, scenario_name: str = "default_demo") -> None:
    """Seed the database with demo scenario data.

    Args:
        session: Active database session.
        scenario_name: Scenario to load.
    """
    from database.repositories import (
        EmergencyRepository, ZoneRepository, RoadRepository,
        ExitRepository, VehicleRepository,
    )

    sm = ScenarioManager()
    data = sm.get_scenario_state_data(scenario_name)

    # Seed emergency
    er = EmergencyRepository(session)
    er.create(
        emergency_id="emergency_001",
        emergency_type="chemical_spill",
        severity="high",
        status="active",
        description="Demo emergency scenario",
    )

    # Seed zones
    zr = ZoneRepository(session)
    for zid, zdata in data["zones"].items():
        zr.upsert(zone_id=zid, name=zdata.get("name", zid),
                   center_lat=zdata.get("center_lat", 0),
                   center_lon=zdata.get("center_lon", 0),
                   radius=zdata.get("radius", 200),
                   area=zdata.get("area", 10000),
                   crowd_count=zdata.get("crowd_count", 0))

    # Seed roads
    rr = RoadRepository(session)
    for rid, rdata in data["roads"].items():
        rr.upsert(road_id=rid, name=rdata.get("name", rid),
                   from_node=rdata.get("from_node", ""),
                   to_node=rdata.get("to_node", ""),
                   length=rdata.get("length", 100),
                   capacity=rdata.get("capacity", 500),
                   congestion=rdata.get("congestion", 0.0),
                   blocked=rdata.get("blocked", False),
                   risk=rdata.get("risk", 0.0))

    # Seed exits
    exr = ExitRepository(session)
    for eid, edata in data["exits"].items():
        exr.upsert(exit_id=eid, name=edata.get("name", eid),
                    lat=edata.get("lat", 0), lon=edata.get("lon", 0),
                    capacity=edata.get("capacity", 1000),
                    flow_rate=edata.get("flow_rate", 150))

    # Seed vehicles
    vr = VehicleRepository(session)
    for vid, vdata in data["vehicles"].items():
        vr.upsert(vehicle_id=vid, vehicle_type=vdata.get("type", "bus"),
                   capacity=vdata.get("capacity", 50),
                   lat=vdata.get("lat", 0), lon=vdata.get("lon", 0),
                   status=vdata.get("status", "available"))

    session.commit()
    logger.info("Demo data seeded successfully")
