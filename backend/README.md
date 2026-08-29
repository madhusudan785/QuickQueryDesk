# QuickQueryDesk — Part 1: Auth & Roles

This is the **first commit** slice of the backend: authentication, JWT, password
hashing, role-based authorization, CORS, and the initial DB migration.
Tickets, RAG, LLM classification, metrics, and WebSockets are **not** included
here — they land in later commits (see `app/api/`, `app/rag/`, `app/websocket/`
once those exist).

## What's in this slice

- `app/core/config.py` — settings loaded from env vars (`.env`)
- `app/core/security.py` — bcrypt password hashing, JWT create/decode
- `app/core/dependencies.py` — `get_current_user`, `require_role(...)` — the
  actual backend-side role enforcement (not just hidden frontend buttons)
- `app/database/base.py`, `app/database/session.py` — async SQLAlchemy engine/session
- `app/models/user.py` — the `User` model (employee/agent)
- `app/schemas/auth.py`, `app/schemas/user.py` — Pydantic request/response schemas
- `app/api/auth.py` — `POST /auth/register`, `POST /auth/login`
- `app/main.py` — FastAPI app: CORS + auth router + `/health`
- `alembic/` — migration `0001_initial_users` creates the `users` table
- `tests/test_security.py` — hashing + JWT create/decode/expiry tests

## Run it locally

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env            # edit DATABASE_URL to match your local Postgres

alembic upgrade head            # creates the users table

uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/docs` for interactive API docs, or:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Employee","email":"jane@example.com","password":"password123","role":"employee"}'

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"password123"}'
```

## Run tests

```bash
pytest tests/ -v
```

## Notes / gotchas

- The app uses the **async** `asyncpg` driver at runtime (`DATABASE_URL` starts
  with `postgresql+asyncpg://`). Alembic's migration runner is **synchronous**,
  so `alembic/env.py` swaps that for `postgresql+psycopg2://` automatically —
  you don't need to do anything, just make sure `psycopg2-binary` is installed
  (it's in `requirements.txt`).
- Passwords are hashed with `bcrypt` directly (not passlib) — see
  `app/core/security.py`. If you see a `passlib` warning in your logs, it's
  coming from something else in your environment, not this code.
- Role enforcement lives in `app/core/dependencies.py::require_role`, used as
  a FastAPI dependency on protected routes — this is what makes it a backend
  check rather than a frontend-only convenience.
