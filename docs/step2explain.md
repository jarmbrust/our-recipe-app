# Step 2 — Backend skeleton (FastAPI + Poetry) — elaborated

This walks through every action in **Step 2** of `docs/dev-steps_1-14.md:49-111`, explaining the _what_ and _why_ of each move so you can execute it confidently on a fresh `backend/` directory. Commands assume your shell is in the repo root unless noted.

---

## 0. Prerequisites

Before you start, confirm:

- Python 3.14 is installed locally (`python3.14 --version`). Poetry will use this interpreter to spin up the virtualenv.
- Poetry is installed (`poetry --version`). If missing: `curl -sSL https://install.python-poetry.org | python3 -`.
- Docker Postgres from Step 1 is running (`docker compose ps`) so the app has a database to talk to even though we won't connect yet in this step.

You'll also produce a `.env` file (gitignored) at the end so `pydantic-settings` can read secrets without code changes.

---

## 1. Initialize Poetry in `backend/`

**Actions**

- `cd backend`
- `poetry init -n` — creates a minimal `pyproject.toml` with no interactive prompts (`-n` = non-interactive).
- `poetry env use 3.14` — pins the project's virtualenv to Python 3.14.

**Why this order**
Init first so `pyproject.toml` exists, _then_ pin the interpreter so subsequent `poetry add` happens against 3.14. Doing it the other way leaves the default interpreter selected until the first `add`.

**Gotcha**
`poetry env use` only writes a `python` directive into `pyproject.toml` and configures the shell. If the venv already exists from a previous run, run `poetry env remove python3.14 && poetry env use 3.14` to force a fresh one.

---

## 2. Install runtime dependencies

Single batch via `poetry add` (one transaction, one lock resolve):

```
poetry add \
  fastapi[standard] \
  uvicorn[standard] \
  pydantic[email] \
  pydantic-settings \
  sqlalchemy[asyncio] \
  asyncpg \
  alembic \
  pyjwt \
  passlib[bcrypt] \
  python-multipart \
  loguru
```

**Per-package rationale**

- `fastapi[standard]` — pulls Starlette + `fastapi-cli` extras (form parsing, etc.).
- `uvicorn[standard]` — adds `watchfiles` and `websockets` so `--reload` works and websockets are available later.
- `pydantic[email]` — installs `email-validator`, required for any `EmailStr` field in schemas.
- `pydantic-settings` — env-driven `Settings` class (`app/config.py`).
- `sqlalchemy[asyncio]` — SQLAlchemy 2.x with the `async` extra for `AsyncSession`, `create_async_engine`.
- `asyncpg` — fastest async Postgres driver. Use it at runtime; Alembic itself can still use sync `psycopg` for migrations.
- `alembic` — migrations (Step 3 wires it up).
- `pyjwt` — JWT encode/decode. Plain `jwt` API, no FastAPI-specific helpers.
- `passlib[bcrypt]` — password hashing for `User.password_hash`.
- `python-multipart` — required for FastAPI form/file parsing; without it, multipart endpoints 500.
- `loguru` — JSON-to-stdout logger for Railway capture.

**Caveat on `pyjwt` vs `python-jose`**: `AGENTS.md` doesn't pin one; `pyjwt` is preferred because `python-jose` is unmaintained. The dev-steps picks `pyjwt` correctly.

---

## 3. Install development dependencies

```
poetry add --group dev \
  pytest \
  pytest-asyncio \
  httpx \
  ruff \
  mypy \
  freezegun
```

- `pytest` — test runner.
- `pytest-asyncio` — required for the project's all-async FastAPI tests.
- `httpx` — used as the test `AsyncClient` (`AsyncClient(app=app, base_url="http://test")`).
- `ruff` — lint + format (single tool for both, replaces flake8/black/isort).
- `mypy` — static type checker (`strict = true` per config later).
- `freezegun` — for time-sensitive tests when JWT expiry logic lands.

**Add later (deferred):** `openapi-spec-validator` is called out in Step 5, not Step 2.

After this step, `backend/poetry.lock` is generated — **commit it** (`AGENTS.md` §Conventions).

---

## 4. Create the directory + file layout

Reproduce the tree at `docs/dev-steps_1-14.md:69-94`. Two practical notes:

- **Empty `__init__.py` files** are required so Python treats each folder as a package. Without them, `from app.api.deps import get_db` fails on import.
- **Skeleton module bodies** should be valid (no `pass`-only modules where logic is expected) so `mypy --strict` doesn't complain about unannotated functions. Each route module gets a `router = APIRouter()` instance even if empty.

Concrete files to create now (minimal stubs that `import` cleanly):

