# AI Bug Fixer

An AI-powered code analysis and debugging tool built with **LangChain**, **Streamlit**, and **FastAPI**, using the **NVIDIA Devstral** model to detect bugs, vulnerabilities, and performance issues across your codebase.

---

## Features

- **Code Input** — Paste code directly and get instant AI-generated analysis
- **File Upload** — Upload source files for in-depth review
- **GitHub Repository Analysis** — Point to any public GitHub repo and scan the entire codebase
- **Multi-file Cross-referencing** — Detect issues that span across files (import errors, type mismatches, circular deps)
- **Semantic RAG Retrieval** — FAISS-backed vector index provides contextual code snippets to the LLM
- **Interactive Q&A** — Ask follow-up questions about your code or the analysis results
- **Severity Classification** — Each bug is tagged as `low`, `medium`, `high`, or `critical`
- **Type Classification** — Bugs are categorized as `syntax`, `logic`, `performance`, `security`, or `quality`
- **Side-by-side Code Diff** — View original code alongside the AI-generated fix
- **Parallel File Processing** — Large repositories are analyzed concurrently using `ThreadPoolExecutor`

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **Backend API** | FastAPI + Uvicorn |
| **LLM Orchestration** | LangChain (LCEL chains) |
| **Language Model** | NVIDIA Devstral 2 123B (`mistralai/devstral-2-123b-instruct-2512`) |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) |
| **Vector Store** | FAISS |
| **Language Detection** | Regex-based + filename extension mapping |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│   (Code Input / File Upload / GitHub Repo tabs)     │
└───────────────────────┬─────────────────────────────┘
                        │  HTTP (REST)
┌───────────────────────▼─────────────────────────────┐
│                  FastAPI Backend                     │
│   /analyze-code  /analyze-file  /analyze-repo       │
│   /ask-question  /health                            │
└───────┬───────────────┬─────────────────────────────┘
        │               │
┌───────▼──────┐  ┌─────▼──────────────────────────── ┐
│  LLMService  │  │      BugFixerService               │
│  (LangChain  │  │  - Language Detection              │
│   LCEL chains│  │  - Code Chunking                   │
│   Devstral)  │  │  - RAG Context Retrieval           │
└──────────────┘  │  - Parallel File Processing        │
                  └────────┬───────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │  EmbeddingService       │
              │  + RetrieverService     │
              │  (Sentence Transformers │
              │   + FAISS Index)        │
              └─────────────────────────┘
```

### LangChain LCEL Chains

Three named chains are built on startup and printed as ASCII graphs in the terminal:

| Chain | Purpose |
|---|---|
| `analyze_chain` | Single-file bug analysis |
| `qa_chain` | Interactive Q&A about analyzed code |
| `multifile_chain` | Cross-file repository analysis |

---

## Getting Started

### Prerequisites

- Python 3.9+
- An [NVIDIA API key](https://build.nvidia.com/) (free tier available)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/ai-bug-fixer.git
cd ai-bug-fixer

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy the example env file
cp .env.example .env
```

Open `.env` and add your credentials:

```env
LLM_API_KEY=nvapi-your-key-here
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL=mistralai/devstral-2-123b-instruct-2512

EMBEDDING_MODEL=all-MiniLM-L6-v2
FAISS_INDEX_PATH=./data/faiss_index
```

> **Alternative Models** — The app is compatible with any OpenAI-compatible endpoint. You can switch to OpenAI GPT-4 or Anthropic Claude by updating `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` in `.env`.

---

## Running the App

You need two terminals running simultaneously.

**Terminal 1 — Backend API:**
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Streamlit Frontend:**
```bash
streamlit run frontend/app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Command-Line Interface

A CLI tool is also available for quick analysis without the UI:

```bash
# Analyze a single file
python cli.py analyze path/to/your/file.py

# Analyze a directory
python cli.py analyze path/to/your/project/

# Ask a question about a file
python cli.py ask "What does this function do?" path/to/file.py
```

---

## Supported Languages

| Language | Extensions |
|---|---|
| Python | `.py` |
| JavaScript | `.js`, `.jsx` |
| TypeScript | `.ts`, `.tsx` |
| Java | `.java` |
| C / C++ | `.c`, `.cpp` |
| Go | `.go` |
| Rust | `.rs` |
| Ruby | `.rb` |
| PHP | `.php` |
| Swift | `.swift` |
| Kotlin | `.kt` |

---

## Bug Detection Categories

| Type | Description |
|---|---|
| **Syntax** | Malformed code, missing brackets, incorrect operators |
| **Logic** | Incorrect conditions, off-by-one errors, wrong business logic |
| **Performance** | Inefficient loops, excessive memory use, blocking calls |
| **Security** | SQL injection, hardcoded secrets, unvalidated input |
| **Quality** | Dead code, poor naming, missing error handling |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze-code` | Analyze a code snippet |
| `POST` | `/analyze-file` | Analyze an uploaded file |
| `POST` | `/analyze-repo` | Clone and analyze a GitHub repo |
| `POST` | `/ask-question` | Q&A about analyzed code |
| `GET` | `/health` | Health check |

---

## Project Structure

```
ai-bug-fixer/
├── backend/
│   ├── main.py                  # FastAPI app and route definitions
│   └── services/
│       ├── llm.py               # LangChain LCEL chains + NVIDIA Devstral
│       ├── bug_fixer.py         # Main orchestration service
│       ├── embeddings.py        # Sentence Transformer embedding service
│       └── retriever.py        # FAISS vector store and retrieval
├── frontend/
│   └── app.py                   # Streamlit UI
├── cli.py                       # Command-line interface
├── requirements.txt
├── .env.example
└── README.md
```

---

## About NVIDIA Devstral

**Devstral** is a code-specialized large language model developed by Mistral AI and NVIDIA. The `devstral-2-123b-instruct-2512` variant used in this project offers:

- A **123 billion parameter** architecture optimized for code understanding and generation
- A **32K+ token context window** for handling large files and multi-file codebases
- Strong performance on code reasoning, bug detection, and structured JSON output
- Access via the NVIDIA NIM API with an OpenAI-compatible interface

