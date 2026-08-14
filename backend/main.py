"""
FastAPI Main Application — Entry point, lifespan, CORS, routing.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings
from database.database import db_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Starting Emergency Evacuation AI Backend (%s mode)", settings.APP_MODE)

    # Initialize database
    db_manager.db_url = settings.DATABASE_URL
    db_manager.echo = settings.DB_ECHO
    db_manager.initialize()
    db_manager.create_tables()

    # Initialize services
    from backend.services.emergency_service import emergency_service
    emergency_service.initialize()

    logger.info("Backend ready on %s:%d", settings.HOST, settings.PORT)
    yield

    # Shutdown
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Emergency Evacuation AI",
        description="Agentic AI Framework for Distributed Emergency Evacuation Optimization",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    from backend.api.emergency import router as emergency_router
    from backend.api.crowd import router as crowd_router
    from backend.api.routes import router as routes_router
    from backend.api.traffic import router as traffic_router
    from backend.api.agents import router as agents_router
    from backend.api.simulation import router as simulation_router
    from backend.api.dashboard import router as dashboard_router
    from backend.api.user import router as user_router

    app.include_router(emergency_router, prefix="/api/emergency", tags=["Emergency"])
    app.include_router(crowd_router, prefix="/api/crowd", tags=["Crowd"])
    app.include_router(routes_router, prefix="/api/routes", tags=["Routes"])
    app.include_router(traffic_router, prefix="/api/traffic", tags=["Traffic"])
    app.include_router(agents_router, prefix="/api/agents", tags=["Agents"])
    app.include_router(simulation_router, prefix="/api/simulation", tags=["Simulation"])
    app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
    app.include_router(user_router, prefix="/api/user", tags=["User"])

    @app.get("/", tags=["Health"])
    def root():
        return {"status": "ok", "service": "Emergency Evacuation AI", "mode": settings.APP_MODE}

    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "healthy", "mode": settings.APP_MODE}

    return app


app = create_app()
