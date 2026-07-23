"""
Semantic cache for full query -> final_answer pairs.

Sits in front of the whole graph (wired into backend/main.py's /query
endpoint), not inside any single agent/tool. This is deliberate: the goal
is to skip an ENTIRE supervisor run — every agent it would have invoked,
every LLM call, every knowledge_agent lookup — when the incoming query is
a near-duplicate of a recent one. Caching inside one tool (e.g.
search_scientific_knowledge) would only save that one lookup; caching here
saves the whole cycle, which is the actual "biggest win" the phase-2
notes call out.

Backed by Upstash Redis (free tier, REST API — no persistent TCP socket,
which fits an async FastAPI process cleanly). All cache entries + their
embeddings are stored as ONE JSON blob under a single key, not one Redis
key per entry. This is intentional: with up to ~200 cached entries, doing
a similarity scan means 200 individual GETs per cache lookup over Upstash's
REST API, which would blow the ~50ms latency target on its own. One GET
+ an in-process numpy scan is one network round-trip.

Reuses the same all-MiniLM-L6-v2 model already loaded for the Qdrant
vector layer (see data_setup/vector_layer/builder.py) — same embedding
space, no second model to download/maintain.

Known limitations (this is the "started" pass, not the final version):
- No true concurrency control on the read-modify-write in `set()` — under
  concurrent requests, the last writer wins and a cache entry from another
  in-flight request could be dropped on trim. Fine at this traffic scale;
  worth a Redis transaction (or Upstash's optimistic locking) later.
- Embedding + Redis round-trip realistically lands in the tens of ms, not
  a hard <50ms guarantee — that number depends on Upstash region latency
  and whether the embedding model is warm. Log actual timings before
  treating 50ms as a promise anywhere user-facing.
"""

import os
import json
import time
import hashlib
import logging
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from upstash_redis.asyncio import Redis

logger = logging.getLogger(__name__)

STORE_KEY = "semcache:store"


class SemanticCache:
    def __init__(
        self,
        similarity_threshold: float = 0.92,
        max_cached: int = 200,
        ttl_seconds: int = 3600,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_cached = max_cached
        self.ttl_seconds = ttl_seconds

        url = os.getenv("UPSTASH_REDIS_URL")
        token = os.getenv("UPSTASH_REDIS_TOKEN")
        self.enabled = bool(url and token)

        if not self.enabled:
            logger.warning(
                "Semantic cache disabled — UPSTASH_REDIS_URL/UPSTASH_REDIS_TOKEN not set."
            )
            self.redis = None
            self.model = None
            return

        self.redis = Redis(url=url, token=token)
        # Same model already used by the vector layer — see module docstring.
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    async def _load_store(self) -> list[dict]:
        raw = await self.redis.get(STORE_KEY)
        if not raw:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Semantic cache store was corrupt — resetting.")
            return []

    async def get(self, query: str) -> Optional[dict]:
        """Returns the cached entry if a near-duplicate query is found above
        the similarity threshold, else None. Never raises — a cache failure
        should never block a real query from reaching the graph."""
        if not self.enabled:
            return None

        try:
            start = time.monotonic()
            store = await self._load_store()
            if not store:
                return None

            now = time.time()
            live_entries = [e for e in store if now - e.get("ts", 0) < self.ttl_seconds]

            query_vec = self.model.encode(query, normalize_embeddings=True)

            best_score = -1.0
            best_entry = None
            for entry in live_entries:
                cached_vec = np.array(entry["embedding"], dtype=np.float32)
                score = float(np.dot(query_vec, cached_vec))  # both normalized -> cosine sim
                if score > best_score:
                    best_score = score
                    best_entry = entry

            elapsed_ms = (time.monotonic() - start) * 1000
            if best_entry and best_score >= self.similarity_threshold:
                logger.info(
                    "Semantic cache HIT (similarity=%.3f, %.1fms) for: %s",
                    best_score, elapsed_ms, query[:80],
                )
                return {
                    "final_answer": best_entry["final_answer"],
                    "similarity": best_score,
                    "matched_query": best_entry["query"],
                }

            logger.info(
                "Semantic cache MISS (best_score=%.3f, %.1fms) for: %s",
                best_score, elapsed_ms, query[:80],
            )
            return None

        except Exception as exc:
            logger.warning("Semantic cache get() failed, treating as miss: %s", exc)
            return None

    async def set(self, query: str, final_answer: str) -> None:
        """Best-effort write. A failure here should never surface to the
        caller — the graph already ran and produced a real answer."""
        if not self.enabled or not final_answer:
            return

        try:
            query_vec = self.model.encode(query, normalize_embeddings=True).tolist()
            entry_id = hashlib.sha1(query.encode()).hexdigest()[:16]

            store = await self._load_store()
            # Drop any existing entry for this exact query (dedupe), then
            # push the new one to the front and trim to max_cached.
            store = [e for e in store if e.get("id") != entry_id]
            store.insert(
                0,
                {
                    "id": entry_id,
                    "query": query,
                    "final_answer": final_answer,
                    "embedding": query_vec,
                    "ts": time.time(),
                },
            )
            store = store[: self.max_cached]

            await self.redis.set(STORE_KEY, json.dumps(store), ex=self.ttl_seconds)

        except Exception as exc:
            logger.warning("Semantic cache set() failed (non-fatal): %s", exc)
