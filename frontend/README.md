# QuickQueryDesk Frontend — Part 1: Auth & Roles

This is the **first commit** slice of the frontend: login, registration, JWT
storage, and role-aware routing. Employee/agent dashboards, ticket pages, and
the metrics page are **not** included yet — they land in Part 2 (see the
commented-out routes in `src/App.tsx` for exactly what gets wired back in).

## What's in this slice

- `src/services/api.ts` — Axios instance with a request interceptor that
  attaches the JWT (`Authorization: Bearer <token>`) and a response
  interceptor that clears the session and redirects to `/login` on a 401.
- `src/services/auth.ts` — thin wrapper around `POST /auth/register` and
  `POST /auth/login`.
- `src/context/AuthContext.tsx` + `src/hooks/useAuth.ts` — auth state
  (`user`, `isAuthenticated`, `isLoading`), backed by `localStorage`
  (`access_token` + `user`), restored on page load.
- `src/components/layout/ProtectedRoute.tsx` — the actual route guard: not
  authenticated → redirect to `/login`; wrong role for a `requiredRole`
  route → redirect to that role's dashboard. **This is a UX convenience,
  not the security boundary** — the backend enforces roles independently
  (see the backend Part 1 commit's `require_role` dependency). A user
  could edit `localStorage` and bypass this in the browser; they still
  can't call agent-only endpoints without a valid agent JWT.
- `src/pages/Login.tsx`, `src/pages/Register.tsx` — the actual forms.
- `src/types/index.ts` — shared TypeScript types (includes Ticket/Metrics
  types now, ahead of Part 2, so nothing needs merging later).
- `src/App.tsx` — routing. Only `/login`, `/register`, and a default
  redirect to `/login` are active in this slice.

## Run it locally

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The dev server proxies `/auth` (and a few
other paths reserved for Part 2) to `http://localhost:8000` — see
`vite.config.ts` — so run the Part 1 backend alongside this on port 8000.

## Verified before packaging

- `npm install` — installs cleanly (115 packages, 0 vulnerabilities)
- `npx tsc -b` — zero TypeScript errors
- `npx vite build` — production build succeeds
- `npx vite` — dev server boots and serves `/` with a `200`

## Notes

- JWT is stored in **`localStorage`**, not an httpOnly cookie. Tradeoff:
  simpler to implement and works cleanly with the Axios interceptor
  pattern, at the cost of some XSS exposure compared to httpOnly cookies.
  Worth naming explicitly in the project README's "Decisions and
  Tradeoffs" section.
- Styling is Tailwind v4 via `@tailwindcss/vite` (no `tailwind.config.js`
  needed) with custom design tokens defined in `src/index.css` via
  `@theme`.
