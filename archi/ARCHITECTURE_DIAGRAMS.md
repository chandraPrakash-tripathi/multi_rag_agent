# Architecture Diagrams — Space Intelligence Platform

This document contains a high-level system diagram, followed by four detailed
low-level diagrams that map every file in the repo to the phase it belongs
to and what it connects to. All diagrams are Mermaid — they render natively
on GitHub, and in any Mermaid-aware viewer.

---

## 1. High-Level Diagram — the 5 macro phases

Phases A–C run offline/on a schedule to prepare data. Phase D runs live on
every user query. Phase E is what exposes it to a human.

```mermaid
flowchart TD
    NASA["NASA APIs<br/>NeoWs · DONKI · EONET · APOD"]
    SFN["Spaceflight News API"]
    DOCS["NASA HTML pages<br/>JWST · Artemis · Hubble · Mars · Earth Obs"]

    subgraph PHASE_A["PHASE A — Ingestion (Bronze layer)"]
        BRONZE["Raw JSON / HTML saved to disk<br/>data_setup/data_str, data_unstr"]
    end

    subgraph PHASE_B["PHASE B — Unification (Silver layer)"]
        SILVER["unified_events + unified_knowledge<br/>SQLite / PostgreSQL"]
    end

    subgraph PHASE_C["PHASE C — Vectorization"]
        VECTOR["Chunked + embedded knowledge<br/>Qdrant vector DB"]
    end

    subgraph PHASE_D["PHASE D — Agent runtime (LangGraph, per query)"]
        SUPERVISOR["Supervisor<br/>decides which agents run"]
        SPECIALISTS["Specialist agents<br/>NEO · Weather · Earth · APOD · News · Knowledge"]
        ANALYTICS["Analytics agent"]
        REPORT["Report agent<br/>final synthesis"]
    end

    subgraph PHASE_E["PHASE E — Serving"]
        API["FastAPI backend<br/>/query endpoint"]
        UI["Next.js frontend"]
    end

    NASA --> BRONZE
    SFN --> BRONZE
    DOCS --> BRONZE
    BRONZE --> SILVER
    SILVER --> VECTOR

    UI --> API --> SUPERVISOR
    SUPERVISOR --> SPECIALISTS
    SPECIALISTS --> SUPERVISOR
    SPECIALISTS -. reads .-> SILVER
    SPECIALISTS -. reads .-> VECTOR
    SUPERVISOR --> ANALYTICS --> SUPERVISOR
    SUPERVISOR --> REPORT --> API --> UI
```

---

## 2. Low-Level Diagram — Data Pipeline (Ingestion → Silver → Vector)

Every box here is one real file in the repo. Arrows show which file feeds
which, in the exact order you'd run them.

```mermaid
flowchart TD
    subgraph CONFIG["data_setup/config"]
        C1["datasets_str.json<br/>neows, donki, eonet, apod, spaceflight_news"]
        C2["datasets_unstr.json<br/>jwst, artemis, hubble, mars, earth_observatory"]
    end

    subgraph INGEST["data_setup/ingestion — Bronze layer"]
        SETTINGS["scripts/settings.py<br/>loads NASA_API_KEY from .env"]
        FS["fetch_str.py<br/>GET each JSON API, save timestamped raw file"]
        FU["fetch_unstr.py<br/>GET each HTML page, save timestamped raw file"]
        BRONZE_STR[["data_setup/data_str/&#123;provider&#125;/&#123;dataset_id&#125;/*.json"]]
        BRONZE_HTML[["data_setup/data_unstr/&#123;provider&#125;/&#123;dataset_id&#125;/*.html"]]
    end

    subgraph UNIFIED["data_setup/unified_layer — Silver layer"]
        MODELS["models.py<br/>UnifiedEvent + UnifiedKnowledge (SQLAlchemy)"]
        DATABASE["database.py<br/>engine + SessionLocal + init_db()"]
        BASE_T["transformers/base.py<br/>BaseTransformer interface"]
        T_NEOWS["transformers/neows.py"]
        T_DONKI["transformers/donki.py"]
        T_EONET["transformers/eonet.py"]
        T_APOD["transformers/apod.py"]
        T_SFN["transformers/spaceflight.py"]
        T_HTML["transformers/html_docs.py"]
        REGISTRY["transformers/__init__.py<br/>TRANSFORMER_REGISTRY"]
        ENGINE["engine.py<br/>UnifiedEngine.run_pipeline()"]
        DB[("unified_layer.db<br/>unified_events / unified_knowledge")]
    end

    subgraph VECTORL["data_setup/vector_layer"]
        BUILDER["builder.py<br/>VectorKnowledgeBuilder"]
        QDRANT[("Qdrant<br/>unified_knowledge_collection")]
    end

    C1 --> FS
    C2 --> FU
    SETTINGS --> FS
    FS --> BRONZE_STR
    FU --> BRONZE_HTML

    BASE_T --> T_NEOWS & T_DONKI & T_EONET & T_APOD & T_SFN & T_HTML
    T_NEOWS & T_DONKI & T_EONET & T_APOD & T_SFN & T_HTML --> REGISTRY
    MODELS --> DATABASE
    DATABASE --> ENGINE
    REGISTRY --> ENGINE
    BRONZE_STR --> ENGINE
    BRONZE_HTML --> ENGINE
    ENGINE -->|"session.merge() per record"| DB

    DB -->|"fetch_knowledge_documents()"| BUILDER
    BUILDER -->|"chunk + embed<br/>all-MiniLM-L6-v2"| QDRANT
```

