# AI Bug Fixer

An intelligent code analysis system that detects bugs, explains issues in simple terms, and suggests fixes using LangChain and Large Language Models.

## Features

- **Multi-Input Support**:
  - Paste code directly
  - Upload source files
  - Analyze GitHub repositories

- **Bug Detection**:
  - Syntax errors
  - Logical bugs
  - Performance issues
  - Security vulnerabilities
  - Code quality issues

- **Intelligent Output**:
  - Beginner-friendly explanations
  - Fixed code suggestions
  - Severity levels (low/medium/high/critical)
  - Improvement suggestions

- **RAG Integration**:
  - FAISS vector store for semantic search
  - Multi-file context reasoning
  - Sentence Transformers embeddings

## Tech Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **LLM**: NVIDIA Devstral / OpenAI / Claude (API-compatible)
- **Embeddings**: Sentence Transformers
- **Vector DB**: FAISS
- **Framework**: LangChain

## Project Structure

```
ai-bug-fixer/
├── backend/
│   ├── main.py                 # FastAPI application
│   └── services/
│       ├── llm.py              # LLM service
│       ├── embeddings.py       # Embedding generation
│       ├── retriever.py        # FAISS retriever
│       └── bug_fixer.py        # Main bug fixing logic
├── frontend/
│   └── app.py                  # Streamlit UI
├── utils/
│   └── github_loader.py        # GitHub repo loader
├── config.py                  # Configuration settings
├── requirements.txt            # Python dependencies
└── README.md
```

## Installation

### 1. Clone the Repository

```bash
cd ai-bug-fixer
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file (optional):

```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL=mistralai/devstral-2-123b-instruct-2512
```

## Usage

### Start Backend API

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend UI

```bash
cd frontend
streamlit run app.py
```

Or from the root:

```bash
streamlit run frontend/app.py
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze-code` | POST | Analyze single code snippet |
| `/analyze-file` | POST | Analyze uploaded file |
| `/analyze-repo` | POST | Analyze GitHub repository |
| `/analyze-multi-file` | POST | Analyze multiple files |
| `/health` | GET | Health check |

### Example API Request

```python
import requests

# Analyze code
response = requests.post(
    "http://localhost:8000/analyze-code",
    json={
        "code": "def add(a, b):\n    return a - b",  # Bug: should be +
        "filename": "example.py"
    }
)

print(response.json())
```

## API Response Format

```json
{
  "bugs": [
    {
      "type": "logic",
      "severity": "medium",
      "line_start": 2,
      "line_end": 2,
      "description": "Subtraction used instead of addition",
      "simple_explanation": "The function name says 'add' but it subtracts. Change '-' to '+'."
    }
  ],
  "explanation": "The function has a logical bug...",
  "fixed_code": "def add(a, b):\n    return a + b",
  "suggestions": [
    "Add type hints for better code clarity",
    "Include docstring for function documentation"
  ]
}
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Streamlit     │────▶│   FastAPI       │
│   Frontend      │     │   Backend       │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼───────┐         ┌───────▼───────┐
            │  Bug Fixer    │         │   Retriever   │
            │  Service      │         │   (FAISS)     │
            └───────┬───────┘         └───────┬───────┘
                    │                         │
            ┌───────▼───────┐         ┌───────▼───────┐
            │  LLM Service  │         │  Embedding    │
            │  (Devstral)   │         │  Service      │
            └───────────────┘         └───────────────┘
```

## Prompt Engineering

The system uses structured prompts for consistent output:

```
You are a senior software engineer.
Analyze the code and:
1. Identify bugs (syntax, logic, performance, security)
2. Explain in simple terms
3. Provide corrected code
4. Suggest improvements
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For issues and feature requests, please open a GitHub issue.