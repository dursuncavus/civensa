FROM python:3.12-slim
WORKDIR /app
# eMudhra advisory (Oct 2026): refresh the system CA store on every image build.
RUN apt-get update && apt-get install -y --no-install-recommends --only-upgrade ca-certificates && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini sitecustomize.py ./
ENV PYTHONPATH=/app DEMO_SEED=0
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