**How to read this:** `datasets_str.json` / `datasets_unstr.json` declare
*what* to pull. `fetch_str.py` / `fetch_unstr.py` pull it onto disk
(Bronze). `engine.py` picks the right transformer per `dataset_id` (via the
`TRANSFORMER_REGISTRY`), converts raw files into `UnifiedEvent` /
`UnifiedKnowledge` rows, and merges them into `unified_layer.db` (Silver).
`builder.py` then reads every `UnifiedKnowledge` row, chunks it, embeds it,
and upserts it into Qdrant.

---

## 3. Low-Level Diagram — Agent Core (Repositories → Tools → Graph)

```mermaid
flowchart TD
    DB[("unified_layer.db")]
    QDRANT[("Qdrant")]

    subgraph REPO["agent/app/core/repository"]
        BASE_R["base.py<br/>BaseRepository — session mgmt, dict conversion"]
        R_AST["asteroid_repository.py"]
        R_WEA["weather_repository.py"]
        R_EAR["earth_repository.py"]
        R_APO["apod_repository.py"]
        R_NEW["news_repository.py"]
        R_KNO["knowledge_repository.py<br/>Qdrant search, no SQL session"]
    end

    subgraph TOOLS["agent/app/core/tools"]
        TL_AST["asteroid_tools.py"]
        TL_WEA["weather_tools.py"]
        TL_EAR["earth_tools.py"]
        TL_APO["apod_tools.py"]
        TL_NEW["news_tools.py"]
        TL_KNO["knowledge_tools.py"]
    end

    subgraph ASSIST["agent/app/core/assistant"]
        ASSISTANT["assistant.py<br/>AssistantBase — Ollama/Groq switch"]
    end

    subgraph GRAPH["agent/app/core/graph + agents"]
        STATE["graph_state.py<br/>GraphState (7 layers)"]
        FACTORY["agent_node_factory.py<br/>make_agent_node()"]
        SUPERVISOR["supervisor.py<br/>routes to agents, loops until DONE"]
        ANALYTICS["analytics_agent.py<br/>pure-python stats, no LLM"]
        AUDITOR["auditor_agent.py<br/>error retry gate"]
        REPORT["report_agent.py<br/>final markdown synthesis"]
        BUILDER["graph_builder.py<br/>build_graph() — wires every node"]
    end

    DB --> BASE_R
    BASE_R --> R_AST & R_WEA & R_EAR & R_APO & R_NEW
    QDRANT --> R_KNO

    R_AST --> TL_AST
    R_WEA --> TL_WEA
    R_EAR --> TL_EAR
    R_APO --> TL_APO
    R_NEW --> TL_NEW
    R_KNO --> TL_NEW
    R_KNO --> TL_KNO

    ASSISTANT --> FACTORY
    TL_AST & TL_WEA & TL_EAR & TL_APO & TL_NEW & TL_KNO --> FACTORY
    STATE --> FACTORY
    STATE --> SUPERVISOR
    STATE --> ANALYTICS
    STATE --> AUDITOR
    STATE --> REPORT

    FACTORY --> BUILDER
    SUPERVISOR --> BUILDER
    ANALYTICS --> BUILDER
    AUDITOR --> BUILDER
    REPORT --> BUILDER
    ASSISTANT --> SUPERVISOR
    ASSISTANT --> REPORT
```

