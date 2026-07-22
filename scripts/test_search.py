"""
Standalone debug script for the web search fallback tool.
Run with: poetry run python scripts/test_web_search_tool.py

This avoids PowerShell's unreliable multi-line `python -c "..."` quoting,
and explicitly loads .env (web_search_tools.py itself does NOT call
load_dotenv() — it just reads os.environ, so whatever process runs it
needs to have already loaded the .env file, same as test_search.py does).
"""

import os
import sys
import traceback

from dotenv import load_dotenv

load_dotenv()

print(
    "SERPAPI_KEY loaded:",
    "yes" if os.getenv("SERPAPI_KEY") else "NO (missing from .env or env)",
)
print("Python:", sys.version)
print("CWD:", os.getcwd())
print("-" * 60)

try:
    from agent.app.core.tools.web_search_tools import web_search_fallback

    print("Import OK. Tool name:", web_search_fallback.name)

    content, artifact = web_search_fallback.func("Python programming tutorials")
    print("-" * 60)
    print("CONTENT:\n", content)
    print("-" * 60)
    print("ARTIFACT:\n", artifact)

except Exception:
    print("FAILED — full traceback below:")
    traceback.print_exc()
