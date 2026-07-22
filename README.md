# Building Service Management System

Starter monorepo for a FastAPI backend and Vue 3 frontend.

## Structure

```text
Backend/     FastAPI application and tests
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

Alternatively, run both services with `docker compose up --build`.

