import argparse
import json
from pathlib import Path
from datetime import datetime

import requests

ROOT = Path(__file__).resolve().parents[1]

CONFIG = ROOT / "config" / "datasets_unstr.json"

RAW_DIR = ROOT / "data" / "raw_unstr_documents"


def load_datasets():

    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)["datasets"]


def fetch_document(dataset):

    print("=" * 80)
    print(dataset["name"])
    print("=" * 80)

    response = requests.get(
        dataset["url"],
        timeout=30,
    )

    response.raise_for_status()

    dataset_dir = RAW_DIR / dataset["id"]

    dataset_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    extension = "html"

    if dataset["type"] == "pdf":
        extension = "pdf"

    filename = f"{timestamp}.{extension}"

    with open(
        dataset_dir / filename,
        "wb",
    ) as f:

        f.write(response.content)

    print(f"Saved -> {dataset_dir / filename}")


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        default=None,
    )

    args = parser.parse_args()

    datasets = load_datasets()

    if args.dataset:

        datasets = [d for d in datasets if d["id"] == args.dataset]

    for dataset in datasets:

        fetch_document(dataset)


if __name__ == "__main__":
    main()
