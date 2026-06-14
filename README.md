# RampUp

AI-Powered New Hire Knowledge Accelerator built on Azure OpenAI + pgvector.

RampUp ingests your company's M365 content (SharePoint documents, Teams
meeting transcripts, OneNote notebooks) and answers new-hire questions with
grounded, source-cited responses.

---

## Project Structure

```
rampup/
├── app/                  # FastAPI backend
│   ├── api/routes.py     # REST endpoints
│   ├── config/           # pydantic-settings
│   ├── core/             # DB engine, ORM models
│   ├── ingestion/        # chunker, embedder, Graph API client
│   ├── migrations/       # Alembic + pgvector HNSW index
│   └── query/            # retriever, answer generator
└── frontend/             # React + Vite + Tailwind UI
    └── src/
        ├── components/
        │   ├── ChatView.tsx    # Chat interface with source citations
        │   ├── IngestView.tsx  # Document ingestion by URL
        │   └── Sidebar.tsx     # Navigation sidebar with server status indicator
        ├── api.ts              # Typed fetch wrappers
        └── App.tsx
```

---

## Backend State

### Implemented

| Area | File(s) | Status |
|---|---|---|
| FastAPI app + lifespan | `app/main.py` | Complete |
| Settings via pydantic-settings | `app/config/settings.py` | Complete |
| Async DB engine manager | `app/core/database.py` | Complete |
| ORM model (DocumentChunk) | `app/core/orm.py` | Complete |
| Alembic migrations (pgvector HNSW index + unique constraint) | `app/migrations/` | Complete |
| Text chunker (tiktoken-based token chunking) | `app/ingestion/chunker.py` | Complete |
| Embedding service (Azure OpenAI with upsert) | `app/ingestion/embedder.py` | Complete |
| Graph API client (synthetic data) | `app/ingestion/graph_client.py` | Placeholder |
| pgvector cosine retriever | `app/query/retriever.py` | Complete |
| GPT-4o answer generator | `app/query/generator.py` | Partial |
| REST API routes (`/ingest`, `/query`, `/health`, `/gaps`) | `app/api/routes.py` | Complete |

### Placeholders (marked `# TODO` in code)

1. **MS Graph OAuth2 flow** (`graph_client.py`) – `get_access_token()` returns
   an empty string; real implementation needs the client-credentials flow
   against `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`.

2. **Retry / backoff** (`embedder.py`) – `embed_text()` has no retry logic;
   add tenacity with exponential backoff for `RateLimitError`.

3. **Async ingestion pipeline** (`routes.py` `/ingest`) – the endpoint
   currently processes ingestion synchronously; wire in ARQ / Celery / Azure Queue Storage for background jobs.

4. **Confidence classification** (`generator.py`) – confidence is inferred
   from the answer text via a string heuristic. Switching to structured JSON
   output from the model (with `response_format={"type": "json_object"}`)
   would be more reliable.

5. **Prompt engineering** (`generator.py` `_SYSTEM_PROMPT`) – the current
   prompt is a starting point. Fine-tune with few-shot examples and
   chain-of-thought instructions for better grounding.

---

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js 18+ and [pnpm](https://pnpm.io/)
- PostgreSQL 15+ with the `pgvector` extension enabled
- Azure OpenAI resource with `text-embedding-3-large` and `gpt-4o` deployments

The easiest way to run PostgreSQL locally is via Docker:

```bash
docker run -d \
  --name rampup-pg \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=rampup \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 1. Install backend dependencies

```bash
cd rampup
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Key variables:

| Variable | Example |
|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/rampup` |
| `LLM_PROVIDER` | `azure` \| `openai` \| `gemini` |
| `AZURE_OPENAI_ENDPOINT` | `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | your key (if using `azure` provider) |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | embedding deployment name (default: `text-embedding-3-large`) |
| `OPENAI_API_KEY` | your key (if using `openai` provider) |
| `GEMINI_API_KEY` | your key (if using `gemini` provider) |

### 3. Run database migrations

```bash
uv run alembic upgrade head
```

Creates the `document_chunk` table and the HNSW vector index.

### 4. Start the API server

```bash
# Run from the project root (rampup/), not from inside app/
uv run uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 5. Start the frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend available at `http://localhost:3000`. The Vite dev server proxies
all `/api/*` requests to `http://localhost:8000` automatically.

---

## Architecture

### Ingestion Pipeline

```
MS Graph API
  └─ SharePoint drive files  ──┐
  └─ Teams meeting transcripts ┘
          │
          ▼
    graph_client.py          (fetch raw documents)
          │
          ▼
    chunker.py               (split into ~512-token chunks with overlap)
          │
          ▼
    embedder.py              (text-embedding-3-large → 3072-dim vectors)
          │
          ▼
  PostgreSQL + pgvector       (store chunks + HNSW index for ANN search)
```

### Query Pipeline

```
User question (POST /api/query)
          │
          ▼
    embedder.embed_text()    (embed question)
          │
          ▼
    retriever.search()       (cosine ANN search → top-K chunks above threshold)
          │
          ▼
    generator.generate()     (GPT-4o with grounding prompt → answer + citations)
          │
          ▼
    QueryResponse            (answer, sources[], confidence)
```

---

## Render Deployment

This project is ready for one-click deployment on Render!

### Using the Blueprint (render.yaml)

1. Fork this repository
2. Go to Render → Blueprints → New Blueprint
3. Connect your forked repository
4. Follow the steps to deploy
5. After deployment, set the required environment variables in the Render dashboard for the `rampup-backend` service:
   - AZURE_OPENAI_ENDPOINT
   - AZURE_OPENAI_API_KEY
   - AZURE_OPENAI_API_VERSION (optional, defaults to 2024-02-15-preview)
   - AZURE_OPENAI_EMBEDDING_DEPLOYMENT
   - AZURE_OPENAI_CHAT_DEPLOYMENT
   - (Or set LLM_PROVIDER to openai/gemini and corresponding keys)

6. (Optional but Recommended) Load Sample Data:
   - Open the Render Dashboard → `rampup-backend` service → Shell
   - Run: `python generate_sample_dataset.py`
   - This will populate the database with sample onboarding documents!

### Manual Deployment

You can also deploy the services manually using the Dockerfiles provided:
- Backend: Uses root Dockerfile
- Frontend: Uses frontend/Dockerfile

---

## Next Steps

1. Implement the MS Graph OAuth2 client credentials flow.
2. (Done) Replaced character chunking with tiktoken-based token chunking.
3. (Done) Added UNIQUE(source_url, chunk_index) migration + upsert logic.
4. Wire the `/ingest` endpoint to a background task queue (ARQ recommended).
5. Add retry / backoff to the embedding calls.
6. Switch GPT-4o output to structured JSON for reliable confidence scoring.
7. Add authentication middleware (Azure AD JWT validation) for production use.
8. Write integration tests against a local pgvector Docker container.
9. Set up Azure Container Apps or AKS deployment with Helm charts.
