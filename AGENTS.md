# AGENTS.md — Recipe App

## Project State

Always read `docs/architecture_document.md` before coding. Local working tree may be ahead of the document — verify Step status in `docs/dev-steps_1-14.md` before assuming `backend/` or `frontend/` is empty.

For architecture decisions and recommendations, see `docs/recommendations.md`.

## Agent Behavior

Always apply the `mentor-rehire-mode` skill when explaining or teaching in this repo.

## Stack

| Layer | Tech |
|-------|------|
| Frontend                   | Next.js 16 (App Router) + React 19 + Tailwind CSS v4 (PostCSS) + Zustand + Prettier (format) |
| Backend | FastAPI (Python 3.14) + Poetry + async SQLAlchemy + Alembic |
| Database | PostgreSQL 16 (Docker locally, Neon in prod) |
| Images | Cloudinary (unsigned uploads) |
| Package managers | `pnpm` via corepack (frontend), `poetry` (backend) |

## Commands (once code exists)

### Backend
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload          # dev server on :8000
poetry run pytest                                 # all tests
poetry run pytest tests/test_foo.py -k test_bar   # single test
poetry run ruff check . && poetry run ruff format .  # lint + format
poetry run mypy .                                 # type check
poetry run alembic revision --autogenerate -m "x" # migration
poetry run alembic upgrade head                   # apply migrations
```

### Frontend
```bash
cd frontend
pnpm install
pnpm dev                                          # dev server
pnpm run codegen                                  # regenerate API types from /openapi.json (requires backend on :8000)
pnpm run lint                                     # lint
pnpm run format                                   # format (Prettier)
```

### Infrastructure
```bash
docker compose up -d                              # start local PostgreSQL
docker compose down                               # stop
```

## Architecture Facts

- **Monorepo**: `backend/` (FastAPI) + `frontend/` (Next.js 16)
- **Domain setup**: `app.ourrecipeapp.com` (Vercel) + `api.ourrecipeapp.com` (Railway) share one registrable domain for HttpOnly JWT cookies
- **Auth**: JWT in HttpOnly cookie, 24h expiry, HS256. No refresh tokens for MVP
- **PUT /recipes/{id}** does full replace of ingredients/steps — frontend must send complete arrays on every save
- **Soft deletes** on recipes (`is_deleted` flag)
- **API contract**: FastAPI serves `/openapi.json`; frontend generates typed client via `pnpm run codegen` → `types/api.d.ts`
- **GET /users/{id}/recipes** returns only recipes owned by that user (private included for self-access only)

## Key Gotchas

- **Next.js SSR cookie handling**: During SSR, use `cookies()` from `next/headers` in Server Components. For server-to-backend API calls, read the cookie and forward it manually in request headers. Client Components send cookies automatically.
- **Tailwind CSS v4**: Uses PostCSS plugin (`@tailwindcss/postcss`), NOT `@tailwindcss/vite`. Config is CSS-first via `@theme`, no `tailwind.config.js`
- **Server Components are default**: Components are Server Components unless marked `'use client'`. Need `'use client'` for hooks, event handlers, browser APIs.
- **FastAPI async**: Endpoints are `async def`. Mixing sync code in the request path blocks the event loop
- **Local dev cookies**: Omit `Domain` and `Secure` attributes on localhost
- **CORS**: exact origins only, never `*`, when `allow_credentials=True`
- **Railway builds backend with Nixpacks**, not a custom Dockerfile. Use `Procfile` or `railway.json` for start command

## Conventions

- Order: lint → typecheck → test
- Commit `poetry.lock` and `pnpm-lock.yaml`
- Commit generated `types/api.d.ts` alongside backend API changes
- Backend logs JSON to stdout via `loguru`; Railway captures it
- When changing the API contract, update `docs/architecture_document.md` (version + Revision History) and keep `docs/dev-steps_1-14.md` aligned
