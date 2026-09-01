# QuickQueryDesk Frontend — Part 3: Agent Dashboard, Overrides & Live Updates

Builds on Parts 1–2 (auth, employee ticket creation). Agent dashboard,
ticket override, AI-draft review/send, audit log display, and now
real-time WebSocket updates are all active. The metrics dashboard lands
in Part 4 — see the commented route in `src/App.tsx`.

## Real-time updates (new)

- `src/services/websocket.ts` — a small `WebSocketService` class with
  automatic reconnect (exponential backoff, capped at 10 attempts).
  This file already existed in the codebase but wasn't imported
  anywhere — this slice actually wires it into the dashboards.
- `src/hooks/useWebSocket.ts` — new. A thin hook that reads the JWT from
  `localStorage`, opens a `WebSocketService` connection to the given path
  (`/ws/agent` or `/ws/employee`), and cleans up on unmount.
- `AgentDashboard.tsx` — connects to `/ws/agent`; on a `ticket_created`
  event, re-fetches the ticket list (respecting whatever filters are
  currently active) so a new ticket appears without a manual refresh.
- `EmployeeDashboard.tsx` — connects to `/ws/employee`; on
  `ticket_resolved`, re-fetches "My Tickets" so the status flips live.
- `EmployeeTicketDetail.tsx` — also connects to `/ws/employee`; if the
  specific ticket being viewed gets resolved while the employee has it
  open, the page refreshes itself to show the reply.

Re-fetching on event (rather than merging the WebSocket payload directly
into local state) was a deliberate choice: it reuses the existing,
already-tested REST fetch logic instead of duplicating list-merge/dedupe
logic, and it keeps REST as the actual source of truth — the WebSocket
event is just a trigger to go re-check it.

## New in this slice

- `src/pages/AgentDashboard.tsx` — all tickets, with search-by-title and
  status/category/priority filters (server-side, via query params on
  `GET /tickets`). Shows an open/resolved count summary.
- `src/pages/AgentTicketDetail.tsx` — the full agent workflow:
  - Original ticket + submitting employee
  - AI-suggested category/priority shown side-by-side with the current
    (possibly overridden) value, with an arrow indicator when they differ
  - Override controls (category/priority dropdowns + "Update
    Classification"), which call `PATCH /tickets/{id}` and refresh the
    audit log on success
  - AI draft reply with its knowledge-base source citations
    (title + content preview)
  - An editable reply textarea, pre-filled with the AI draft when one
    exists, with "Send Reply" calling `POST /tickets/{id}/reply`
    (resolves the ticket)
  - Override history (audit log): field, old → new value, agent, timestamp
- `src/App.tsx` — agent routes (`/agent/dashboard`, `/agent/tickets/:id`)
  now active alongside the employee routes from Part 2.

**No backend changes in this slice** — `GET /tickets`, `PATCH
/tickets/{id}`, `POST /tickets/{id}/reply`, and `GET /tickets/{id}/audit`
were already built and confirmed working via Swagger before this frontend
was added. This is a pure UI layer on top of already-tested endpoints.

## Run it locally

```bash
cd frontend
npm install
npm run dev
```

Run the Part 3 backend alongside this on port 8000 — the Vite dev proxy
forwards `/auth` and `/tickets` there (see `vite.config.ts`).

## Verified before packaging

- `npm install` — clean, 0 vulnerabilities
- `npx tsc -b` — zero TypeScript errors
- `npx vite build` — production build succeeds
- Dev server boots and serves `/` with a `200`

## Note

`Navbar.tsx` also links to `/agent/metrics`, which isn't routed until
Part 4 — that link will 404 until then, same as the agent routes did in
the Part 2 slice.

## Not verified in this build sandbox

The WebSocket connection itself was not opened against a live backend in
the sandbox this was built in (no way to run both processes and a real
browser together here). `tsc -b`, `vite build`, and the dev server
boot/serve were all verified — the actual live-update behavior needs a
real end-to-end test on your machine: run the backend, run this
frontend, open an agent dashboard tab and an employee tab, and confirm
events actually arrive. See backend/README.md's "Verified for this
slice" section for the equivalent backend-side caveat.
