

OnboardIQ
New-hire questions answered instantly — grounded in your company's own SharePoint,
Teams, and OneNote content
Theme: 04 — AI Meets Data ·  Function: AI-Powered Employee Onboarding Accelerator
Suggested stack: Azure OpenAI (GPT-4o + text-embedding-3-large) · pgvector · FastAPI ·
React  ·  Optional MS: Azure OpenAI · MS Graph API · Azure Container Apps · Cosmos DB

## Problem Statement
## Problem Background
The first ninety days for a new hire are a continuous scavenger hunt. Onboarding guides live in
SharePoint folders nobody links to. Engineering standards are in a Confluence page last edited
two years ago. The answer to 'when is the benefits deadline?' is in a Teams message from the
HR channel that requires knowing which channel to search. The result is a predictable pattern:
new hires ask their immediate teammates the same questions repeatedly, senior engineers lose
hours a week to repeated answering, and the organisational knowledge that actually governs
day-to-day work — not the official onboarding deck but the real practices, norms, and contacts
— takes months to absorb rather than days.
## Why It Matters
Slow onboarding has a compounding cost. A new hire who takes six months to reach full
productivity costs the organisation four months of marginal output compared to one who
reaches it in two. Senior engineer time spent answering repeated questions is senior engineer
time not spent on the work only they can do. At scale — a hundred new hires a quarter — the
aggregate cost of institutional knowledge being locked in undiscoverable documents is
measured in engineering quarters, not days.
## Solution Summary
## Why This Problem Was Chosen
Retrieval-augmented generation over a company's own M365 corpus is a high-value, tractable
problem. The data already exists in SharePoint, Teams, and OneNote. The questions are
predictable enough that a well-indexed knowledge base can answer the majority of them. The
output — a grounded, source-cited answer — is immediately trustworthy because the new hire

can follow the citation to the original document. The system gets more useful the more content
is ingested, creating a compounding return on the initial setup investment.
## Proposed Solution
OnboardIQ ingests documents from SharePoint, Teams meeting transcripts, and OneNote
notebooks via the Microsoft Graph API. Each document is chunked into ~512-token segments
with overlap, embedded using Azure OpenAI text-embedding-3-large (3,072-dimensional
vectors), and stored in a PostgreSQL pgvector table with an HNSW index for approximate
nearest-neighbour search. When a new hire submits a question, the question is embedded and
a cosine ANN search retrieves the top-K most relevant chunks above a similarity threshold.
GPT-4o synthesises a grounded answer from the retrieved chunks and returns it with source
citations. Questions that cannot be answered above the confidence threshold are logged as
knowledge gaps for HR or the relevant team to address.
## Expected Impact
·        New-hire questions answered in seconds, grounded in company-specific documents
rather than generic LLM training data.
·        Senior engineer interrupt load reduced — repeated factual questions are handled by the
system.
·        Knowledge gaps surfaced systematically — when the system cannot answer, it records
the unanswered question for HR to close.
·        Onboarding time to productivity shortened by making institutional knowledge
immediately discoverable.
## Technical Approach & Implementation
## Solution Workflow
Ingestion: POST /api/ingest triggers fetching from SharePoint or Teams via the Graph API client.
Documents are split by the chunker (~512 tokens, 50-token overlap), embedded by the
embedding service (text-embedding-3-large), and stored in PostgreSQL via the pgvector upsert
pipeline. Query: POST /api/query embeds the question, runs an HNSW cosine ANN search to
retrieve the top-K relevant chunks (similarity threshold: 0.7), and passes the retrieved context to
GPT-4o for grounded answer generation. The response includes the answer, source URLs, and
a confidence classification (high / medium / low / not_found). Questions classified as not_found
are logged to the knowledge_gap table. Sample documents for zero-database testing: run
generate_sample_dataset.py to populate the database with synthetic M365 content. Maximum
upload size per document: 10 MB. For larger files, split before ingestion or use the Azure
Document Intelligence pre-processing pipeline.
## Key Features

