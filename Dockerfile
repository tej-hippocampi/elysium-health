# CareGuide backend + frontend (patient dashboard). Landing is deployed separately.
FROM python:3.12-slim

WORKDIR /app

# Copy backend and frontend (backend serves /static from ../frontend)
COPY backend/requirements.txt backend/
COPY backend/ backend/
COPY frontend/ frontend/

RUN pip install --no-cache-dir -r backend/requirements.txt

WORKDIR /app/backend
EXPOSE 8000

# Use PORT from environment (Railway, Render, etc.) or default 8000
ENV PORT=8000
CMD ["sh", "-c", "python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
