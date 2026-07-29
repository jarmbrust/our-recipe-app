# Implementation Plan — Steps 1 through 14

**Source:** Derived from `docs/architecture_document.md` (MVP v1.0, July 20, 2026).
**Convention:** After each meaningful step, run **lint → typecheck → test** in that order (see `AGENTS.md` §Conventions).

---

## Step 1 — Repo + environment scaffolding

**Goal:** An empty monorepo, both halves cleanly isolated, runnable local services.

1. Confirm GitHub repo exists; init locally if not (remote README only — no code pushed yet).
2. Create top-level layout:

   ```
   recipe-app/
     backend/
     frontend/
     docs/
       architecture_document.md
       dev-steps_1-14.md
     docker-compose.yml
     .gitignore
     .editorconfig
     README.md
     AGENTS.md
   ```
3. Write `.gitignore` for:
   - `node_modules/`, `.next/`, `.venv/`
   - `__pycache__/`, `*.pyc`
   - `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`
   - `alembic/versions/__pycache__/`
   - `.env`, `.env.*`
   - `.DS_Store`
   - `frontend/openapi.json` (reproducible; gitignore)
   - `frontend/types/api.d.ts` is **committed** after codegen
4. `.editorconfig`: 2-space indent for web, 4-space for `*.py`; LF line endings; `trim_trailing_whitespace = true`; `insert_final_newline = true`.
5. `docker-compose.yml` — two services only:
   - `postgres` on `5432`, persistent named volume, healthcheck.
   - `postgres-test` on `5433` for pytest, ephemeral.
   Both `postgres:16-alpine`.
6. Verify with `docker compose up -d` → `docker compose ps` shows both `Up (healthy)`. Stop with `docker compose down`.

**Verification:** repo is clean; both Postgres services healthy.

---

## Step 2 — Backend skeleton (FastAPI + Poetry)

**Goal:** `poetry run uvicorn` boots a hello-world app that returns a version string at `/api/health`.

1. `cd backend && poetry init -n`. Pin Python: `poetry env use 3.12` (or 3.13 — choose one and document in `README.md`).
2. Runtime deps (single `poetry add` call):
   - `fastapi[standard]`
   - `uvicorn[standard]`
   - `pydantic[email]`
   - `pydantic-settings`
   - `sqlalchemy[asyncio]`
   - `asyncpg`
   - `alembic`
   - `pyjwt` (or `python-jose[cryptography]`)
   - `passlib[bcrypt]`
   - `python-multipart`
   - `loguru`
3. Dev deps: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`, `freezegun`.
4. Layout:

   ```
   backend/
     pyproject.toml
     poetry.lock          (commit)
     app/
       __init__.py
       main.py
       config.py
       api/
         __init__.py
         deps.py          (get_db, get_current_user — placeholders)
         routes/
           __init__.py
           health.py
       db/
         __init__.py
         base.py          (DeclarativeBase)
         session.py       (async engine + sessionmaker)
       models/            (filled in Step 3)
       schemas/           (filled in Step 4–5)
       services/          (filled in Step 4–5)
     alembic/
       env.py
       script.py.mako
     alembic.ini
   ```
5. `app/config.py`: pydantic-settings `Settings` reading `.env`. Fields:
   - `DATABASE_URL`
   - `JWT_SECRET`
   - `JWT_ALGORITHM = "HS256"`
   - `JWT_EXPIRES_MINUTES = 1440`
   - `ENV = "dev" | "prod"`
   - `CORS_ORIGINS: list[str]`
6. `app/main.py`: `FastAPI()` instance, `CORSMiddleware` with env-driven `allow_origins`, mount `api_router = APIRouter(prefix="/api")`. Include `/health`.
7. `app/db/session.py`: `create_async_engine`, `async_sessionmaker(expire_on_commit=False)`, `get_db()` dependency yielding `AsyncSession`.
8. `app/api/deps.py`: empty placeholders for `get_current_user`.
9. `pyproject.toml` tool configs:
   - `[tool.ruff]`: `line-length = 100`, `target-version = "py312"`, rules `E,F,W,I,UP,B,SIM`.
   - `[tool.ruff.format]`: quote-style `preserve`.
   - `[tool.mypy]`: `strict = true`, `plugins = ["pydantic.mypy"]`.

**Verification:** `poetry run uvicorn app.main:app --reload` → `http://localhost:8000/docs` and `http://localhost:8000/api/health` both return 200. Then `poetry run ruff check . && poetry run ruff format --check . && poetry run mypy .` clean.

