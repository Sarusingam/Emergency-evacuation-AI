"""
run.py — Main entry point for Emergency Evacuation AI.

Starts the FastAPI backend server. In demo mode, runs without
any external dependencies (no GPU, PostgreSQL, Redis, OSRM, or LLM API keys).

Usage:
    python run.py              # Start backend server
    python run.py --demo       # Run interactive demo (no server)
    python run.py --test       # Run system tests
"""

import sys
import argparse
import logging
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the FastAPI backend server."""
    import uvicorn
    from backend.config import settings

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    display_host = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host

    print("\n" + "=" * 60)
    print("  🚨 Emergency Evacuation AI — Backend Server")
    print("=" * 60)
    print(f"  Mode:      {settings.APP_MODE}")
    print(f"  Server:    http://{display_host}:{port}")
    print(f"  API Docs:  http://{display_host}:{port}/docs")
    print(f"  Dashboard: http://localhost:5173 (start with npm run dev)")
    print("=" * 60 + "\n")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG,
        reload_dirs=["backend", "agents", "communication", "computer_vision", "config", "database", "models", "optimization", "routing", "simulation"],
        reload_excludes=[".venv", "venv", "data", "logs", "*.db", "*.sqlite", "*.sqlite3"],
        log_level=settings.LOG_LEVEL.lower(),
    )


def run_demo():
    """Run the interactive demo."""
    from scripts.run_demo import main
    main()


def run_tests():
    """Run system tests."""
    from scripts.test_system import main
    sys.exit(main())


def main():
    parser = argparse.ArgumentParser(
        description="Emergency Evacuation AI System",
    )
    parser.add_argument("--demo", action="store_true", help="Run interactive demo")
    parser.add_argument("--test", action="store_true", help="Run system tests")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")

    args = parser.parse_args()

    if args.demo:
        run_demo()
    elif args.test:
        run_tests()
    else:
        start_server(args.host, args.port)


if __name__ == "__main__":
    main()
