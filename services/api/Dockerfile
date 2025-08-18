FROM ghcr.io/astral-sh/uv:debian-slim
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY app/pyproject.toml app/pyproject.toml
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY app/src/ app/src/
COPY services/api/src/ services/api/src/
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-install-project

COPY . .
RUN uv sync --frozen

CMD ["uv", "run", "--package", "api", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]