**How to read this:** Repositories are the only files allowed to open a DB
session or query Qdrant. Tools wrap repositories in LangChain's `@tool`
decorator so an LLM can call them. `agent_node_factory.py` wraps a tool set
+ an `AssistantBase` instance into a runnable LangGraph node. `graph_builder.py`
is the file that actually registers every node and compiles the graph —
nothing here runs until that file's `build_graph()` is called.

> Note: `auditor_agent.py` is registered as a node but is not currently
> reached by `supervisor.py`'s routing logic — see the "Known Gaps" section
> of `SYSTEM_DOCUMENTATION.txt` for details.

---

## 4. Low-Level Diagram — Runtime Sequence (one user query, step by step)

```mermaid
sequenceDiagram
    participant UI as Next.js UI
    participant API as FastAPI /query
    participant G as Compiled LangGraph
    participant SUP as supervisor.py
    participant AG as Specialist agent(s)
    participant TOOL as Tool + Repository
    participant ANA as analytics_agent.py
    participant REP as report_agent.py

    UI->>API: POST /query {query, thread_id}
    API->>G: graph.invoke(state, config)
    G->>SUP: START -> supervisor_node(state)
    SUP->>SUP: build_context() from completed_agents
    SUP->>SUP: LLM decides next agent(s) or DONE

    alt agents selected
        SUP->>AG: Command(goto=[agents], cycle_count+1)
        AG->>TOOL: assistant tool-calling loop (max 4 iters)
        TOOL-->>AG: content + artifact
        AG->>SUP: Command(goto="supervisor", update=domain_data)
        SUP->>SUP: loop again (up to MAX_CYCLES=3)
    end

    opt user asked for trends/stats
        SUP->>ANA: Command(goto="analytics_agent")
        ANA->>SUP: Command(goto="supervisor", update=analytics+charts)
    end

    SUP->>REP: decision=="DONE" -> Command(goto="report_agent")
    REP->>REP: LLM synthesizes final markdown from full state
    REP->>G: Command(goto=END, update=final_answer+report)
    G->>API: result dict
    API->>UI: QueryResponse (final_answer, report, errors, completed_agents, execution_logs)
```

---

## 5. Low-Level Diagram — Backend + Frontend

```mermaid
flowchart TD
    subgraph BACKEND["agent/app/main.py — FastAPI"]
        LIFESPAN["lifespan()<br/>opens SqliteSaver, builds graph once at startup"]
        CHECKPOINT[("checkpoints.db<br/>per-thread_id conversation state")]
        AUTH["verify_api_key()<br/>checks x-api-key header if API_KEY set"]
        LIMITER["slowapi Limiter<br/>10 requests/min per IP"]
        QUERY_EP["POST /query<br/>runs graph.invoke(), returns QueryResponse"]
        HEALTH_EP["GET /health"]
    end

    subgraph FRONTEND["frontend/src/app"]
        LAYOUT["layout.tsx<br/>fonts, root HTML shell"]
        PAGE["page.tsx<br/>textarea, submit, result rendering"]
        UI_COMPONENTS["components/ui/*.tsx<br/>shadcn primitives: Card, Button, Badge, etc."]
    end

    GRAPH["compiled LangGraph<br/>(from diagram 3)"]

    LIFESPAN --> CHECKPOINT
    LIFESPAN --> GRAPH
    AUTH --> QUERY_EP
    LIMITER --> QUERY_EP
    GRAPH --> QUERY_EP

    LAYOUT --> PAGE
    UI_COMPONENTS --> PAGE
    PAGE -->|"fetch POST, x-api-key header"| QUERY_EP
    QUERY_EP -->|"final_answer, report, errors,<br/>completed_agents, execution_logs"| PAGE
```

---

*For prose-level detail on every file's exact logic, see `SYSTEM_DOCUMENTATION.txt`.*
