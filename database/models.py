"""
ORM Models — SQLAlchemy models for all evacuation entities.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Emergency(Base):
    __tablename__ = "emergencies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    emergency_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    emergency_type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="active")
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class Zone(Base):
    __tablename__ = "zones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    center_lat: Mapped[float] = mapped_column(Float, default=0.0)
    center_lon: Mapped[float] = mapped_column(Float, default=0.0)
    radius: Mapped[float] = mapped_column(Float, default=200.0)
    area: Mapped[float] = mapped_column(Float, default=10000.0)
    crowd_count: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)


class CrowdObservation(Base):
    __tablename__ = "crowd_observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(50), index=True)
    count: Mapped[int] = mapped_column(Integer)
    density: Mapped[float] = mapped_column(Float, default=0.0)
    density_level: Mapped[str] = mapped_column(String(20), default="LOW")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Road(Base):
    __tablename__ = "roads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    road_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    from_node: Mapped[str] = mapped_column(String(50))
    to_node: Mapped[str] = mapped_column(String(50))
    length: Mapped[float] = mapped_column(Float, default=100.0)
    capacity: Mapped[int] = mapped_column(Integer, default=500)
    congestion: Mapped[float] = mapped_column(Float, default=0.0)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    risk: Mapped[float] = mapped_column(Float, default=0.0)


class EvacuationExit(Base):
    __tablename__ = "evacuation_exits"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exit_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    lat: Mapped[float] = mapped_column(Float, default=0.0)
    lon: Mapped[float] = mapped_column(Float, default=0.0)
    capacity: Mapped[int] = mapped_column(Integer, default=1000)
    flow_rate: Mapped[int] = mapped_column(Integer, default=150)
    current_load: Mapped[int] = mapped_column(Integer, default=0)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(30))
    capacity: Mapped[int] = mapped_column(Integer, default=50)
    lat: Mapped[float] = mapped_column(Float, default=0.0)
    lon: Mapped[float] = mapped_column(Float, default=0.0)
    assigned_zone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="available")


class EvacuationPlan(Base):
    __tablename__ = "evacuation_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    emergency_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    total_people: Mapped[int] = mapped_column(Integer, default=0)
    people_assigned: Mapped[int] = mapped_column(Integer, default=0)
    assignments: Mapped[dict] = mapped_column(JSON, default=dict)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class AgentEvent(Base):
    __tablename__ = "agent_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(50), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
