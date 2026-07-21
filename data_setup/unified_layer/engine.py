import json
from pathlib import Path
from data_setup.unified_layer.database import SessionLocal, init_db
from data_setup.unified_layer.transformers import TRANSFORMER_REGISTRY
from data_setup.unified_layer.freshness import record_freshness

# Define absolute paths based on the project structure
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_SETUP_ROOT = PROJECT_ROOT / "data_setup"
CONFIG_DIR = DATA_SETUP_ROOT / "config"


class UnifiedEngine:
    """Core orchestrator that moves raw Bronze data into the Silver unified database layer."""

    def __init__(self):
        # Automatically generate the unified_events and unified_knowledge tables
        init_db()

    def process_dataset(self, dataset_id: str, provider: str, raw_dir_path: Path):
        """Looks up the correct transformer and processes all files in a directory."""
        transformer_cls = TRANSFORMER_REGISTRY.get(dataset_id)
        if not transformer_cls:
            print(f"[-] No transformer registered for dataset: {dataset_id}")
            return

        transformer = transformer_cls()
        session = SessionLocal()
        total_records = 0  ##new

        try:
            # Recursively find all files in the specific dataset directory
            files = [f for f in raw_dir_path.rglob("*") if f.is_file()]
            if not files:
                print(f"[-] No raw files found in: {raw_dir_path}")
                record_freshness(
                    dataset_id, provider, "failed", error="No raw files found"
                )  ##recording freshness
                return

            for file_path in files:
                print(f"[+] Processing raw file: {file_path.name}")

                try:
                    # Execute the transformer's interface contract
                    records = transformer.transform(file_path)

                    # Merge handles upserts gracefully (prevents duplicate ID crashes)
                    for record in records:
                        session.merge(record)
                        total_records += 1

                except Exception as e:
                    print(f"  [-] Failed to process {file_path.name}: {e}")

            # Commit the entire batch transaction to the database
            session.commit()
            print(f"[✓] Successfully unified dataset: {dataset_id}")
            record_freshness(
                dataset_id, provider, "success", records_processed=total_records
            )

        except Exception as e:
            session.rollback()
            print(f"[-] Database transaction error for {dataset_id}: {e}")
            record_freshness(dataset_id, provider, "failed", error=str(e))
        finally:
            session.close()

    def run_pipeline(self):
        """Scans the JSON configs and triggers processing for all available datasets."""
        print("=" * 60)
        print("Starting Unified Layer Processing Pipeline")
        print("=" * 60)

        # 1. Process Structured Data
        print("\n>>> Processing Structured Datasets (Bronze -> Silver)")
        str_config = CONFIG_DIR / "datasets_str.json"

        if str_config.exists():
            with open(str_config, "r", encoding="utf-8") as f:
                datasets = json.load(f).get("datasets", [])
                for ds in datasets:
                    ds_id = ds["id"]
                    provider = ds["provider"]
                    raw_dir = DATA_SETUP_ROOT / "data_str" / provider / ds_id

                    if raw_dir.exists():
                        self.process_dataset(ds_id, provider, raw_dir)
                    else:
                        print(f"[-] Directory not found: {raw_dir}")

        # 2. Process Unstructured Data
        print("\n>>> Processing Unstructured Datasets (Bronze -> Silver)")
        unstr_config = CONFIG_DIR / "datasets_unstr.json"

        if unstr_config.exists():
            with open(unstr_config, "r", encoding="utf-8") as f:
                datasets = json.load(f).get("datasets", [])
                for ds in datasets:
                    ds_id = ds["id"]
                    provider = ds["provider"]
                    raw_dir = DATA_SETUP_ROOT / "data_unstr" / provider / ds_id

                    if raw_dir.exists():
                        self.process_dataset(ds_id, provider, raw_dir)
                    else:
                        print(f"[-] Directory not found: {raw_dir}")


if __name__ == "__main__":
    engine = UnifiedEngine()
    engine.run_pipeline()
