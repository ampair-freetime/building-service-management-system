FROM python:3.12-slim

# uv installs the exact versions pinned in uv.lock (pip would re-resolve on every build).
COPY --from=ghcr.io/astral-sh/uv:0.9.10 /uv /usr/local/bin/uv

# The virtualenv lives outside /app so the development bind mount (./Backend:/app)
# cannot hide it or replace it with the host's .venv.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Dependencies first: this layer is reused until pyproject.toml or uv.lock changes,
# so editing application code no longer reinstalls every package.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts
COPY app ./app

# Run without root so a compromised process cannot modify the image or the host mount.
RUN useradd --system --uid 10001 --no-create-home app
USER app

EXPOSE 8000
CMD ["python", "scripts/start_server.py", "--host", "0.0.0.0"]
