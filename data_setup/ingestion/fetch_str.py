# data_setup/fetch.py

import argparse
import json
from pathlib import Path

import requests

from ...scripts.settings import get_settings

settings = get_settings()

ROOT = Path(__file__).resolve().parents[1]
DATASET_CONFIG = ROOT / "data_setup" / "config" / "datasets_str.json"


def load_datasets():
    with open(DATASET_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)["datasets"]


def fetch_dataset(dataset: dict):

    print("=" * 80)
    print(f"Dataset : {dataset['name']}")
    print("=" * 80)

    params = {}

    # Add API Key if required
    if dataset.get("api_key", False):
        params["api_key"] = settings.NASA_API_KEY

    # Merge dataset specific default parameters
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

        if isinstance(data, dict):
            print("Top Level Keys")
            print(list(data.keys()))

        elif isinstance(data, list):
            print(f"Returned {len(data)} items")

        # ---------------------------------------------------
        # TODO
        #
        # Save Raw JSON
        # Normalize
        # Save PostgreSQL
        # Save Qdrant
        #
        # ---------------------------------------------------

    except Exception as e:

        print(f"ERROR : {e}")

        if "response" in locals():
            print(response.text)


def main():

    parser = argparse.ArgumentParser(description="Fetch NASA datasets.")

    parser.add_argument(
        "--dataset",
        help="Dataset ID from datasets.json",
        default=None,
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
