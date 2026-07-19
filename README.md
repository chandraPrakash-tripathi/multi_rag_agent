# 🛰️ Space Intelligence Platform — Multi-Agent RAG System

A production-style **multi-agent RAG platform** built on **LangGraph** that continuously ingests live NASA data, retrieves scientific knowledge, performs analytics, and generates grounded intelligence reports on demand — all through a supervised, self-routing agent graph.

This isn't a single chatbot wrapper around an LLM. It's a full pipeline: raw data ingestion → structured/unstructured unification → vector embedding → a multi-agent LangGraph orchestration layer → a FastAPI backend → a Next.js frontend.

---

## What it does

Ask it things like:

- *"Are there any hazardous asteroids approaching this week?"*
- *"Any solar storms or geomagnetic activity today?"*
- *"Show me active wildfires right now."*
- *"Explain today's Astronomy Picture of the Day."*
- *"What's the latest space news?"*
- *"Explain how black holes form."* *(answered via RAG over NASA documentation)*

A **supervisor agent** reads the query, decides which specialist agent(s) are relevant, runs them (in parallel where possible), and loops until it has enough information — then a **report agent** synthesizes everything into one clean markdown answer, and hands back a full trace of which agents ran and why.

---

## Architecture

```
                          User Query
                              │
                        FastAPI Backend
                              │
                      LangGraph Supervisor
                              │
        ┌──────────┬──────────┼──────────┬──────────┬──────────┐
        ▼          ▼          ▼          ▼          ▼          ▼
   NEO Agent   Weather    Earth Events  APOD Agent  News Agent  Knowledge
  (asteroids)   Agent      Agent                                Agent (RAG)
        │          │          │           │           │           │
        └──────────┴──────────┴─────┬─────┴──────────-┴───────────┘
                                     ▼
                            Analytics Agent
                                     │
                              Report Agent
                                     │
                              Final Answer
```

**Data layer (built offline, ahead of time):**

```
NASA / Spaceflight APIs  →  Bronze (raw JSON/HTML on disk)
                          →  Silver (unified SQL: PostgreSQL/SQLite)
                          →  Vector layer (Qdrant embeddings)
```

Structured data (asteroids, space weather, earth events) lives in a SQL database for fast filtering and analytics. Unstructured knowledge (NASA docs, mission pages, APOD explanations, news articles) is chunked and embedded into Qdrant for semantic retrieval.

---

## Agents

| Agent | Capability | Data Source |
|---|---|---|
| **NEO Agent** | Hazardous asteroid monitoring, closest approaches, speed/size analysis | NASA NeoWs |
| **Weather Agent** | Solar flares, CMEs, geomagnetic storms | NASA DONKI |
| **Earth Events Agent** | Active wildfires, volcanoes, floods, storms | NASA EONET |
| **APOD Agent** | Explains NASA's Astronomy Picture of the Day | NASA APOD |
| **News Agent** | Latest launches, discoveries, mission updates | Spaceflight News API |
| **Knowledge Agent (RAG)** | Answers conceptual science questions via semantic search | NASA mission docs / educational pages |
| **Analytics Agent** | Trends, statistics, and chart configs from already-gathered data | — |
| **Report Agent** | Synthesizes everything into one final markdown report | — |

A supervisor node routes to these agents dynamically per query, based on an LLM decision — no hardcoded if/else routing.

---

## Tech Stack

