import asyncio
import sys
from pathlib import Path

# Add the project root to the path so we can import our app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import db_manager
from app.core.orm import build_session_maker, DocumentChunk
from app.ingestion.chunker import text_chunker
from app.ingestion.embedder import embedding_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


SAMPLE_DOCUMENTS = [
    {
        "text": """
Welcome to Contoso! This guide covers your first 90 days.

Week 1: IT setup, badge access, and team introductions. Make sure to set up your
laptop with our standard tools including VS Code, GitHub, and Slack. Your manager
will schedule a 1:1 with you on your first day.

Week 2: Product training and shadow sessions with senior engineers. You'll be
paired with a buddy who can answer all your questions. The engineering team
meets every Tuesday at 10 AM for standup.

Week 4: First project assignment! You'll start with a small feature to get
familiar with the codebase.

Benefits enrollment deadline is Day 30. Your HR contact is hr-support@contoso.com
for any questions.

PTO policy: All new hires get 15 days of PTO per year, plus 10 paid holidays.
You can start using PTO after your 90-day probation period.
        """.strip(),
        "source_url": "https://contoso.sharepoint.com/sites/hr/Documents/New_Hire_Onboarding_Guide_2024.pdf",
        "source_type": "sharepoint",
        "title": "New Hire Onboarding Guide 2024"
    },
    {
        "text": """
Engineering Standards & Practices

All code must pass CI before merging. Our CI pipeline includes:
- Linting with ESLint and Flake8
- Unit tests with pytest and Jest
- Integration tests for critical paths

Branch naming convention: feature/<ticket-id>-short-description
Example: feature/ENG-1234-add-user-auth

PRs require two approvals from team members. At least one approval should be from
a senior engineer or tech lead.

Deploy to staging every Wednesday; production every other Friday.

On-call rotation is managed via PagerDuty. Each team is on call for one week at a time.
Runbooks live in Confluence at https://confluence.contoso.com/display/ENG/Runbooks

Tech stack:
- Backend: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React 18, TypeScript, Tailwind CSS, Vite
- AI/ML: Azure OpenAI, pgvector for vector storage
        """.strip(),
        "source_url": "https://contoso.sharepoint.com/sites/eng/Documents/Engineering_Standards.docx",
        "source_type": "sharepoint",
        "title": "Engineering Standards & Practices"
    },
    {
        "text": """
Q1 All-Hands Meeting – Engineering

VP Engineering: Our Q1 priorities are reliability, reducing P0 incidents by 40%,
and launching the self-serve billing portal.

EM: The new hire cohort starts February 1st. Please add them to Slack channels,
including #eng-general and #team-<your-team-name>.

DevOps: Migration to Kubernetes is 70% complete; target GA is end of Q2. We're
using AKS (Azure Kubernetes Service) for our cloud infrastructure.

Product: We're shipping the new analytics dashboard next month! It will include
real-time metrics and custom reporting.

IT support: Contact it-helpdesk@contoso.com for any tech issues. They're available
Monday-Friday, 8 AM-6 PM PST.
        """.strip(),
        "source_url": "https://teams.microsoft.com/l/meeting/transcript/abc123",
        "source_type": "teams",
        "title": "Q1 All-Hands Meeting – Engineering Transcript"
    }
]


async def main():
    print("🚀 Starting sample dataset generation...")

    # Initialize DB
    await db_manager.initialize()
    session_factory = build_session_maker()

    async with session_factory() as session:
        # Check if we already have chunks
        existing = await session.execute(select(DocumentChunk).limit(1))
        if existing.scalar_one_or_none():
            print("⚠️ Found existing document chunks!")
            response = input("Do you want to continue and add more samples? (y/N): ").strip().lower()
            if response != 'y':
                print("✅ Exiting without changes.")
                return

        # Process each document
        total_chunks = 0
        for doc in SAMPLE_DOCUMENTS:
            print(f"\n📄 Processing: {doc['title']}")

            # Chunk the document
            chunks = text_chunker.chunk_document(doc)
            print(f"   → Split into {len(chunks)} chunks")

            # Embed and upsert
            await embedding_service.upsert_chunks(session, chunks)
            await session.commit()

            total_chunks += len(chunks)

        print(f"\n✅ Done! Added {total_chunks} chunks total.")


if __name__ == "__main__":
    asyncio.run(main())
