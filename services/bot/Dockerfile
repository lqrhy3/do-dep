FROM ghcr.io/astral-sh/uv:debian-slim
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY app/pyproject.toml app/pyproject.toml
COPY services/bot/pyproject.toml services/bot/pyproject.toml
COPY app/src/ app/src/
COPY services/bot/src/ services/bot/src/
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-install-project

COPY . .
RUN uv sync --frozen

CMD ["uv", "run", "--package", "bot", "python", "-m", "bot.main"]