- **Orchestration:** [LangGraph](https://github.com/langchain-ai/langgraph) — stateful multi-agent graph with checkpointing
- **LLMs:** Groq (production) or Ollama (local), swappable via env var
- **Structured storage:** SQLAlchemy + SQLite (local) / PostgreSQL (production)
- **Vector storage:** [Qdrant](https://qdrant.tech/)
- **Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`)
- **Backend:** FastAPI + Uvicorn, with rate limiting (`slowapi`)
- **Frontend:** Next.js (App Router) + Tailwind + shadcn/ui
- **Package management:** Poetry

---

## Project Structure

```
├── data_setup/
│   ├── config/                # Declarative dataset definitions (structured + unstructured)
│   ├── ingestion/              # Pulls raw data from NASA/Spaceflight APIs → Bronze layer
│   ├── unified_layer/          # Transforms Bronze → clean SQL tables (Silver layer)
│   │   ├── models.py           # SQLAlchemy schema: UnifiedEvent, UnifiedKnowledge
│   │   ├── engine.py           # Orchestrates the transform pipeline
│   │   └── transformers/       # One transformer per data source
│   └── vector_layer/           # Chunks + embeds Silver-layer text into Qdrant
│
├── agent/app/
│   ├── core/
│   │   ├── repository/         # Only layer that talks to SQL/Qdrant directly
│   │   ├── tools/               # LangChain tools wrapping each repository
│   │   ├── assistant/           # Shared LLM wrapper (env-aware: Groq/Ollama)
│   │   ├── agents/               # Agent node implementations (analytics, auditor, report)
│   │   └── graph/                # GraphState schema, supervisor, graph builder
│   └── main.py                  # FastAPI app (`/query`, `/health`)
│
├── frontend/                    # Next.js chat UI
├── scripts/                     # Settings + manual smoke-test scripts
└── docs/doc.md                  # Original design document
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- [Poetry](https://python-poetry.org/)
- A running [Qdrant](https://qdrant.tech/) instance (Docker: `docker run -p 6333:6333 qdrant/qdrant`)
- A NASA API key ([get one free here](https://api.nasa.gov/))
- Either a local [Ollama](https://ollama.com/) install, or a [Groq](https://groq.com/) API key

### 1. Install dependencies

```bash
poetry install
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
NASA_API_KEY=your_nasa_api_key

# LLM environment: "local" (Ollama) or "prod" (Groq)
ENVIRONMENT=local
LOCAL_MODEL=qwen2.5:7b
# GROQ_API_KEY=your_groq_key        # required if ENVIRONMENT=prod
# PROD_MODEL=openai/gpt-oss-120b    # optional override

# Storage
DATABASE_URL=sqlite:///unified_layer.db
QDRANT_URL=http://localhost:6333

# API security (optional — leave unset to disable auth locally)
# API_KEY=your_backend_api_key
```

### 3. Run the data pipeline (in order)

```bash
# Step 1 — pull raw data from NASA / Spaceflight APIs
poetry run python -m data_setup.ingestion.fetch_str
poetry run python -m data_setup.ingestion.fetch_unstr

# Step 2 — transform raw data into the unified SQL layer
poetry run python -m data_setup.unified_layer.engine

# Step 3 — chunk + embed knowledge into Qdrant
poetry run python -m data_setup.vector_layer.builder
```

### 4. Run the backend

```bash
poetry run uvicorn agent.app.main:app --reload
```

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` (and `NEXT_PUBLIC_API_KEY` if `API_KEY` is set on the backend) in `frontend/.env.local`.

---

## API

**`POST /query`**

```json
{
  "query": "Are there any hazardous asteroids approaching this week?",
  "thread_id": "optional — reuse to continue a conversation"
}
```

Response:

```json
{
  "thread_id": "session_...",
  "final_answer": "markdown report",
  "report": "markdown report",
  "errors": [],
  "completed_agents": ["neo_agent"],
  "execution_logs": ["Supervisor cycle 0: 'neo_agent'"]
}
```

**`GET /health`** — liveness check.

---

## Design Notes

- **GraphState** is working memory for a single request only — never a persistence layer. Structured/unstructured data lives in SQL and Qdrant; GraphState just tracks what the current run has gathered.
- Every agent returns control to the **supervisor**, which decides the next step using an LLM-driven routing decision (not hardcoded logic) — bounded by a max-cycle safety valve so it can't loop forever.
- Repositories are the **only** layer allowed to touch a database session directly — tools and agents only ever see plain dicts.
- Conversations persist across turns via a SQLite checkpointer keyed by `thread_id`.

---

## Roadmap / Known Limitations

- Data pipeline runs (ingestion → unification → vectorization) are manual/scheduled, not incremental — full re-embeds happen each run.
- Analytics currently covers asteroids and earth events; more domains can be added following the same pattern.
- Frontend does not yet render the analytics agent's chart output.

---

## License

Add your preferred license here (e.g. MIT).