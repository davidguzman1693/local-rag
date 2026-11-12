FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app/services/ai-service

# Install dependencies first for layer caching
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

# Copy application source
COPY src/ ./src/
COPY main.py cli.py ./
COPY samples/ ./samples/

ENV LOCAL_RAG_HOST=0.0.0.0
ENV LOCAL_RAG_PORT=8000

EXPOSE 8000

CMD ["uv", "run", "python", "main.py"]

