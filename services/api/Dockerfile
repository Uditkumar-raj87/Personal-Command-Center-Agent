FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY services/api /app/services/api
COPY packages /app/packages
RUN pip install --no-cache-dir .