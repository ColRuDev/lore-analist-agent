# Lore Analyst Agent

An AI-powered conversational agent for deep analysis of game lore, scripts, and
narrative documents. It combines **Retrieval-Augmented Generation (RAG)** over
local PDF files with **live web search**, delivering structured, source-grounded
analysis through a **streaming CLI** and a **Streamlit web UI**.

---

## Features

- **Local RAG** — Ingests PDF documents (scripts, lore guides, design docs) into
a persistent ChromaDB vector store and retrieves relevant passages using MMR search.
- **Web Search** — Falls back to DuckDuckGo when information is not found in the
local database (e.g., studio news, sequel announcements, OST credits).
- **Conversational Memory** — Maintains full message history within a session,
enabling follow-up questions that reference previous answers.
- **Token Streaming** — Responses are streamed token-by-token to the terminal as
they are generated.
- **Streamlit Web UI** — Browser-based chat interface that mirrors every CLI
feature: token streaming, model switching with history preservation, and a
clear-conversation button.
- **Tool-Calling Agent** — The LLM autonomously decides when to query the local
database, search the web, or answer directly from context.

---

## Architecture

```plaintext
User Input
    │
    ▼
AgentRunner (runner.py)          ← manages history, stream/invoke
    │
    ▼
LangChain Tool-Calling Agent     ← LLM + system prompt
    │
    ├──► lore_database_search     ← ChromaDB MMR retriever (local PDFs)
    │
    └──► web_search               ← DuckDuckGo (live web)
``` 

### Key modules

| Module | Responsibility |
| --- | --- |
| `src/ingestion.py` | ETL pipeline: load PDFs → chunk → embed → store in ChromaDB |
| `src/retriever.py` | Build ChromaDB retriever (MMR, k=5, fetch_k=20) |
| `src/tools.py` | Define `lore_database_search` and `web_search` LangChain tools |
| `src/agent/core.py` | Instantiate the LangChain agent with the LLM and tools |
| `src/agent/runner.py` | `AgentRunner` class: wraps the agent, manages history, exposes `invoke()` and `stream()` |
| `src/agent/chat.py` | Interactive CLI loop |
| `src/models/google.py` | Gemini LLM and embeddings models |
| `src/prompts/lore_analyst.py` | System prompt defining the Senior Script & Lore Analyst persona |
| `src/configs.py` | Global constants (ChromaDB path, retriever parameters) |
| `src/streamlit/session.py` | `init_session_state()` — one-time session bootstrap (runner, model, tools, messages) |
| `src/streamlit/sidebar.py` | `render_sidebar()` — model radio selector + clear-conversation button |
| `src/streamlit/chat.py` | `render_chat()` — chat history, `st.chat_input`, token-by-token streaming |
| `src/streamlit/app.py` | `run()` — page config + wires session, sidebar and chat together |

### Data flow — Ingestion

```text
data/*.pdf
    └─► PyPDFDirectoryLoader
            └─► RecursiveCharacterTextSplitter (chunk=1200, overlap=200)
                    └─► Gemini Embeddings
                            └─► ChromaDB  (./chroma_db)
```

### Data flow — Query

```text
User question
    └─► HumanMessage appended to history
            └─► Agent reasons
                    ├─► [if lore] lore_database_search → ChromaDB MMR → top-5 chunks
                    ├─► [if web]  web_search → DuckDuckGo → text result
                    └─► Final answer streamed token-by-token → terminal
```

---

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- A **Google AI Studio API key**

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd lore-analist-agent
uv sync
```

### 2. Configure environment variables

Create a `.env` file at the project root:

```env
GOOGLE_API_KEY=your_google_ai_studio_api_key_here
```

### 3. Add your source documents

Place PDF files (scripts, lore guides, transcripts, design documents) inside the
`data/` directory:

```text
data/
├── bioshock_script.pdf
├── tron_lore_guide.pdf
└── ...
```

### 4. Ingest documents into the vector store

```bash
uv run python -m src.ingestion
```

This processes all PDFs in `data/`, splits them into chunks, generates
embeddings, and persists them to `./chroma_db`. It is **idempotent** —
re-running it skips chunks that are already stored (deduplication by content hash).

---

## Running the agent

### Interactive CLI (default)

```bash
uv run lore-agent
# or equivalently:
uv run python -m src
```

Example session:

```text
--- Lore Analyst Agent (LAA) ---
Type 'exit' to quit.

