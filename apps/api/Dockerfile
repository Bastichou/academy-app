FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080
CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8080"]
