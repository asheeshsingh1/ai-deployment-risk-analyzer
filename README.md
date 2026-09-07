# Deployment Risk Analyzer

An AI-powered system that analyzes software deployments and estimates
the risk of releasing a change to production.

## Current Architecture

GitHub/Gitlab PR
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
AI Analysis

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