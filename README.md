# 🤖 Multi-RAG Agent System

## 📖 Overview
The **Multi-RAG Agent** is an advanced AI framework designed to handle complex, multi-domain queries by orchestrating multiple specialized Retrieval-Augmented Generation (RAG) agents. 

Instead of relying on a single, monolithic knowledge base that can lead to diluted context or hallucinations, this system categorizes knowledge into distinct domains. A supervisor agent intelligently routes incoming questions to the appropriate domain-specific worker agents, synthesizing their findings into a single, cohesive answer.

---

## 🏗️ How the Full System Works

The architecture relies on a multi-step orchestration pipeline to process, route, retrieve, and generate answers. Here is the step-by-step lifecycle of a user query:

### 1. Query Ingestion & Intent Recognition (The Router)
When a user submits a query, it first hits the **Supervisor/Router Agent**. This agent does not answer the question directly. Instead, it uses a lightweight LLM call to classify the intent and domain of the prompt. 
* *Example:* If a user asks, "How do our Q3 revenue numbers compare to the new HR leave policy?", the Router identifies two distinct intents: **Financial** and **HR**.

### 2. Parallel Delegation to Specialized Agents
Once the intents are mapped, the Router dispatches the query (or sub-queries) to the relevant **Worker Agents**. Each worker agent is an independent RAG pipeline connected to a specific Vector Database.
* **Agent A (Finance):** Embeds the query, searches the Financial Vector Store, and retrieves Q3 revenue context.
* **Agent B (HR):** Embeds the query, searches the HR Vector Store, and retrieves the leave policy context.

### 3. Domain-Specific Retrieval & Ranking
Each Worker Agent performs semantic search (and optionally keyword-based BM25 search) against its dedicated vector store. The agents rank the retrieved chunks, discard irrelevant data, and format the most pertinent context. 

### 4. Synthesis & Final Generation
The Worker Agents return their retrieved context and draft answers back to the **Synthesizer Agent** (which can be the same as the Supervisor). The Synthesizer aggregates the context from all triggered domains, resolves any conflicting information, and streams a final, highly accurate response back to the user.

---

## 🌟 Key Features
* **Dynamic Routing:** Intelligently directs questions to the right knowledge base, improving retrieval accuracy.
* **Parallel Processing:** Queries requiring multiple domains are processed concurrently by worker agents, reducing latency.
* **Isolated Vector Stores:** Prevents "context pollution" by keeping domain knowledge strictly separated.
* **Self-Correction & Fallback:** If a worker agent fails to find relevant context, the system can gracefully fall back to web search or request user clarification.

---

## 🛠️ Tech Stack (Suggested)
* **Orchestration:** LangChain / LlamaIndex / CrewAI
* **LLMs:** OpenAI (GPT-4o), Anthropic (Claude 3.5), or local models via Ollama
* **Vector Database:** ChromaDB, FAISS, Pinecone, or Qdrant
* **Embeddings:** HuggingFace / OpenAI text-embeddings
* **Backend:** Python, FastAPI

---

## 🚀 Getting Started

### Prerequisites
* Python 3.9+
* API keys for your chosen LLM provider

### Installation
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/chandraPrakash-tripathi/multi_rag_agent.git](https://github.com/chandraPrakash-tripathi/multi_rag_agent.git)
   cd multi_rag_agent