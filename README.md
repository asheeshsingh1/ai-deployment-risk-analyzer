# Deployment Risk Analyzer

An AI-powered system that analyzes software deployments and estimates
the risk of releasing a change to production.

## Current Architecture

GitHub PR
    |
    v
FastAPI
    |
    v
Change Analyzer
    |
    +---- Historical Deployments
    |
    +---- Service Dependencies
    |
    +---- Production Incidents
    |
    +---- Runtime Metrics
    |
    v
Risk Engine
    |
    v
LangGraph
    |
    v
LLM
    |
    v
GitHub PR Comment

## Phase 1

Phase 1 provides the application foundation:

- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- Docker Compose
- Repository model
- Service model
- Deployment model
- Incident model
- Health endpoint

## Setup

Clone Repo:
```bash
git clone https://github.com/asheeshsingh1/ai-deployment-risk-analyzer.git
```

Change Directory:
```bash
cd deployment-risk-analyzer
```

Copy env:
```bash
cp .env.example .env
```

Setup you api keys into the env file.

Docker Commands:
```bash
docker compose pull
docker compose up -d
```

Access Dashboard/UI:
```bash
http://localhost:5173
```