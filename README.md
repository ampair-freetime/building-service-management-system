# Building Service Management System

Starter monorepo for a FastAPI backend and Vue 3 frontend.

## Structure

```text
Backend/
  app/
    db/      Database base class and async session
    api/     FastAPI endpoints
    core/    Application configuration
  tests/     Backend tests
Frontend/    Vue 3 application built with Vite
.codex/      Repository-local development skill
```

## Run locally

Start the API:

```bash
cd Backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Start the web application in another terminal:

```bash
cd Frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`; the API and its documentation run at
`http://localhost:8000` and `http://localhost:8000/docs`.

Alternatively, run the PostgreSQL database, API, and web application together:

```bash
docker compose up --build
```

PostgreSQL is available locally on port `5432`. Its data is persisted in the
`postgres_data` Docker volume. The development credentials can be overridden
with `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`.