---

## Step 3 — Database migrations (SQLAlchemy + Alembic)

**Goal:** `alembic upgrade head` creates the full schema on a fresh Postgres.

1. `app/db/base.py`: `DeclarativeBase` + typing pattern suitable for SQLAlchemy 2.x async.
2. Write all models up front so autogenerate produces one reviewable migration:
   - `User` (per `architecture_document.md` §3)
   - `Unit` (seeded rows via a second manual revision)
   - `Recipe`
   - `RecipeIngredient`
   - `PreparationStep`
3. `alembic init alembic`. Update `alembic/env.py` to:
   - Import `Settings`; build sync URL for Alembic itself (`psycopg`) and async URL at runtime.
   - Import `Base` and `app.models.*` so metadata is populated.
   - `target_metadata = Base.metadata`.
4. `poetry run alembic revision --autogenerate -m "initial schema"`. Review the diff — explicitly verify:
   - `numeric(8,3)` on quantities
   - `boolean` (not `int`) on `is_private`, `is_deleted`
   - `timestamptz` on timestamps
   - FK indexes on `recipe_id`, `user_id`
5. Add a second manual revision `seed_units` inserting canonical units via `op.bulk_insert` (`cup, c, imperial`, `gram, g, metric`, `tbsp, tbsp`, `tsp, tsp`, `oz, oz`, `lb, lb`, `ml, ml`, `l, l`).
6. Apply: `docker compose up -d` → `poetry run alembic upgrade head`. Confirm with `psql` or TablePlus: 5 tables; `unit` populated.

**Verification:** drop & recreate DB, run migrations from scratch, same result. Commit `poetry.lock`.

---

## Step 4 — Auth backend (register / login / logout / me)

**Goal:** All `auth/*` endpoints work, `Set-Cookie` headers correct per env, decoded JWT round-trips through `GET /auth/user`.

1. `app/services/security.py`: `hash_password` (passlib bcrypt), `verify_password`, `create_access_token(sub=user_id, expires_delta=...)`, `decode_access_token` raising `HTTPException(401)` on failure.
2. `app/schemas/auth.py`: separate input and output Pydantic models. `RegisterIn`, `LoginIn`, `UserOut`, `UserUpdateIn`. Output schemas never include `password_hash`.
3. `app/api/deps.py::get_current_user`: reads `token` cookie via `Request.cookies`, decodes JWT, queries user, returns ORM `User`. Raise **401** for missing/invalid (not 403).
4. `app/api/routes/auth.py`:
   - `POST /auth/register` — 409 on duplicate `username` or `email`; create user; issue JWT; set cookie; return `UserOut`.
   - `POST /auth/login` — verify password; issue JWT; set cookie; return `UserOut`.
   - `POST /auth/logout` — same `Set-Cookie` shape but `Max-Age=0`.
   - `GET /auth/user` — `Depends(get_current_user)`.
   - `PUT /auth/user`, `PUT /auth/email`, `PUT /auth/password` — stub with `{message: "..."}` so the contract exists; full behavior can be body-filling work.
5. `app/services/cookies.py`: build the `Set-Cookie` value per env.
   - `ENV=dev`: no `Domain`, no `Secure`.
   - `ENV=prod`: `Domain=.ourrecipeapp.com; Secure; SameSite=Lax; HttpOnly; Path=/; Max-Age=86400`.
6. Tests in `backend/tests/test_auth.py` using `httpx.AsyncClient(app=app, base_url="http://test")`:
   - Register success → 201, `Set-Cookie` present, attributes correct for env.
   - Register duplicate username → 409.
   - Register duplicate email → 409.
   - Login wrong password → 401.
   - `GET /auth/user` without cookie → 401.
   - `GET /auth/user` with cookie → 200; assert `password_hash` **not** in response.
   - Logout clears cookie.
