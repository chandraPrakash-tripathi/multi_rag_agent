# What this accomplishes:
# A single, tiny choke point for writing "when did this dataset last run,
# and did it succeed?" — called from UnifiedEngine after every dataset is
# processed (success or failure). Kept separate from engine.py so it can
# also be called directly from the vector-layer step, or from a future
# monitoring/alerting script, without importing the whole engine.
from datetime import datetime

from data_setup.unified_layer.database import SessionLocal
from data_setup.unified_layer.models import DatasetFreshness


def record_freshness(
    dataset_id: str,
    source_provider: str,
    status: str,  # "success" | "failed"
    records_processed: int | None = None,
    error: str | None = None,
) -> None:
    """Upserts the freshness row for a dataset_id. Never raises — a failure
    here should never take down the ingestion run itself."""

    session = SessionLocal()
    try:
        row = DatasetFreshness(
            dataset_id=dataset_id,
            source_provider=source_provider,
            last_ingested_at=datetime.utcnow(),
            last_status=status,
            records_processed=records_processed,
            last_error=error,
        )
        session.merge(row)
        session.commit()
    except Exception as e:
        # Freshness tracking is observability, not the critical path.
        print(f"[-] Failed to record freshness for {dataset_id}: {e}")
        session.rollback()
    finally:
        session.close()
