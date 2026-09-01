# QuickQueryDesk — Backend (through Part 3)

## What's new in this slice: WebSocket real-time updates

Agent dashboard and ticket detail (Part 3 frontend, built earlier) now
receive live updates. **This closes a real gap**: the WebSocket
infrastructure (`ConnectionManager`, `/ws/agent`, `/ws/employee`
endpoints, JWT-validated) already existed in the codebase, but nothing
actually called `manager.notify_agents()` or `manager.notify_employee()`
— `api/tickets.py` had a literal `# WebSocket notification will be added
in Phase 10` comment where the call should have been. This commit wires
those two calls in:

- `POST /tickets` (ticket creation) → `manager.notify_agents("ticket_created", ...)`
  — every connected agent's dashboard gets the new ticket live.
- `POST /tickets/{id}/reply` (resolve) → `manager.notify_employee(employee_id,
  "ticket_resolved", ...)` — the specific employee who filed that ticket
  sees it flip to Resolved live, if they're connected.

### Why WebSockets (not Socket.io or SSE)

Native FastAPI WebSockets need no extra dependency, and both real-time
requirements here are simple push notifications with no need for
Socket.io's rooms/namespaces. FastAPI's `@app.websocket(...)` plus a
small in-memory connection manager is enough.

### Connection management

`app/websocket/manager.py`'s `ConnectionManager` tracks two pools:
agent connections (a flat list — every agent sees every new ticket) and
employee connections (keyed by `user_id` — each employee only gets
events for their own tickets, since the manager targets
`notify_employee(user_id, ...)` at a specific key). It's in-memory only:
if the server restarts, all connections drop and clients must reconnect
(which they do automatically — see below). This is a known, accepted
limitation for this project's scope; a production system would use
Redis pub/sub or similar to survive restarts and scale across multiple
backend processes.

### Auth

The browser's native WebSocket API can't set custom headers, so the JWT
is passed as a query parameter (`/ws/agent?token=...`) and validated via
`decode_access_token` before `websocket.accept()` is called — an invalid
or missing token gets the connection closed immediately with
`WS_1008_POLICY_VIOLATION`. The agent endpoint additionally checks
`payload["role"] == "agent"` before accepting.

### On disconnect

The backend catches `WebSocketDisconnect` and removes the connection
from the manager's pool. The frontend (`services/websocket.ts`)
reconnects automatically with exponential backoff (1s, 2s, 4s, ... up to
30s, capped at 10 attempts). **REST APIs remain the source of truth** —
if a client misses an event during a disconnect, the next page load or
manual refresh still shows the correct state from the database, since
WebSocket only supplements the initial load, it never replaces it.

## Everything else

