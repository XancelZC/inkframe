# InkFrame

InkFrame is an AI-assisted novel-to-screenplay converter. It turns Chinese or English prose into an editable structured screenplay draft, with source references, confidence scores, inferred-content markers, and intermediate JSON files for debugging.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) OpenAI API key for real LLM provider

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

### LLM Provider

By default, InkFrame uses a **mock provider** that returns deterministic JSON. No API key required.

To use a real LLM provider, set environment variables:

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1  # optional
```

## Architecture

```
Novel Text
  |
  v
Stage 0: Text Preprocessing (pure rules)
  - Split into chapters and paragraphs
  - Detect language (zh/en)
  - Assign stable IDs
  |
  v
Stage 1: Character Extraction (LLM)
  - Extract characters, aliases, descriptions
  - Build relationship graph
  - Uses jieba/spaCy for candidate names
  |
  v
Stage 2: Scene Synthesis (LLM)
  - Generate scenes with dialogue, action, narration
  - Link elements to source paragraphs
  - Mark inferred content and confidence scores
  |
  v
Stage 3: Consistency Validation (rules)
  - Check character name references
  - Verify scene continuity
  - Flag low-confidence elements
  |
  v
YAML Export
  - Structured screenplay with metadata
  - Source references for traceability
```

Each stage reads the previous stage's JSON output and writes its own. Intermediate files are stored in `data/projects/<project_id>/`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/projects` | List all projects |
| POST | `/api/projects` | Create project (form: title, text, file) |
| GET | `/api/projects/{id}` | Get project detail |
| POST | `/api/projects/{id}/process?from_stage=...` | Run pipeline from stage |
| GET | `/api/projects/{id}/stages/{stage}` | Get stage intermediate JSON |
| GET | `/api/projects/{id}/characters` | Get character table |
| PUT | `/api/projects/{id}/characters` | Save edited characters |
| GET | `/api/projects/{id}/screenplay` | Get screenplay |
| PUT | `/api/projects/{id}/screenplay` | Save edited screenplay |
| GET | `/api/projects/{id}/validation` | Get validation log |
| GET | `/api/projects/{id}/export` | Download YAML |
| GET | `/api/projects/{id}/status` | Get pipeline status |
| GET | `/api/projects/{id}/events` | SSE progress stream |
| GET | `/api/models` | List LLM providers |

## Frontend Features

- **Split Editor**: Left pane (source text) + right pane (screenplay cards)
- **Bidirectional Linking**: Hover paragraph highlights linked screenplay elements
- **Character Table**: View and edit extracted characters
- **Relationship Graph**: Visual character network (React Flow)
- **Scene Timeline**: Horizontal timeline of scenes
- **Validation Log**: Filterable log with severity indicators
- **YAML Preview**: Live JSON preview of screenplay
- **Export**: Download screenplay as YAML file

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

## Project Structure

```
inkframe/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── llm/          # LLM provider abstraction
│   │   ├── models/       # Pydantic data contracts
│   │   ├── pipeline/     # Stage 0-3 implementations
│   │   ├── storage.py    # File-backed storage
│   │   └── main.py       # FastAPI app
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/   # Graph, Timeline, SceneList
│   │   ├── pages/        # Home, NewProject, ProjectDetail
│   │   └── App.tsx       # Client-side routing
│   └── package.json
├── examples/             # Sample novel texts
├── PRD.md                # Product requirements
├── theme.css             # Design tokens
└── .agents/              # Design guide
```

## Documentation

- [PRD.md](./PRD.md): Product requirements, architecture decisions, API contract, storage contract
- [theme.css](./theme.css): Design tokens (Notion-based)
- [.agents/DESIGN_GUIDE.md](./.agents/DESIGN_GUIDE.md): UI implementation guidance
