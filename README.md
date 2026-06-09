# CodeLens - AI-Powered Code Review Platform

A GitHub-integrated tool that automatically reviews pull requests,
explains diffs, and learns from your team's review style over time.

## Features

- Automatic PR reviews triggered via GitHub webhooks
- RAG pipeline that indexes your codebase for context-aware feedback
- Inline comments posted directly on pull requests
- Async job queue so reviews never block webhook delivery
- Per-org data isolation for multi-tenant safety

## Tech Stack

- **Backend:** Python 3.12, FastAPI, Uvicorn
- **AI/ML:** OpenAI GPT-4o, text-embedding-3-small, LangChain
- **Vector Store:** ChromaDB (local), Pinecone (production)
- **Queue:** Redis (async job queue)
- **Auth:** GitHub Apps, JWT (RS256), installation access tokens
- **Deployment:** Docker, Railway / Render

## Architecture

GitHub webhook → diff parser → Redis queue → RAG retrieval
→ LLM review → inline PR comments via GitHub Checks API

## Project Status

- [x] Phase 1 — Environment, FastAPI scaffold, project structure
- [x] Phase 2 — GitHub App, webhook pipeline, diff parser, Redis queue
- [x] Phase 3 — RAG pipeline (codebase indexing + retrieval)
- [x] Phase 4 — LLM review engine + inline PR comments
- [ ] Phase 5 — Auth, multi-tenancy, per-org isolation
- [ ] Phase 6 — Docker, deployment, observability

## Setup

### Prerequisites

- Python 3.11+
- Redis
- A GitHub App (see docs)
- OpenAI API key

### Installation

```bash
git clone https://github.com/Rohpar1504/CodeLens.git
cd CodeLens
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
uvicorn app.main:app --reload
```

## Environment Variables

See `.env.example` for all required variables.