| Path                                       | Minimum content needed                                        |
| ------------------------------------------ | ------------------------------------------------------------- |
| `app/__init__.py`                          | empty                                                         |
| `app/main.py`                              | `FastAPI()` app, CORS setup, include router; see §6 below     |
| `app/config.py`                            | `Settings(BaseSettings)` class; see §5 below                  |
| `app/api/__init__.py`                      | empty                                                         |
| `app/api/deps.py`                          | placeholder `get_db()` and `get_current_user()`; see §8 below |
| `app/api/routes/__init__.py`               | empty                                                         |
| `app/api/routes/health.py`                 | `GET /health` returning version string                        |
| `app/db/__init__.py`                       | empty                                                         |
| `app/db/base.py`                           | `DeclarativeBase` subclass; see §7 hint                       |
| `app/db/session.py`                        | async engine, sessionmaker, `get_db()`; see §7                |
| `alembic/env.py`, `alembic/script.py.mako` | from `alembic init alembic` (run in Step 3, not Step 2)       |
| `alembic.ini`                              | from `alembic init alembic`                                   |

---

```BASH
  Files created (11):
  - backend/app/__init__.py, backend/app/api/__init__.py, backend/app/api/routes/__init__.py, backend/app/db/__init__.py — package markers
  - backend/app/config.py — Settings with NoDecode + BeforeValidator for CSV CORS_ORIGINS (pydantic-settings v2 idiom)
  - backend/app/main.py — FastAPI app, CORS, loguru → JSON stdout
  - backend/app/api/deps.py — re-exports get_db, placeholder get_current_user
  - backend/app/api/routes/health.py — /health returning status + version + env
  - backend/app/db/base.py — DeclarativeBase
  - backend/app/db/session.py — async engine + sessionmaker + get_db (AsyncIterator per ruff UP043)
  - backend/.env — gitignored
  File edited (1):
  - backend/pyproject.toml — appended [tool.ruff], [tool.ruff.lint], [tool.ruff.format], [tool.mypy], [tool.pytest.ini_options]
```

## 5. `app/config.py` — typed settings

**Actions**: define a `Settings(BaseSettings)` class with these fields:

| Field                 | Type                     | Default   | Source                                          |
| --------------------- | ------------------------ | --------- | ----------------------------------------------- |
| `DATABASE_URL`        | `str`                    | —         | required env var                                |
| `JWT_SECRET`          | `str`                    | —         | required env var                                |
| `JWT_ALGORITHM`       | `str`                    | `"HS256"` | constant                                        |
| `JWT_EXPIRES_MINUTES` | `int`                    | `1440`    | (= 24h per `AGENTS.md` §Auth)                   |
| `ENV`                 | `Literal["dev", "prod"]` | `"dev"`   | env-driven                                      |
| `CORS_ORIGINS`        | `list[str]`              | `[]`      | parse comma-separated env via `BeforeValidator` |

**Why `pydantic-settings`** — you get type validation for free: a misconfigured env raises at startup, not at first request. `model_config = SettingsConfigEnv(env_file=".env", env_file_encoding="utf-8", extra="ignore")` is the standard incantation.

**CORS list parsing** — `pydantic-settings` reads `CORS_ORIGINS` as a plain string. Use a `field_validator` or `BeforeValidator` that splits on `","` and strips whitespace. The architectural gotcha (`AGENTS.md` §FastAPI) is that wildcard `*` doesn't compose with `allow_credentials=True`, so always pass exact origins.

Add a `settings = Settings()` module-level singleton so the rest of the app imports a ready-made object.

Add a `.env` at `backend/.env` matching the fields (gitignored), e.g.:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/recipes
JWT_SECRET=dev-only-change-me
ENV=dev
CORS_ORIGINS=http://localhost:3000
```

---

## 6. `app/main.py` — app factory + CORS + router mount

**Actions**

1. Construct `app = FastAPI(title="Recipe API", version="0.1.0")`.
2. Add `CORSMiddleware` reading `settings.CORS_ORIGINS`:
   - `allow_origins=settings.CORS_ORIGINS`
   - `allow_credentials=True`
   - `allow_methods=["*"]`
   - `allow_headers=["*"]`
3. Build `api_router = APIRouter(prefix="/api")`.
4. `api_router.include_router(health.router)` — wires `GET /api/health`.
5. `app.include_router(api_router)`.

**`/api/health` payload** — return a small JSON with `{"status": "ok", "version": app.version, "env": settings.ENV}` so the verification step (`docs/dev-steps_1-14.md:111`) has something to assert beyond a 200.

**Loguru hookup** — register `loguru` as the stdlib logging handler so `uvicorn`'s access logs flow through it:

```
from loguru import logger
import logging