·        M365 Content Ingestion — Pulls documents directly from SharePoint and Teams via
the Microsoft Graph API — no manual export required.
·        pgvector HNSW Search — 3,072-dimensional embeddings stored with an HNSW index
for sub-second approximate nearest-neighbour retrieval at scale.
·        Source-Cited Answers — Every answer includes the source URLs of the documents it
was grounded in, so new hires can verify and explore further.
·        Knowledge Gap Logging — Unanswered questions are recorded automatically,
creating a prioritised list for HR to address with new documentation.
·        Sample Dataset Generator — generate_sample_dataset.py creates realistic synthetic
M365 documents for testing without requiring live M365 credentials.
## Technology Stack
## Frontend
·        React + TypeScript
·        Tailwind CSS
·        ChatView (chat interface with citations), IngestView (document ingestion by URL),
Sidebar (navigation + server status)
·        Vite dev server with /api/* proxy
## Backend
·        Python 3.11 + FastAPI
·        SQLAlchemy 2.0 async ORM
·        Alembic migrations (pgvector HNSW index)
·        structlog
## AI / ML
·        Azure OpenAI text-embedding-3-large (3,072-dim) for document and query embedding
·        GPT-4o for grounded answer generation with source citations
·        Cosine similarity ANN retrieval via pgvector HNSW
## Data & Integrations
·        Microsoft Graph API — SharePoint drive files and Teams meeting transcripts
·        PostgreSQL 15+ with pgvector extension
·        Azure AD client credentials OAuth2 flow for Graph API access
·        pypdf for PDF text extraction (future)
·        Azure Document Intelligence for scanned documents (future)
## Models & Algorithms
Chunking: documents are split into ~512-token segments (character-count proxy, to be replaced
with tiktoken cl100k_base) with 50-character overlap so context is not lost at chunk boundaries.

Embedding: text-embedding-3-large produces 3,072-dimensional vectors, stored in the
document_chunk table alongside source URL, chunk index, and raw text. Retrieval: pgvector
HNSW cosine ANN search returns the top-K chunks above a 0.7 similarity threshold. Threshold
and K are configurable via environment variables. Generation: GPT-4o receives the retrieved
chunks as context and is instructed via a grounding prompt to answer only from the provided
context and cite source URLs. Confidence classification uses a string heuristic on the response
(to be replaced with structured JSON output mode).
## Innovation
Knowledge gap logging as a first-class feature — rather than silently returning a low-confidence
answer, the system records unanswered questions and surfaces them to HR as a prioritised
documentation backlog. This turns the system's failures into actionable signals rather than
invisible gaps. Source citation at the chunk level means new hires can follow the answer back to
the original document, building their own understanding of where institutional knowledge lives
rather than becoming dependent on the chatbot.
## Future Scope
## Near-term
·        Implement MS Graph OAuth2 client credentials flow in graph_client.py.
·        Replace character-based chunking with tiktoken cl100k_base for accurate token
boundaries.
·        Add UNIQUE(source_url, chunk_index) constraint and ON CONFLICT DO UPDATE for
safe re-ingestion.
## Medium-term
·        Async background ingestion pipeline via ARQ or Azure Queue Storage.
·        Structured JSON output from GPT-4o for reliable confidence scoring.
·        Azure AD JWT validation middleware for production authentication.
## Long-term
·        Personalised onboarding path — track which questions a new hire has asked and
proactively surface the next most likely questions.
·        Continuous ingestion — subscribe to Graph API change notifications so new documents
are indexed the moment they are created.
·        Multi-tenant deployment — serve multiple organisations from a single instance with
tenant-isolated vector stores.
## Scalability & Larger Vision

## How It Scales
The vector store scales independently of the application tier: pgvector with an HNSW index
handles millions of chunks without architectural change. Ingestion is embarrassingly parallel —
documents are chunked, embedded, and upserted independently, so ingestion throughput
scales with the number of background workers. Query latency is dominated by the embedding
call and the GPT-4o generation, both of which are sub-second at normal load and scale
horizontally with Azure OpenAI capacity. Adding a new source type (OneNote, Confluence,
Google Drive) is a connector addition, not a pipeline redesign.
## How It Expands
The near-term work is completing the Graph API integration so real M365 content is ingested
without manual export. Medium term, async ingestion and continuous change-notification
subscriptions make the knowledge base self-maintaining — documents are indexed the moment
they are published. Long term, personalised onboarding paths and proactive question surfacing
shift the system from reactive (answering questions) to proactive (anticipating what a new hire
needs to know next based on their role and progress).
## The Larger Vision
Institutional knowledge stops being a privilege of tenure. A new hire on day one has the same
access to the company's accumulated knowledge as a five-year employee — not through a
static wiki that is always slightly out of date, but through a live, grounded system that reads from
the same documents the team actually uses. The end state is an organisation where
onboarding time is measured in days rather than months, where senior engineer time is not
consumed by repeated factual questions, and where the quality of the knowledge base is
continuously measured through the gap log.
## Potential Impact
For a single cohort of new hires, OnboardIQ compresses the time-to-productivity curve and
measurably reduces the interrupt load on senior staff. For an organisation onboarding at scale,
the cumulative gain across cohorts is significant: a two-month reduction in onboarding time for a
hundred hires a year is two hundred months of additional productive engineering. The
knowledge gap log has a secondary benefit: it creates a continuous, bottom-up signal of where
documentation is missing, turning onboarding failures into documentation improvement tickets.
