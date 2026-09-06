FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY scripts ./scripts
COPY tests ./tests
COPY alembic.ini .

RUN chmod +x scripts/start.sh

EXPOSE 8000

CMD ["./scripts/start.sh"]