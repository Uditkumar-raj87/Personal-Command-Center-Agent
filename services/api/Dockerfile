FROM python:3.12-slim
WORKDIR /app
COPY services/api /app/services/api
COPY packages /app/packages
RUN pip install --no-cache-dir fastapi uvicorn pydantic sqlalchemy alembic python-dotenv