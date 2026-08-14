"""
Backend Config — Settings loaded from .env + YAML.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_yaml(filename: str) -> dict[str, Any]:
    path = CONFIG_DIR / filename
    if path.exists():
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


_settings = load_yaml("settings.yaml")
_thresholds = load_yaml("thresholds.yaml")


class Settings:
    """Application settings from env + YAML."""
    # Server
    HOST: str = os.getenv("HOST", _settings.get("server", {}).get("host", "127.0.0.1"))
    PORT: int = int(os.getenv("PORT", _settings.get("server", {}).get("port", 8000)))
    DEBUG: bool = os.getenv("DEBUG", str(_settings.get("server", {}).get("debug", True))).lower() == "true"
    CORS_ORIGINS: list[str] = _settings.get("server", {}).get("cors_origins", ["http://localhost:5173", "http://localhost:3000"])

    # App
    APP_MODE: str = os.getenv("APP_MODE", _settings.get("app", {}).get("mode", "demo"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", _settings.get("app", {}).get("log_level", "INFO"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", _settings.get("database", {}).get("url", "sqlite:///./data/evacuation.db"))
    DB_ECHO: bool = _settings.get("database", {}).get("echo", False)

    # LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", _settings.get("agents", {}).get("llm", {}).get("provider", "openai"))
    LLM_MODEL: str = os.getenv("LLM_MODEL", _settings.get("agents", {}).get("llm", {}).get("model", "gpt-4o-mini"))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Agents
    MAX_REPLAN_CYCLES: int = _settings.get("agents", {}).get("max_replan_cycles", 10)

    # Communication
    USE_REDIS: bool = os.getenv("USE_REDIS", str(_settings.get("communication", {}).get("use_redis", False))).lower() == "true"
    REDIS_URL: str = os.getenv("REDIS_URL", _settings.get("communication", {}).get("redis_url", "redis://localhost:6379/0"))


settings = Settings()