No other backend changes since Part 2 — ticket creation, LLM
classification (Groq/Gemini), and the RAG pipeline (see the earlier README section
below, and the Part 2 zip's notes) are unchanged and still verified
working via the live retrieval test you ran locally.

## What's in this slice

**Backend**
- `app/models/ticket.py`, `app/models/audit_log.py` — the `Ticket` and
  `AuditLog` tables. `ai_category`/`ai_priority` are set once at creation
  and never mutated; `current_category`/`current_priority` start as copies
  and can be overridden by an agent later (Part 3) — this split is what
  makes "AI suggested vs. what an agent actually chose" comparable.
- `app/services/llm.py` — calls Groq or Gemini (Groq as active provider)
  to classify a ticket into one of `IT/HR/Finance/Admin/Other` and
  `Low/Medium/High`. Uses a **structured JSON schema** / output on the LLM
  call to constrain output, then
  independently re-validates the parsed result against the allowed sets
  and falls back to `Other`/`Medium` if the LLM returns anything invalid
  or the call fails. Same file also generates the AI draft reply, grounded
  in whatever the RAG pipeline retrieves.
- `app/rag/knowledge_base.py` — **loads the 8 markdown articles directly
  from `backend/knowledge_base/*.md`** using LangChain's `DirectoryLoader`
  + `TextLoader`. Each file's first `# Heading` becomes the article title;
  category is assigned via a filename → category map. This replaced an
  earlier hardcoded Python list of articles — the `.md` files are now the
  actual, real source of truth for the vector store, not just for show.
- `app/rag/engine.py` — chunks articles (`RecursiveCharacterTextSplitter`,
  chunk_size=800, overlap=100), embeds with
  `sentence-transformers/all-MiniLM-L6-v2` (CPU, normalized), indexes with
  FAISS, and retrieves top-k with a relevance-score threshold (0.3) so a
  query with no genuinely relevant article returns nothing rather than a
  weak forced match — this is what lets the AI say "not covered in the
  knowledge base" instead of hallucinating.
- `app/api/tickets.py` — `POST /tickets` (create + classify + retrieve +
  draft, all in one request), `GET /tickets/my` (employee, own tickets
  only), `GET /tickets` (agent, filterable), `GET /tickets/{id}`,
  `PATCH /tickets/{id}` (agent override + audit log), `POST
  /tickets/{id}/reply` (resolve), `GET /tickets/{id}/audit`. Role checks
  are enforced in the route body itself, not just via frontend routing.
- Alembic migration `0002` adds `tickets` and `audit_logs` on top of
  Part 1's `users` table.

**Frontend**
- `pages/CreateTicket.tsx` — title/description/attachment form.
- `pages/EmployeeDashboard.tsx` — "My Tickets" list with status, category,
  and priority badges.
- `pages/EmployeeTicketDetail.tsx` — shows the ticket, its AI-suggested
  category/priority, and the agent's final reply once resolved. **Does
  not show `ai_draft_reply`** — that's intentional, not a gap: the draft
  is meant to be reviewed and edited by an agent before the employee ever
  sees a reply (matches the assessment brief's "editor where the agent
  can edit the AI draft" — the draft is agent-facing, shown on
  `AgentTicketDetail.tsx` in Part 3).
- `services/tickets.ts` — all ticket API calls (including agent/metrics
  endpoints used starting Part 3, kept here now so nothing needs merging
  later).

## Run it locally

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env            # edit DATABASE_URL; add LLM_API_KEY if you have one

alembic upgrade head            # creates users, tickets, audit_logs

uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

Register an employee, log in, submit a ticket from `/tickets/new`.

## Verified before packaging

- `pip install -r requirements.txt` — succeeds
- All 8 backend tests pass (`pytest tests/ -v`)
- Knowledge base loader: all 8 `.md` articles load with correct titles
  and categories extracted from the actual file content
- Text splitting: real pinned `langchain==0.3.25` produces 24 sensible
  chunks from the 8 articles
- Full app boots with all 14 expected routes registered (auth + tickets)
- Frontend: `npm install`, `tsc -b` (zero errors), `vite build`
  (succeeds), dev server boots and serves `200`

## Verified for this slice

- `python3 -c "from app.main import app"` — boots cleanly with `/ws/agent`
  and `/ws/employee` registered alongside all REST routes
- All 8 backend tests still pass after the changes
- Simulated a full connect → notify_agents → notify_employee flow with
  fake WebSocket objects standing in for real browser connections —
  confirmed the right message (`{"event": ..., "data": ...}`) reaches
  the right connection pool
- **Not verified**: an actual browser-to-server WebSocket connection end
  to end (open two browser tabs, one agent one employee, submit a ticket,
  watch it appear live). Do this yourself as the real smoke test — open
  the agent dashboard and an employee "My Tickets" tab side by side,
  submit a ticket as the employee, confirm it appears on the agent
  dashboard without refreshing; then resolve it as the agent and confirm
  the employee tab flips to Resolved without refreshing.

## Known gaps — read before assuming full coverage

- **`sentence-transformers` (and its `torch` dependency) could not be
  installed or exercised in the sandbox this was built in** — it's a
  multi-GB install that didn't fit. Everything *around* the embedding
  model (document loading, chunking, FAISS wiring, retrieval-call
  structure) was verified; the live embedding + FAISS index build was
  not. Run this yourself as your first real smoke test:
  ```bash
  python3 -c "
  import asyncio
  from app.rag.engine import retrieve_relevant_articles
  print(asyncio.run(retrieve_relevant_articles('VPN not connecting', top_k=3)))
  "
  ```
  You should see 1+ sources with `relevance_score` as a plain float, and
  a title like "VPN Setup Guide".
- **`tests/test_llm.py::test_retrieve_relevant_articles_serialization` is
  a false green without the embedding model installed.** It's guarded by
  `if sources:` — with no embeddings available, `retrieve_relevant_articles`
  returns `[]` and the real assertion (that scores serialize to JSON as
  native floats, not `numpy.float32`) never runs. It'll only give real
  coverage once run somewhere `sentence-transformers` is actually
  installed. Worth tightening later (e.g. skip-with-reason instead of a
  silent pass) so a missing dependency can't masquerade as a passing test.
- Alembic migrations were verified structurally against SQLite (no
  Postgres server available in the build sandbox). Run `alembic upgrade
  head` against your real Postgres as your first step — it should work
  identically, but hasn't been confirmed against the actual target DB.
- No file upload — per spec, `attachment_filename` is just a stored
  string.
