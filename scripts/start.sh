#!/bin/sh

set -e

echo "Running database migrations..."

alembic upgrade head

echo "Database migrations completed."

echo "Starting Deployment Risk Analyzer..."

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000