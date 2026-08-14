"""
Seed Demo — Populate database with demo scenario data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.database import db_manager
from database.seed import seed_demo_data


def main():
    print("=== Seeding Demo Data ===")
    db_manager.initialize()
    db_manager.create_tables()

    session = next(db_manager.get_session())
    try:
        seed_demo_data(session, "default_demo")
        print("✅ Demo data seeded successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
