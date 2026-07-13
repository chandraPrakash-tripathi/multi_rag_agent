import argparse
import json
from pathlib import Path
from datetime import datetime

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_SETUP_ROOT = PROJECT_ROOT / "data_setup"

CONFIG = DATA_SETUP_ROOT / "config" / "datasets_unstr.json"

RAW_DATA_DIR = DATA_SETUP_ROOT / "data_unstr"


def load_datasets():

    with open(
        CONFIG,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)["datasets"]


def save_document(
    dataset: dict,
    response: requests.Response,
):

    provider = dataset["provider"]
    dataset_id = dataset["id"]

    save_dir = RAW_DATA_DIR / provider / dataset_id

    save_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    extension = dataset["type"]

    filename = f"{timestamp}.{extension}"

    filepath = save_dir / filename

    with open(
        filepath,
        "wb",
    ) as f:

        f.write(response.content)

    print(f"Saved -> {filepath}")


def fetch_document(dataset):

    print("=" * 80)
    print(f"Dataset : {dataset['name']}")
    print("=" * 80)

    print("URL :", dataset["url"])

    try:

        response = requests.get(
            dataset["url"],
            timeout=30,
        )

        print(f"HTTP Status : {response.status_code}")

        response.raise_for_status()

        print("✓ Success")

        save_document(
            dataset,
            response,
        )

    except Exception as e:

        print(f"ERROR : {e}")

        if "response" in locals():

            print(response.text)


def main():

    parser = argparse.ArgumentParser(description="Fetch Knowledge Sources")

    parser.add_argument(
        "--dataset",
        default=None,
        help="Dataset ID",
    )

    args = parser.parse_args()

    datasets = load_datasets()

    if args.dataset:

        datasets = [d for d in datasets if d["id"] == args.dataset]

        if not datasets:

            raise ValueError(f"Dataset '{args.dataset}' not found.")

    print(f"\nFound {len(datasets)} dataset(s).\n")

    for dataset in datasets:

        fetch_document(dataset)


if __name__ == "__main__":
    main()
