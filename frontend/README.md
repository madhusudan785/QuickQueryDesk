# QuickQueryDesk Frontend — Part 2: Tickets & AI Classification

Builds on Part 1 (auth). Employee ticket creation and "My Tickets" are now
active. Agent dashboard, ticket override UI, and metrics land in Part 3 —
see the commented routes in `src/App.tsx`.

## New in this slice

- `src/pages/CreateTicket.tsx` — title/description/attachment form,
  posts to `POST /tickets`.
- `src/pages/EmployeeDashboard.tsx` — "My Tickets" list: status, category
  and priority badges, empty/loading states.
- `src/pages/EmployeeTicketDetail.tsx` — full ticket view: description,
  AI-suggested category/priority, and the agent's reply once resolved.
  Deliberately does not surface `ai_draft_reply` to the employee — that's
  agent-only review material until a reply is actually sent.
- `src/services/tickets.ts` — all ticket API calls.
- `src/types/index.ts` — updated with `Ticket`, `TicketListItem`,
  `AuditLog`, `Metrics` types (ahead of Parts 3, so nothing to merge later).

## Run it locally

```bash
cd frontend
npm install
npm run dev
```

Run the Part 2 backend alongside this on port 8000 — the Vite dev proxy
forwards `/auth` and `/tickets` there (see `vite.config.ts`).

## Verified before packaging

- `npm install` — clean, 0 vulnerabilities
- `npx tsc -b` — zero TypeScript errors
- `npx vite build` — production build succeeds
- Dev server boots and serves `/` with a `200`
