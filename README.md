# Automaton Auditor - FDE Week 2

A LangGraph-based multi-agent system for autonomous code audit and governance.

## Features

- **Parallel Detective Agents**: RepoInvestigator, DocAnalyst, VisionInspector running simultaneously
- **Evidence Collection**: Structured evidence with confidence scores
- **Sandboxed Execution**: Safe git cloning in temporary directories
- **AST Parsing**: Code analysis without regex
- **PDF Analysis**: Text extraction and keyword detection
- **Diagram Detection**: Vision analysis for PDF diagrams

## Setup

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/yourusername/automaton-auditor
cd automaton-auditor
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Copy environment template
cp .env.example .env
# Add your API keys to .env
```

## Usage

```bash
python -m src.main --repo <GITHUB_URL> --pdf <PDF_PATH> --output results.json
```

Example:
```bash
python -m src.main --repo https://github.com/langchain-ai/langgraph --pdf test_report.pdf --output evidence.json
```

## Project Structure

```
src/
├── __init__.py
├── main.py              # Entry point
├── state.py             # Pydantic models + reducers
├── graph.py             # LangGraph parallel execution
├── nodes/
│   └── detectives.py    # Repo, Doc, Vision nodes
└── tools/
    ├── repo_tools.py    # Git cloning, AST parsing
    ├── doc_tools.py     # PDF extraction
    └── vision_tools.py  # Diagram detection
```

## Results (Interim)

- ✅ **11 evidence items collected**
- ✅ **90.9% success rate**
- ✅ **All detectives working in parallel**
- ✅ **Neutral handling of missing diagrams**
- ✅ **Transparent shallow clone explanation**

## Requirements

- Python 3.10+
- Dependencies managed via `pyproject.toml`