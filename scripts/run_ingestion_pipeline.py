"""
Single entrypoint for scheduled ingestion runs (called from GitHub Actions,
or manually for local testing).

    python -m scripts.run_ingestion_pipeline --stage structured
    python -m scripts.run_ingestion_pipeline --stage unstructured
    python -m scripts.run_ingestion_pipeline --stage all

--stage structured   : fetch_str   -> unify (writes unified_events)
--stage unstructured : fetch_unstr -> unify (writes unified_knowledge)
                                    -> vectorize (embeds + upserts to Qdrant)
--stage all          : both, in sequence (handy for local backfills)

Fetch scripts are invoked as subprocesses (they own argparse/sys.argv), the
unify + vectorize steps are invoked as plain class calls (idempotent merge /
upsert, safe to call even if the other stage hasn't run yet).
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_fetch(module: str):
    print(f"\n{'=' * 60}\nRunning {module}\n{'=' * 60}")
    result = subprocess.run(
        [sys.executable, "-m", module],
        cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        # Don't kill the whole run over one flaky upstream API — the
        # freshness table will surface the miss instead of a red CI run
        # hiding a partial success.
        print(f"[-] {module} exited with code {result.returncode} (continuing)")


def run_unify():
    from data_setup.unified_layer.engine import UnifiedEngine

    UnifiedEngine().run_pipeline()


def run_vectorize():
    from data_setup.vector_layer.builder import VectorKnowledgeBuilder

    VectorKnowledgeBuilder().run_pipeline()


def main():
    parser = argparse.ArgumentParser(description="Run the scheduled ingestion pipeline")
    parser.add_argument(
        "--stage",
        choices=["structured", "unstructured", "all"],
        required=True,
    )
    args = parser.parse_args()

    if args.stage in ("structured", "all"):
        run_fetch("data_setup.ingestion.fetch_str")
        run_unify()

    if args.stage in ("unstructured", "all"):
        run_fetch("data_setup.ingestion.fetch_unstr")
        run_unify()
        run_vectorize()

    print("\n[✓] Pipeline run complete.")


if __name__ == "__main__":
    main()
