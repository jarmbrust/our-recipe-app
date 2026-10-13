# Our Recipe App

Cook, share, and discover recipes. A full-stack recipe app built with Next.js and FastAPI — personal storage and organization first (meal planning, grocery runs), sharing and discovery second.

## Status

| Milestone | Scope | Status |
|-----------|-------|--------|
| M1 — Auth | register / login / logout / profile | ✅ Complete |
| M2 — Recipes | create / view / edit / delete / list + search | 🔶 In progress |
| M3 — Deploy + polish | HTTPS deployment, responsive polish, e2e smoke test | ⬜ Planned |

Full plan: [`docs/recommendations.md`](docs/recommendations.md)

## Tech stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS v4 · Zustand |
| Backend | FastAPI · Python 3.14 · Poetry · async SQLAlchemy · Alembic |
| Database | PostgreSQL 16 (Docker locally, Neon in prod) |
| Auth | JWT (HS256, 24h) in an HttpOnly `access_token` cookie — same-site subdomains in prod |
| Tooling | ruff + mypy + pytest · ESLint 10 + Prettier · OpenAPI codegen |

## MVP features

- ✅ Register / login / logout / profile
- ✅ Auth cookie flows in both SSR and browser contexts
- ⬜ Create / view / edit / soft-delete recipes
- ⬜ Paginated, searchable recipe list; public/private visibility
- ⬜ Cloudinary image upload
- ⬜ Deployed over HTTPS

## Architecture

Next.js Server Components fetch from a typed API client generated from the backend's OpenAPI schema — no hand-written DTOs, contract drift fails the build. Auth is a JWT in an HttpOnly cookie: the browser sends it via `credentials: "include"`, Server Components forward it manually. The backend is async FastAPI + SQLAlchemy with Alembic migrations.

Full architecture: [`docs/architecture_document.md`](docs/architecture_document.md)

## Prerequisites

- Docker Desktop (local PostgreSQL only — the app itself runs on the host)
- Python 3.14
- Node.js 24 + pnpm (via corepack)

## Quick start

```bash
# 1. Databases (recipe_app on :5432, recipe_app_test on :5433)
docker compose up -d

# 2. Backend
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload          # http://localhost:8000

# 3. Frontend (new terminal)
cd ../frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
pnpm install
pnpm dev                                          # http://localhost:3000
```

**Backend `.env`** — create `backend/.env` before starting uvicorn:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/recipe_app
JWT_SECRET=<generate: python -c "import secrets; print(secrets.token_urlsafe(64))">
ENV=dev
CORS_ORIGINS=http://localhost:3000
```

## Development commands

Backend:

```bash
cd backend
poetry run pytest
poetry run ruff check . && poetry run ruff format . && poetry run mypy .
poetry run alembic revision --autogenerate -m "description"   # new migration
poetry run alembic upgrade head
```

Frontend:

```bash
cd frontend
pnpm run lint && pnpm run typecheck
pnpm run codegen    # regenerate types/api.d.ts — requires backend running on :8000
```

## Documentation

| Doc | Purpose |
|-----|---------|
| `docs/architecture_document.md` | Full architecture + API contract (v1.3) |
| `docs/dev-steps_1-14.md` | Implementation plan |
| `docs/recommendations.md` | Decision record + milestone plan |

## License

MIT — see [LICENSE](LICENSE).
