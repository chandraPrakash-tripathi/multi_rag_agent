import argparse
import json
from datetime import datetime
from pathlib import Path

import requests

from scripts.settings import get_settings

settings = get_settings()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_SETUP_ROOT = PROJECT_ROOT / "data_setup"

DATASET_CONFIG = DATA_SETUP_ROOT / "config" / "datasets_str.json"

RAW_DATA_DIR = DATA_SETUP_ROOT / "data_str"


def load_datasets():

    with open(
        DATASET_CONFIG,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)["datasets"]


def save_raw_json(
    dataset: dict,
    data: dict | list,
):

    provider = dataset["provider"]
    dataset_id = dataset["id"]

    save_dir = RAW_DATA_DIR / provider / dataset_id

    save_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = datetime.now().strftime("%Y%m%d_%H%M%S.json")

    filepath = save_dir / filename

    with open(
        filepath,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False,
        )

    print(f"Saved Raw JSON -> {filepath}")


def fetch_dataset(dataset: dict):

    print("=" * 80)
    print(f"Dataset : {dataset['name']}")
    print("=" * 80)

    params = {}

    if dataset.get("api_key", False):

        params["api_key"] = settings.NASA_API_KEY

    params.update(dataset.get("params", {}))

    print("URL :", dataset["url"])
    print("Params :", params)

    try:

        response = requests.get(
            dataset["url"],
            params=params,
            timeout=30,
        )

        print(f"HTTP Status : {response.status_code}")

        response.raise_for_status()

        data = response.json()

        print("✓ Success")

        save_raw_json(
            dataset,
            data,
        )

        if isinstance(data, dict):

            print("Top Level Keys")

            print(list(data.keys()))

        elif isinstance(data, list):

            print(f"Returned {len(data)} items")

    except Exception as e:

        print(f"ERROR : {e}")

        if "response" in locals():

            print(response.text)


def main():

    parser = argparse.ArgumentParser(description="Fetch Structured Data")

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

        fetch_dataset(dataset)


if __name__ == "__main__":
    main()
