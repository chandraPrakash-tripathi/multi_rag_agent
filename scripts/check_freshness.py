"""
Quick freshness report:

    python -m scripts.check_freshness
    python -m scripts.check_freshness --max-age-hours 48

Exits non-zero if any dataset is stale or failed, so it can also be used as
a CI gate/notification trigger later if you want one.
"""

import argparse
import sys
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_setup.unified_layer.models import DatasetFreshness

# Automatically load variables from your .env file
load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Report dataset ingestion freshness")
    parser.add_argument(
        "--max-age-hours",
        type=int,
        default=36,
        help="Max allowed age in hours before flagging as stale",
    )
    args = parser.parse_args()

    # Grab the database URL directly from the environment
    db_url = os.getenv("DATABASE_URL")

    # Fail gracefully if no database URL is found in the environment or .env file
    if not db_url:
        print(
            "Error: No DATABASE_URL found. Please set it in your .env file or environment variables."
        )
        sys.exit(1)

    # Dynamically create the engine and session
    if db_url.startswith("sqlite"):
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(db_url)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        rows = (
            session.query(DatasetFreshness).order_by(DatasetFreshness.dataset_id).all()
        )
    finally:
        session.close()

    if not rows:
        print("No freshness records yet — run the ingestion pipeline at least once.")
        sys.exit(0)

    # FIXED: Use timezone-aware UTC now, then make it naive for DB comparison
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        hours=args.max_age_hours
    )
    any_stale = False

    print(
        f"{'dataset_id':<20}{'status':<10}{'last_ingested_at (UTC)':<25}{'records':<10}flag"
    )
    print("-" * 80)

    for row in rows:
        is_stale = row.last_ingested_at < cutoff
        is_failed = row.last_status != "success"
        flag = ""
        if is_failed:
            flag = "FAILED"
            any_stale = True
        elif is_stale:
            flag = "STALE"
            any_stale = True

        print(
            f"{row.dataset_id:<20}{row.last_status:<10}"
            f"{row.last_ingested_at.isoformat():<25}"
            f"{str(row.records_processed):<10}{flag}"
        )
        if row.last_error:
            print(f"    error: {row.last_error}")

    sys.exit(1 if any_stale else 0)


if __name__ == "__main__":
    main()