7. `poetry run pytest tests/test_auth.py -v`. Then full check: `ruff check . && ruff format --check . && mypy . && pytest`.

**Verification:** end-to-end register → login → `/auth/user` → logout, all pass with cookies.

---

## Step 5 — Recipe CRUD backend

**Goal:** All `/recipes/*` and `/users/{id}/recipes` endpoints behave per `architecture_document.md` §4 and §7.

1. `app/schemas/recipe.py`:
   - `RecipeIn` (POST/PUT body), with `ingredients: list[IngredientIn]` and `preparation_steps: list[StepIn]` required on POST.
   - `RecipeListItem` for `/recipes` and `/users/{id}/recipes` — **no** nested ingredients/steps to keep list payload small.
   - `RecipeDetail` with nested `ingredients: list[IngredientOut]`, `preparation_steps: list[StepOut]`.
   - `IngredientIn`, `StepIn`.
2. `app/services/recipes.py` (keep routes thin):
   - `create_recipe(session, user_id, payload)` — single `async with session.begin():` block; insert Recipe, bulk insert ingredients/steps with explicit `sort_order` / `step_number`.
   - `update_recipe(session, recipe_id, user_id, payload)` — verify ownership; inside the transaction: `DELETE` from `recipe_ingredients` and `preparation_steps` for that recipe, then bulk insert fresh. **Full replace, no diff.**
   - `soft_delete_recipe(session, recipe_id, user_id)` — sets `is_deleted = True`.
   - `list_recipes(session, page, limit, q, current_user)`.
   - `get_recipe_detail(session, recipe_id, current_user)`.
3. Pagination utility: clamp `page ≥ 1`, `limit ≤ 50` silently. Response shape:

   ```python
   {"items": [...], "total": int, "page": int, "limit": int, "total_pages": int}
   ```
4. Search: `Recipe.title ILIKE '%q%' OR Recipe.description ILIKE '%q%'`. Cap `q` length server-side at 256 chars to bound query cost.
5. Single helper `assert_can_view(recipe, current_user)`:
   - Soft-deleted → 404.
   - Private + not owner → 403 (per arch literal wording).
   - Otherwise → allow.
6. Image-URL guard: Pydantic `field_validator` on `RecipeIn.image_url` — parse URL with `urllib.parse`, require `netloc == "res.cloudinary.com"` and path begins with `/<cloud_name>/`. Otherwise 422.
7. Tests in `backend/tests/test_recipes.py` covering each row of arch §4 + §7:
   - Public list, paginated boundaries (`page=0`, `page=99`, `limit=99`).
   - Search hits and short `q` cap.
   - Detail public OK; detail soft-deleted 404; detail private-not-owner 403.
   - POST auth required.
   - PUT requires owner; PUT full-replace behavior — assert ingredient IDs change, old IDs gone, array size reflects payload exactly.
   - DELETE soft delete: still in DB with `is_deleted = True`, returns 404 on subsequent GET.
   - `/users/{id}/recipes` self/public access rules.
   - Image URL guard: non-Cloudinary URL → 422.
8. Add `openapi-spec-validator` dev dep; quick smoke: validate `/openapi.json` is spec-valid.

**Verification:** full `pytest` + `ruff` + `mypy` green. `/openapi.json` validates.

---

## Step 6 — Frontend scaffolding

`corepack enable && corepack prepare pnpm@latest --activate`. `pnpm create next-app@16 frontend --typescript --tailwind --eslint --app --src-dir=false`. Replace `postcss.config.mjs`, `app/globals.css`, install `@tailwindcss/postcss`, `@heroicons/react`, `zustand`, `openapi-typescript`, `openapi-fetch`. Configure ESLint flat config + Prettier. Placeholder `app/page.tsx` reads `NEXT_PUBLIC_API_URL` and hits `/api/health`.

## Step 7 — Frontend ↔ backend glue

