"""
Repositories — CRUD operations for all database models.
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from database.models import (
    Emergency, Zone, CrowdObservation, Road,
    EvacuationExit, Vehicle, EvacuationPlan, AgentEvent,
)

logger = logging.getLogger(__name__)


class EmergencyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> Emergency:
        obj = Emergency(**kwargs)
        self.session.add(obj)
        self.session.flush()
        return obj

    def get_by_id(self, emergency_id: str) -> Emergency | None:
        return self.session.query(Emergency).filter_by(emergency_id=emergency_id).first()

    def get_active(self) -> list[Emergency]:
        return self.session.query(Emergency).filter_by(status="active").all()

    def update_status(self, emergency_id: str, status: str) -> None:
        e = self.get_by_id(emergency_id)
        if e:
            e.status = status
            e.updated_at = datetime.now(timezone.utc)


class ZoneRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, zone_id: str, **kwargs) -> Zone:
        zone = self.session.query(Zone).filter_by(zone_id=zone_id).first()
        if zone:
            for k, v in kwargs.items():
                if hasattr(zone, k):
                    setattr(zone, k, v)
        else:
            zone = Zone(zone_id=zone_id, **kwargs)
            self.session.add(zone)
        self.session.flush()
        return zone

    def get_all(self) -> list[Zone]:
        return self.session.query(Zone).all()

    def get_by_id(self, zone_id: str) -> Zone | None:
        return self.session.query(Zone).filter_by(zone_id=zone_id).first()


class CrowdObservationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> CrowdObservation:
        obj = CrowdObservation(**kwargs)
        self.session.add(obj)
        self.session.flush()
        return obj

    def get_latest_by_zone(self, zone_id: str) -> CrowdObservation | None:
        return (self.session.query(CrowdObservation)
                .filter_by(zone_id=zone_id)
                .order_by(CrowdObservation.timestamp.desc())
                .first())


class RoadRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, road_id: str, **kwargs) -> Road:
        road = self.session.query(Road).filter_by(road_id=road_id).first()
        if road:
            for k, v in kwargs.items():
                if hasattr(road, k):
                    setattr(road, k, v)
        else:
            road = Road(road_id=road_id, **kwargs)
            self.session.add(road)
        self.session.flush()
        return road

    def get_all(self) -> list[Road]:
        return self.session.query(Road).all()


class ExitRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, exit_id: str, **kwargs) -> EvacuationExit:
        ex = self.session.query(EvacuationExit).filter_by(exit_id=exit_id).first()
        if ex:
            for k, v in kwargs.items():
                if hasattr(ex, k):
                    setattr(ex, k, v)
        else:
            ex = EvacuationExit(exit_id=exit_id, **kwargs)
            self.session.add(ex)
        self.session.flush()
        return ex

    def get_all(self) -> list[EvacuationExit]:
        return self.session.query(EvacuationExit).all()


class VehicleRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, vehicle_id: str, **kwargs) -> Vehicle:
        v = self.session.query(Vehicle).filter_by(vehicle_id=vehicle_id).first()
        if v:
            for k, v_val in kwargs.items():
                if hasattr(v, k):
                    setattr(v, k, v_val)
        else:
            v = Vehicle(vehicle_id=vehicle_id, **kwargs)
            self.session.add(v)
        self.session.flush()
        return v

    def get_all(self) -> list[Vehicle]:
        return self.session.query(Vehicle).all()


class PlanRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> EvacuationPlan:
        obj = EvacuationPlan(**kwargs)
        self.session.add(obj)
        self.session.flush()
        return obj

    def get_latest(self) -> EvacuationPlan | None:
        return (self.session.query(EvacuationPlan)
                .order_by(EvacuationPlan.created_at.desc())
                .first())


class AgentEventRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> AgentEvent:
        obj = AgentEvent(**kwargs)
        self.session.add(obj)
        self.session.flush()
        return obj

    def get_recent(self, limit: int = 50) -> list[AgentEvent]:
        return (self.session.query(AgentEvent)
                .order_by(AgentEvent.timestamp.desc())
                .limit(limit).all())