logging.getLogger().handlers = [InterceptHandler()]
logger.configure(handlers=[{"sink": "stdout", "serialize": True}])
```

`serialize=True` produces the JSON Railway captures per `AGENTS.md` §Conventions.

---

## 7. `app/db/session.py` + `app/db/base.py`

**`db/base.py`** — `class Base(DeclarativeBase): pass`. SQLAlchemy 2.x typing helpers live here; models import `Base` directly.

**`db/session.py`**:

- `engine = create_async_engine(settings.DATABASE_URL, echo=(settings.ENV == "dev"))`.
- `AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)`.
- `async def get_db() -> AsyncGenerator[AsyncSession, None]:` that yields a session and closes it in `finally`.

**Why `expire_on_commit=False`** — after commit, attributes are expired by default, forcing a refetch. Disabling keeps ORM instances usable in route responses without an extra round-trip.

`app/api/deps.py::get_db` just re-exports `get_db` from `session.py` so routes import from `deps.py` (one stable import path).

---

## 8. `app/api/deps.py` — placeholders

For Step 2, the only required function is `get_db` (re-export). Add empty stubs that compile cleanly so Step 4 can fill them:

- `async def get_current_user(...) -> None: raise NotImplementedError`

This avoids an import-time error when other modules reference the symbol but isn't functional yet. No JWT logic in Step 2.

---

## 9. `pyproject.toml` tool config

Append three tool tables:

```
[tool.ruff]
line-length = 100
target-version = "py314"
# E = pycodestyle errors, F = pyflakes, W = warnings, I = isort,
# UP = pyupgrade, B = bugbear, SIM = simplify
lint.select = ["E", "F", "W", "I", "UP", "B", "SIM"]

[tool.ruff.format]
quote-style = "preserve"
```

```
[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]
python_version = "3.14"
```

**Notes**

- `quote-style = "preserve"` — important because FastAPI docstrings quote examples; auto-converting would churn diffs.
- `pydantic.mypy` plugin — required so `BaseSettings` and `BaseModel` fields are recognised as properly typed.
- `python_version` — without this, mypy assumes the lowest supported version and would flag 3.14 syntax.

**Suggested additions while you're here:**

- `[tool.pytest.ini_options]` with `asyncio_mode = "auto"` so `pytest-asyncio` doesn't require per-test `@pytest.mark.asyncio`. This unblocks Step 4's `test_auth.py`.
- `[tool.coverage.run]` + `[tool.coverage.report]` so coverage is collected even when you don't ask for it now.

---

## 10. Smoke-test commands

Run in this order from `backend/`:

1. **`poetry install`** — installs everything with the lockfile generated.
2. **`poetry run uvicorn app.main:app --reload`** — keep running; useful for verifying CORS logs.
3. In a second terminal:
   - `curl -i http://localhost:8000/docs` — expect `200 OK` (Swagger UI).
   - `curl -i http://localhost:8000/api/health` — expect `200 OK`, JSON body as defined in §6.
4. Stop the server and run the discipline chain from `AGENTS.md` §Conventions:
   - `poetry run ruff check .` → no findings.
   - `poetry run ruff format --check .` → no format diffs.
   - `poetry run mypy .` → success, no errors.

If any check fails, fix the _first_ line ruff reports (`SIM`/`UP` violations are the most common in a fresh tree) and rerun the chain.

---

## 11. Commit discipline

This step yields a small, reviewable commit:

- `backend/pyproject.toml` — runtime/dev deps and tool configs.
- `backend/poetry.lock` — **commit** per `AGENTS.md`.
- `backend/app/...` — minimal skeleton files; no logic yet.
- `backend/.env` — **gitignored**, never committed.

If a CI is wired in Step 1, the commit's CI run should execute the §10 discipline chain against `backend/` and that's the bar for merging Step 2.

---

## 12. What _not_ to do in Step 2

- Don't write models, schemas, or auth services — those are Steps 3-5.
- Don't run `alembic init` — Step 3 does that with models already present so autogenerate has metadata to diff against.
- Don't write tests yet — there are no behaviors to assert beyond `/api/health`, which is verified manually above.
- Don't pull in extra deps not on the list. Each `poetry add` after this one should map 1:1 to a real need in a later step.

---

## 13. Exit criteria for Step 2

You're done with Step 2 when **all** are true:

1. `poetry run uvicorn app.main:app --reload` boots without errors.
2. `GET /api/health` returns 200 with a JSON body including `env` reflecting your `ENV` setting.
3. `GET /docs` shows the Swagger UI with at least the `/api/health` operation listed.
4. `poetry run ruff check . && poetry run ruff format --check . && poetry run mypy .` exits clean.
5. `poetry.lock` is committed; `.env` is not.

When all five hold, tag this milestone (e.g. `git tag step-2-complete`) and proceed to Step 3 — the database layer.
