# Retirement Planner

A web application that replaces `Retirement_Planner_Calculator_05102025.xlsx` with a hosted,
multi-user retirement projection tool. Full requirements are in [`PRD.md`](./PRD.md); this file
covers running it.

**Status: P0 + P1 implemented** (see PRD.md §12 for the phase definitions). Built in this pass:

- The projection engine, in both `monthly` (default) and `annual_parity` modes, with the corpus
  floored at zero on exhaustion (the fix for the workbook's defect D1) — verified against the
  workbook's own cached values to within ₹0.005 on every pre-exhaustion row
  (`backend/tests/test_engine_parity.py`).
- Accounts (register/login/refresh/logout), persistent named scenarios with the full input model
  (timeline, money, expenses, dependents, custom goals, income streams), the required-corpus and
  required-SIP solvers, and an anonymous no-login calculator.
- A React SPA: landing-page calculator, scenario list, a five-section edit form, and a results
  dashboard (verdict, metric tiles, corpus and income/expense charts, what-if sliders, solver
  panel, projection table).

**Deferred to a later pass** (confirmed with the user): scenario comparison, Excel/CSV/PDF/JSON
export & import, goal-marker chart annotations, the monthly/annual and nominal/real chart toggles,
the sensitivity grid, account deletion, and any cloud deployment. Password reset works end-to-end
except delivery — the reset link is logged server-side rather than emailed (see
`backend/app/services/email.py`).

## Prerequisites

- Python 3.11+ (developed against 3.14)
- Node.js 20+

## Backend

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate          # or: source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

cp .env.example .env              # adjust SECRET_KEY etc. for anything beyond local dev
alembic upgrade head              # or just run uvicorn — migrations also run on startup

uvicorn app.main:app --reload --port 8000
```

Run the test suite (61 tests: engine formulas, the golden workbook reconciliation, solver
convergence, and API contract tests):

```bash
pytest -q
```

## Frontend (development)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api to the backend on :8000
```

## Production build

The frontend builds into `backend/app/static/`, so the whole application deploys as one FastAPI
process:

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or build the container directly from the repo root:

```bash
docker build -t retirement-planner -f backend/Dockerfile .
docker run -p 8000:8000 -v retirement-planner-data:/app/data retirement-planner
```

**Persistence matters here.** Most PaaS hosts (Railway, Render, Fly.io, Heroku) use ephemeral
container filesystems — a SQLite file written to the container's own disk is lost on every
redeploy or restart, taking every user's scenarios with it. Either attach a persistent volume and
point `DATABASE_URL` at a path on it (the `docker run` command above does this locally via a named
volume), or switch `DATABASE_URL` to a Postgres connection string — the app goes through
SQLAlchemy and Alembic exclusively, so that's a one-line config change with no code change. See
PRD.md §10.3 for the full discussion.

## Configuration

All configuration is via environment variables (`backend/.env.example` documents each one):
`DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_MINUTES`, `REFRESH_TOKEN_DAYS`, `CORS_ORIGINS`,
`LOG_LEVEL`, `ENV` (set to `production` to enable `Secure` cookies).

## Project layout

```
backend/
  app/core/engine.py       the projection engine — PRD.md §5
  app/core/solver.py       the two bisection solvers — PRD.md §5.8, §5.9
  app/api/                 FastAPI routers
  app/models/, schemas/    SQLAlchemy ORM / Pydantic
  alembic/                 database migrations
  tests/                   pytest suite, including the golden workbook reconciliation
frontend/
  src/pages/                route-level pages
  src/components/forms/     the five-section scenario input form
  src/components/dashboard/ verdict, metric tiles, what-if sliders, solver panel, table
  src/components/charts/    corpus timeline & income/expense charts
```
