# Recipe App

Monorepo: `backend/` (FastAPI) + `frontend/` (Next.js 16).

See `docs/architecture_document.md` for the full MVP architecture.
See `docs/dev-steps_1-14.md` for the implementation plan.

## Quick start

```bash
docker compose up -d          # start local PostgreSQL
cd backend && poetry install  # install backend deps
cd ../frontend && pnpm install # install frontend deps
```

### Versions

```bash
python 3.14
```
