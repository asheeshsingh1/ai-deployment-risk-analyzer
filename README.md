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

Copy the environment file:

```bash
cp .env.example .env