# Backend container for Railway (or any Docker host).
FROM python:3.12-slim

WORKDIR /app

# Install deps first for layer caching.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# App code.
COPY backend/ ./

# Railway provides $PORT. Default to 8000 locally.
ENV PORT=8000
# Mock mode stays the main line until real endpoints are verified.
ENV LBANK_WIDGET_MOCK_MODE=true

# Shell form so $PORT expands at runtime.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
