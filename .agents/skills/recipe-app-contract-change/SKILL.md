---
name: recipe-app-contract-change
description: Playbook for making API contract changes in the recipe-app repo — bump the architecture doc version and revision history, keep dev-steps aligned, regenerate frontend types, and run the full validation chain.
---

# Recipe App — API Contract Change Playbook

Use this skill when changing the backend API contract in this repo (endpoints, request/response schemas, auth behavior, or the cookie contract).

## Repo facts (this repo only)

- Monorepo: `backend/` (FastAPI, Poetry) + `frontend/` (Next.js 16, pnpm)
- Contract source of truth: backend `/openapi.json` → frontend generated `types/api.d.ts`
- Local databases: `recipe_app` on :5432 (dev), `recipe_app_test` on :5433 (tests)

## Steps, in order

1. **Backend change** — update routes/schemas/services under `backend/app/`
2. **Tests** — extend `backend/tests/`; the test schema is recreated per test run, so no manual migrations are needed in tests
3. **Docs** —
   - bump `docs/architecture_document.md` version and add a Revision History row
   - keep `docs/dev-steps_1-14.md` aligned with the new behavior
   - record decisions in `docs/recommendations.md` when a recommendation changes
4. **Regenerate types** — with the backend running: `cd frontend && pnpm run codegen`. Commit `types/api.d.ts`; `openapi.json` stays gitignored.
5. **Validate** —
   - backend: `cd backend && poetry run ruff check . && poetry run ruff format --check . && poetry run mypy . && poetry run pytest`
   - frontend: `cd frontend && pnpm lint && pnpm typecheck`

## Repo-specific gotchas

- The auth cookie is named `access_token`; the frontend constant is `AUTH_COOKIE_NAME` in `frontend/lib/auth-cookie.ts`
- Two client variants handle cookies differently: `frontend/lib/serverApi.ts` forwards the cookie manually (SSR); `frontend/lib/api.ts` uses `credentials: "include"` (browser)
- Alembic migration files are generated code: run `poetry run ruff format alembic/versions` after autogenerate (lint per-file-ignores are already configured)
- Validation order per `AGENTS.md`: lint → typecheck → test