You: Who is Tron and what is his primary function?

LAA: ## Character Analysis: Tron

**Identity:** Tron is a security program created by Kevin Flynn...

You: Based on that, what kind of threat does the MCP represent?

LAA: ## Threat Assessment: Master Control Program (MCP)
...

You: exit
Goodbye.
```

### Predefined test queries

```bash
uv run lore-agent --mode test
```

Runs three hardcoded queries against the agent (non-streaming) and prints each
answer — useful for quickly validating the full pipeline.

### Streamlit web UI

Bootstrap the `src/streamlit/` package once (only needed the first time):

```bash
python setup_streamlit.py
```

Then launch the app:

```bash
streamlit run streamlit_app.py
```

The UI opens at `http://localhost:8501`. Features:

- Chat interface with token-by-token streaming (identical to the CLI).
- **Sidebar** — radio selector to switch between Gemini models; history is
  preserved across model changes.
- **Clear conversation** button to reset the session without restarting the server.

---

## Verifying the setup

Run the following checklist to confirm everything works end-to-end.

### 1 — Ingestion succeeded

After running `uv run python -m src.ingestion` you should see log output like:

```bash
[INFO] Loading PDF documents from .../data
[INFO] 142 chunks from 3 documents
[INFO] Added 142 new chunks to the database
```

And a `./chroma_db/` directory will be created at the project root.

### 2 — Agent loads without errors

```bash
uv run lore-agent --mode test
```

Expected: three answers printed to stdout. If you see `"Information not found
in the current lore database."` for questions about your PDFs, verify that
ingestion ran and `chroma_db/` exists.

### 3 — Streaming works

Run the interactive CLI and ask a question about a document you ingested.
Tokens should appear progressively in the terminal as the model generates
them, not all at once.

### 4 — Web search works

Ask something outside the scope of your local documents:

```text
You: Search the web for recent news about BioShock 4
```

The agent will invoke `web_search` and return current results from DuckDuckGo.

---

## Project structure

```text
lore-analist-agent/
├── data/                    # Drop your PDF source files here
├── chroma_db/               # Auto-generated vector store (not committed)
├── src/
│   ├── __main__.py          # Entry point (CLI + test modes)
│   ├── configs.py           # Global constants
│   ├── ingestion.py         # ETL pipeline for PDFs
│   ├── retriever.py         # ChromaDB retriever setup
│   ├── tools.py             # LangChain tool definitions
│   ├── logger.py            # Shared logger factory
│   ├── agent/
│   │   ├── core.py          # Agent factory (LLM + tools → LangChain agent)
│   │   ├── runner.py        # AgentRunner: history management + stream/invoke
│   │   └── chat.py          # Interactive CLI loop
│   ├── models/
│   │   └── google.py        # Gemini LLM and embedding model wrappers
│   ├── prompts/
│   │   └── lore_analyst.py  # System prompt (SLA persona)
│   ├── streamlit/
│   │   ├── __init__.py
│   │   ├── session.py       # Session state bootstrap
│   │   ├── sidebar.py       # Sidebar UI component
│   │   ├── chat.py          # Chat area UI component
│   │   └── app.py           # App assembler (entry point for Streamlit)
│   └── utils/
│       └── hash.py          # SHA-based content deduplication
├── streamlit_app.py         # Thin Streamlit launcher
├── setup_streamlit.py       # One-time script: creates src/streamlit/ modules
├── pyproject.toml
└── .env                     # API keys (not committed)
```

---