`lib/api.ts` exports a typed `openapi-fetch` client with `baseUrl: process.env.NEXT_PUBLIC_API_URL`. `lib/fetcher.ts` wraps it with `credentials: "include"` injected by default. `lib/serverApi.ts` is the SSR variant: reads `cookies()` from `next/headers` and forwards the `token` cookie in headers manually (per arch §5 + `AGENTS.md` SSR-cookie gotcha). FastAPI CORS uses `CORS_ORIGINS` env — comma-separated **exact origins** only (wildcard `*` is forbidden when `allow_credentials=True`).

## Step 8 — OpenAPI codegen

Wire `pnpm run codegen` to fetch backend `/openapi.json` → write `frontend/openapi.json` → run `openapi-typescript` → emit `types/api.d.ts`. **Commit `types/api.d.ts`**; **gitignore `frontend/openapi.json`**. CI can run `pnpm run codegen && git diff --exit-code types/api.d.ts` to enforce regen discipline.

## Step 9 — Auth UI

`/auth/login` and `/auth/register` as Server Components rendering Client form components. `useAuthStore` (Zustand) holds `{ user: UserOut | null, initialized: boolean }`. Root layout calls `GET /auth/user` server-side via `lib/serverApi.ts` once and seeds the store via a `StoreHydration` client component (`AGENTS.md` Zustand SSR-hydration gotcha). `middleware.ts` matcher for `/recipes/create` and `/auth/profile` redirects to `/auth/login?redirect=...` when no `token` cookie present.

## Step 10 — Recipe frontend

- `/` (`app/page.tsx`, SSR): paginated list + search input updating `?q=` and `?page=`.
- `/recipes/[id]` (SSR): full detail with `@media print` stylesheet.
- `/recipes/create` (Client): dynamic `ingredients[]` + `preparation_steps[]` state; Cloudinary unsigned upload widget for image.
- `/recipes/[id]/edit` (Client): load detail into local state; `PUT` with full arrays.
- `/auth/profile`: Client sections (Profile / Account / My Recipes). "My Recipes" calls `GET /users/{me}/recipes`.

## Step 11 — Cloudinary upload

Free Cloudinary account + unsigned preset `recipe-app-mvp`. `UploadButton` Client component: `<input type="file">` → `fetch("https://api.cloudinary.com/v1_1/<cloud_name>/image/upload", { method: "POST", body: formData({ file, upload_preset }) })` → store `secure_url` in recipe form. **Harden pre-public-launch**: switch to auth-gated upload signature; the unsigned preset allows anyone with the cloud name to upload to your bucket.

## Step 12 — UI polish

Heroicons per arch §8. Sidebar collapses to hamburger drawer on mobile; grid `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`. Sentry via `@sentry/nextjs` with `withSentryConfig` in `next.config.mjs`.

## Step 13 — Deployment

- Buy `ourrecipeapp.com` (Porkbun / Cloudflare Registrar / Namecheap).
- Backend on Railway: Nixpacks auto-detects Poetry; add `Procfile` with `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Env vars: `DATABASE_URL` (Neon), `JWT_SECRET`, `ENV=prod`, `CORS_ORIGINS=https://app.ourrecipeapp.com`.
- DB on Neon free tier; copy pooled connection string into Railway's `DATABASE_URL`.
- Frontend on Vercel: root `frontend/`, `NEXT_PUBLIC_API_URL=https://api.ourrecipeapp.com` (must be present at **build** time — it's bundled into the client).
- DNS: `app.ourrecipeapp.com` → Vercel CNAME, `api.ourrecipeapp.com` → Railway CNAME; SSL auto-provisioned.
- Final smoke: register, login, create + edit + delete a recipe, view it, log out — over `https://`.

## Step 14 — Post-MVP stubs to leave room for

Document deferred items in `README.md` so they're visible:

- Refresh tokens
- `IngredientCatalog` normalization + migration
- Rate limiting (`slowapi`) on `/auth/login`, `/auth/register`, `/auth/password`
- Recipe-print / shopping list (CSS-only)
- Private recipe sharing one-to-one
- Recipe-PUT smart-merge mode alongside full-replace (backward-compatible shape)
