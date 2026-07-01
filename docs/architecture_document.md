# Our Recipe App — Architecture Document

**Version:** 1.0 (MVP Draft)  
**Date:** June 29, 2026  
**Status:** Architecture draft for MVP development

---

## 1. Technology Stack

| Component | Technology | Hosting |
|-----------|------------|---------|
| Frontend | Nuxt 4 + Tailwind CSS v4 (Vite plugin) | Vercel (Hobby tier, $0/mo) |
| Backend | FastAPI (Python) + Poetry | Railway ($0-5/mo) |
| Database | PostgreSQL 16 | Neon (Free tier, $0/mo) |
| Image Storage | Cloudinary (unsigned uploads for MVP) | Cloudinary (Free tier, $0/mo) |
| Error Tracking | Sentry | Sentry (Free tier, $0/mo) |
| Version Control | GitHub | Free |
| Custom Domain | Registrar TBD | ~$12/yr |
| **Total monthly cost** | | **$0-5/mo + ~$1/mo amortized domain** |

**Monorepo structure:** Single GitHub repository with `backend/` and `frontend/` directories.

**Why a custom domain is required (not optional):** See Section 2. The auth cookie strategy depends on the frontend and backend sharing one registrable domain.

---

## 2. Deployment & Domain Architecture

### Domain Layout

A single registered domain (referred to below as `<root-domain>`, e.g. `ourrecipeapp.com`) with two subdomains:

| Host | Points to | Serves |
|------|-----------|--------|
| `app.<root-domain>` (or apex `<root-domain>`) | Vercel | Nuxt frontend |
| `api.<root-domain>` | Railway | FastAPI backend |

### Why This Matters — Cross-Site Cookie Problem

The authentication design uses a JWT stored in an `HttpOnly` cookie (see Section 5). Browsers only send such a cookie on requests the browser considers **same-site**. "Same-site" is decided by the **registrable domain** (eTLD+1), *not* the full hostname and *not* the port.

- `myapp.vercel.app` + `myapp.railway.app` → **different sites** → cookie is NOT sent on API calls (auth silently breaks).
- `app.<root-domain>` + `api.<root-domain>` → **same site** (shared `<root-domain>`) → cookie IS sent. ✅

The cookie is issued by the backend scoped to the parent domain:

```
Set-Cookie: token=<JWT>; HttpOnly; Secure; SameSite=Lax; Domain=.<root-domain>; Path=/; Max-Age=86400
```

`Domain=.<root-domain>` makes the cookie valid for all subdomains, so both `app.` and `api.` share it.

### CORS Requirement

Even though the two subdomains are same-site, they are still **cross-origin** (different hostnames). The backend must return explicit CORS headers — a wildcard `*` is not allowed when credentials are involved:

```python
# FastAPI CORS middleware (backend)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.<root-domain>"],  # exact origin, NOT "*"
    allow_credentials=True,                        # required to send cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

And the frontend must opt in to sending credentials on every request (`credentials: "include"` / Nuxt `useFetch` with `credentials: "include"`).


---

## 3. Data Model

### Entity-Relationship Diagram

```
User
  id              PK
  username        unique, login credential
  email           unique
  display_name    nullable
  about           nullable (bio)
  avatar_url      nullable (Cloudinary URL)
  password_hash   bcrypt hash
  created_at      timestamp
  updated_at      timestamp

Recipe
  id                  PK
  user_id             FK -> User
  title               text
  description         text
  image_url           nullable (Cloudinary URL)
  prep_time_minutes   nullable (whole number)
  cook_time_minutes   nullable (whole number)
  servings            nullable (whole number)
  notes               nullable
  tags                text (comma-separated for MVP)
  is_private          boolean (default false)
  is_deleted          boolean (soft delete)
  created_at          timestamp
  updated_at          timestamp

RecipeIngredients
  id                    PK
  recipe_id             FK -> Recipe
  name                  text (free-text for MVP)
  catalog_ingredient_id FK -> IngredientCatalog, nullable (post-MVP normalization)
  quantity              numeric(8, 3), nullable (for calculations/conversion)
  quantity_text         varchar(50), nullable (for display: "1/2", "to taste")
  unit_id               FK -> Unit, nullable
  substitution_notes    text, nullable
  sort_order            integer

PreparationSteps
  id              PK
  recipe_id       FK -> Recipe
  step_number     integer
  instructions    text

Unit
  id              PK
  name            text (e.g. "cup", "gram")
  abbreviation    text (e.g. "c", "g")
  system          text ("metric" or "imperial")
```

### Quantity Dropdown Options (Frontend)

| Number | Options |
|--------|---------|
| 1 | 1, 1 1/4, 1 1/3, 1 1/2, 1 2/3, 1 3/4 |
| 2 | 2, 2 1/4, 2 1/3, 2 1/2, 2 2/3, 2 3/4 |
| 3 | 3, 3 1/4, 3 1/3, 3 1/2, 3 2/3, 3 3/4 |
| 4 | 4, 4 1/2 |
| 5 | 5, 5 1/2 |
| Text | to taste, as needed, a dash |
| Custom | free text input |

### Ingredient Name Decision

**MVP:** Free-text `name` field on `RecipeIngredients`. Users type ingredient names per-recipe.

**Post-MVP:** A shared `IngredientCatalog` table with unique names. `RecipeIngredients` will reference catalog entries via `catalog_ingredient_id` (nullable FK already in schema).

| Aspect | MVP (free-text) | Post-MVP (normalized) |
|--------|-----------------|----------------------|
| Build time | approx less than 1/2 hour | a few hours + migration |
| Consistency | User-dependent | Canonical names enforced |
| "Recipes with flour" query | `ILIKE '%flour%'` | Direct FK lookup |
| Migration path | N/A | Create catalog, migrate names, add FK |

---

## 4. API Endpoints

> **Base URL:** `https://api.<root-domain>` in production, `http://localhost:8000` in development.

### Auth Endpoints

**POST /auth/register** — Create account and auto-login

```
Request:
{
  "username": "thechef",
  "email": "james@example.com",
  "display_name": "James da Chef",     // optional, defaults to username
  "password": "securePassword123"
}

Response (201):
{ 
  "id": 1,
  "username": "thechef",
  "email": "james@example.com",
  "display_name": "James da Chef"
}
// Set-Cookie: token=<JWT>; HttpOnly; Secure; SameSite=Lax; Domain=.<root-domain>; Path=/; Max-Age=86400
```

Errors: 409 (username/email exists), 422 (validation).

---

**POST /auth/login** — Authenticate and set JWT cookie

```
Request:
{
  "username": "thechef",
  "password": "securePassword123"
}

Response (200):
{
  "id": 1,
  "username": "thechef",
  "email": "james@example.com",
  "display_name": "James da Chef",
  "avatar_url": "https://res.cloudinary.com/..."
}
// Set-Cookie: token=<JWT>; HttpOnly; Secure; SameSite=Lax; Domain=.<root-domain>; Path=/; Max-Age=86400
```

Errors: 401 (invalid credentials).

---

**POST /auth/logout** — Clear JWT cookie

```
Response (200):
{ "message": "Logged out" }
// Set-Cookie: token=; HttpOnly; Secure; SameSite=Lax; Domain=.<root-domain>; Path=/; Max-Age=0
```

---

**GET /auth/user** — Get current user profile (auth required)

```
Response (200):
{
  "id": 1,
  "username": "thechef",
  "email": "james@example.com",
  "display_name": "James da Chef", 
  "about": "Warms up a jar of spaghetti sauce like no one's business! Magnifique!",
  "avatar_url": "https://res.cloudinary.com/not-great-image.jpg"
}
```

Errors: 401 (no valid JWT).

---

**PUT /auth/user** — Update display name, bio, avatar (auth required)

```
Request:
{
  "display_name": "Chef James",
  "about": "Makes a mean tuna on toast!",
  "avatar_url": "https://res.cloudinary.com/new-avatar.jpg"
}

Response (200): { "message": "Profile updated" }
```

---

**PUT /auth/email** — Change email (requires current password)

```
Request:
{
  "email": "newemail@example.com",
  "current_password": "securePassword123"
}

Response (200): { "message": "Email updated" }
```

Errors: 401 (wrong password).

---

**PUT /auth/password** — Change password (requires current password)

```
Request:
{
  "current_password": "securePassword123",
  "new_password": "evenMoreSecurePassword456"
}

Response (200): { "message": "Password updated" }
```

Errors: 401 (wrong password).

---

### Recipe Endpoints

**GET /recipes** — List recipes (paginated, searchable)

```
Query: ?page=1&limit=20&q=cookies

Response (200):
{
  "items": [
    {
      "id": 1,
      "title": "Grandma's Monster Cookies",
      "description": "Freak'n huge, and are made with have oatmeal, M&Ms, AND chocolate chips!",
      "image_url": "https://res.cloudinary.com/monster-cookie.jpg",
      "prep_time_minutes": 40,
      "cook_time_minutes": 15,
      "servings": 12,
      "tags": "dessert, cookies",
      "is_private": false,
      "user": 
      { 
        "id": 1,
        "username": "thechef",
        "display_name": "James da Chef",
        "avatar_url": "..."
      },
      "created_at": "2026-06-23T12:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 20,
  "total_pages": 3
}
```

Access: No auth required. Returns public recipes (`is_private = false`). If authenticated, includes the current user's private recipes mixed in with results.

> **Pagination edge cases:** `?page=0` or negative page values are clamped to `page=1`. Requesting a page past the last (e.g. `?page=99` when only 3 pages exist) returns `items: []` with the same `total` and `total_pages` — not a 404. `?limit` values above `50` are silently clamped to `50`.

---

**GET /recipes/{id}** — Get recipe detail with ingredients + steps

```
Response (200):
{
  "id": 1,
  "title": "Grandma's Monster Cookies",
  "description": "Freak'n huge, and are made with have oatmeal, M&Ms, AND chocolate chips!",
  "image_url": "https://res.cloudinary.com/monster-cookie.jpg",
  "prep_time_minutes": 40,
  "cook_time_minutes": 15,
  "servings": 12,
  "notes": "Best served warm",
  "tags": "dessert, cookies",
  "is_private": false,
  "user": 
  {
    "id": 1,
    "username": "thechef",
    "display_name": "James da Chef",
    "avatar_url": "..."
  },
  "ingredients": [
    {
      "id": 1,
      "name": "Flour",
      "quantity": 2.5,
      "quantity_text": "2 1/2",
      "unit": 
      {
        "id": 1,
        "name": "cup",
        "abbreviation": "c"
      },
      "substitution_notes": null,
      "sort_order": 1
    },
    {
      "id": 2,
      "name": "Sugar",
      "quantity": 1.0,
      "quantity_text": "1",
      "unit": 
      { 
        "id": 1,
        "name": "cup",
        "abbreviation": "c"
      },
      "substitution_notes": "can use coconut sugar",
      "sort_order": 2
    }
  ],
  "preparation_steps": [
    {
      "step_number": 1,
      "instructions": "Preheat oven to 350F"
    },
    {
      "step_number": 2,
      "instructions": "Mix dry ingredients"
    }
  ],
  "created_at": "2026-06-23T12:00:00Z",
  "updated_at": "2026-06-23T14:00:00Z"
}
```

Access: No auth required for public recipes. Returns 403 if private and not the owner. Returns 404 if soft-deleted.

> **Image URL validation:** `Recipe.image_url` is validated on the server to ensure the host is `res.cloudinary.com` (and the path begins with `/<cloud_name>/`). This is a simple check for MVP. If, however, user-supplied URLs are ever accepted later, the same check prevents attackers from pointing the field at their own servers.

---

**POST /recipes** — Create recipe (auth required, owner)

```
Request:
{
  "title": "Grandma's Monster Cookies",
  "description": "Freak'n huge, and are made with have oatmeal, M&Ms, AND chocolate chips!",
  "image_url": "https://res.cloudinary.com/monster-cookie.jpg",
  "prep_time_minutes": 40,
  "cook_time_minutes": 15,
  "servings": 12,
  "notes": "Best served warm",
  "tags": "dessert, cookies",
  "is_private": false,
  "ingredients": [
    { 
      "name": "Flour",
      "quantity": 2.5,
      "quantity_text": "2 1/2",
      "unit_id": 1,
      "substitution_notes": null,
      "sort_order": 1
    },
    {
      "name": "Sugar",
      "quantity": 1.0,
      "quantity_text": "1",
      "unit_id": 1,
      "substitution_notes": "can use Stevia",
      "sort_order": 2
    }
  ],
  "preparation_steps": [
    { 
      "step_number": 1,
      "instructions": "Preheat oven to 350F"
    },
    {
      "step_number": 2,
      "instructions": "Mix ingredients"
    },
    {
      "step_number": 3,
      "instructions": "Bake for 15 minutes"
    }
  ]
}

Response (201): { "id": 42, "message": "Recipe created" }
```

All operations inside a database transaction. Errors: 401 (unauth), 422 (validation).

---

**PUT /recipes/{id}** — Update recipe (auth required, owner only)

```
Request: Same shape as POST /recipes (all fields optional for partial update)
Response (200): { "message": "Recipe updated" }
```

> **Contract:** `PUT /recipes/{id}` This will replace all ingredients and cooking instructions for the recipe. Importantly, it will also update any recipe fields.
The backend runs `DELETE` on existing rows for both child tables and re-inserts whatever the request contains, all inside a single transaction. 
**The frontend must hold the current state in client state and send the full ingredient + step arrays on every save** 
Any ingredient or step not in the payload is deleted server-side. 
The trade-off is it's simple and fast to implement, as well as predictable. A Drawback is a stale client tab can wipe unrelated changes if the user submits from it.

Errors: 401, 403 (not owner), 404 (not found).

> **Post-MVP, replace the full-replace with a smart merge:** Replace the "delete-then-insert" with a "diff-against-database" that accepts either with the current behavior, using a full-state payload (for backward compatibility), or an `operations` array (`{op: "update"|"delete"|"create", ...}`). 
Existing clients will continue to work as-is, or be modified with the new changes to work similar to new clients by sending smaller, safer payloads.

---

**DELETE /recipes/{id}** — Soft-delete recipe (auth required, owner only). Allowing data retrieval.

```
Response (200): { "message": "Recipe deleted" }
```

Errors: 401, 403, 404.

---

**GET /users/{id}/recipes** — List recipes by user

```
Query: ?page=1&limit=20
Response: Same shape as GET /recipes, filtered by user_id
```

Access rules:
- **Self-access and Public access** (user `{id}` matches the authenticated user): 
returns all of that user's non-deleted recipes, including private ones, as well as all public recipes in the system.
- **Public access** (no auth): returns only public (`is_private = false`) recipes.
- **Post-MVP access** allow one user's private recipes to be shared with other specific users.
---

### Endpoint Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | No | Create account + auto-login |
| POST | /auth/login | No | Login, set JWT cookie |
| POST | /auth/logout | No | Clear JWT cookie |
| GET | /auth/user | Yes | Get current user profile |
| PUT | /auth/user | Yes | Update name, bio, avatar |
| PUT | /auth/email | Yes | Update email (requires password) |
| PUT | /auth/password | Yes | Update password (requires current) |
| GET | /recipes | No | List recipes (paginated, searchable) |
| GET | /recipes/{id} | No | Get recipe detail with ingredients + steps |
| POST | /recipes | Yes | Create recipe |
| PUT | /recipes/{id} | Yes (owner) | Update recipe |
| DELETE | /recipes/{id} | Yes (owner) | Soft-delete recipe |
| GET | /users/{id}/recipes | No | List recipes by user |

---

### 4.1 Generated TypeScript Client (Frontend ↔ Backend Type Safety)

FastAPI auto-publishes an **OpenAPI 3** schema at `/openapi.json` on the live backend. The frontend generates its typed API client from this schema so that every request and response shape is enforced at TypeScript compile time on the frontend. This catches contract drift at PR review instead of in production.

**Workflow:**

| Step | Where | What |
|------|------|------|
| Backend serves `/openapi.json` | `http://localhost:8000/openapi.json` (dev), `https://api.<root-domain>/openapi.json` (prod) | Source of truth for the API contract |
| Generator runs in frontend | `frontend/openapi.json` (saved) | Snapshot fetched from the live backend |
| Spec transformed to TS | `pnpm run codegen` → `frontend/types/api.d.ts` | Generated types + client functions |
| Frontend imports the client | any `.ts/.vue` | `import { listRecipes } from "~/types/api"` (or wherever codegen emits) |

**Tooling:** [`openapi-typescript`](https://openfmt.dev/javascript/openapi-typescript/) for types plus [`openapi-fetch`](https://openfmt.dev/javascript/openapi-fetch/) for the runtime client gives fully-typed functions like `listRecipes({ query: { q: "cookies", page: 1, limit: 20 }, credentials: "include" })` with no manual DTOs to maintain.

**When to regenerate:** any time a Pydantic schema, request body, or response shape changes on the backend, run `pnpm run codegen`, review the diff in `types/api.d.ts`, commit it alongside the backend change. CI can fail the build if `types/api.d.ts` is out of date (cheap `pnpm run codegen && git diff --exit-code types/api.d.ts` check).

**Pros:** types are guaranteed-correct, no hand-written DTOs, fewer `any`s, review-time feedback when the contract changes.

**Cons:** ~15 min of one-time setup, plus regen discipline when endpoints change. The generator can occasionally produce awkward types for `oneOf`/`anyOf` shapes — hand-correction is rare but possible.

---

## 5. Authentication Flow

### Token Strategy

**Decision: Single JWT with 24-hour expiry.** No refresh tokens for MVP.

| Approach | Chosen? | Rationale |
|----------|---------|-----------|
| Single JWT (24h) | **MVP** | Simpler to implement. No `/auth/refresh` endpoint. No refresh token DB storage. |
| Refresh tokens | Post-MVP | Adds ~2 days of work for no meaningful benefit in a demo context. |

### Cookie Configuration

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `HttpOnly` | yes | JS cannot read the token (XSS protection) |
| `Secure` | yes | HTTPS only |
| `SameSite` | `Lax` | Works across subdomains of one registrable domain |
| `Domain` | `.<root-domain>` | Shared between `app.` and `api.` subdomains |
| `Path` | `/` | Sent for all routes |
| `Max-Age` | `86400` | 24-hour expiry |

> **Local dev:** On `localhost`, omit `Domain` and `Secure` (browsers reject `Secure` cookies on `http://localhost` in some cases; and `localhost` cannot have a `Domain` attribute set to a real domain). Use environment-based cookie settings: `Secure` + `Domain` in production, neither locally.

### Auth State Detection

**Decision: Check `GET /auth/user` on app mount + store result in Pinia.**

Flow:
1. App mounts -> calls `GET /auth/user` (with `credentials: "include"`)
2. If 200 -> user is logged in. Store user data in Pinia.
3. If 401 -> user is logged out. Show login/register links.
4. On route change -> check Pinia state. If protected route and no state -> redirect to `/auth/login`.

> **Nuxt SSR cookie-forwarding gotcha:** During server-side rendering, the Nuxt server (not the browser) calls the backend. The browser's cookie is NOT automatically attached to that server-to-server request. For any SSR page that needs the logged-in user, the incoming request's `Cookie` header must be **forwarded** into the `$fetch`/`useFetch` call. A common pattern is a composable that reads the request headers via `useRequestHeaders(["cookie"])` on the server and passes them along. Purely client-side calls (after hydration) send the cookie automatically.

### Redirect Behavior

| Scenario | Behavior |
|----------|----------|
| Login success | Redirect to `/` (home) |
| Register success | Auto-login + redirect to `/` |
| Logout | Clear cookie + redirect to `/` |
| Protected page (not logged in) | Redirect to `/auth/login?redirect=/recipes/create` |
| Login with redirect param | Redirect to original page |

### Rate Limiting (Post-MVP)

**Decision: Rate limiting is *post-MVP*.** Not in MVP scope. Will be added with `slowapi` (or equivalent) on `/auth/login`, `/auth/register`, and `/auth/password`, with a starting limit of `5/minute` per IP for login/register. Tracked separately because it adds middleware, tests, and a new config knob for negligible demo value before launch.

### JWT Signing

JWTs use **HS256** with a shared `JWT_SECRET` env var on the backend. Generate the secret once (`python -c "import secrets; print(secrets.token_urlsafe(64))"`) and store it as a Railway environment variable. **Never commit it.** Plan: rotate every 6 months as a maintenance task. The same secret is used to sign and verify because the backend is both issuer and verifier — asymmetric (RS256) keys are unnecessary overhead for MVP.

### Logging (MVP)

Backend logs to `stdout` in JSON format via a `loguru` JSON sink; Railway captures `stdout` automatically and exposes a log viewer in the dashboard — no separate log aggregator is in MVP scope. The frontend relies on Sentry for browser-side errors; routine console output is not persisted. POST/GET/PUT/DELETE request lines are logged at info level; exceptions are logged at error level and (where configured) forwarded to Sentry.

---

## 6. Frontend Routes (Nuxt File-based)

```
/                           Recipe list (SSR)
/auth/login                 Login form (dedicated page)
/auth/register              Registration form (dedicated page)
/auth/profile               User profile + My Recipes + settings (protected)
/recipes/create             New recipe form (protected)
/recipes/[id]               Recipe detail (SSR, public)
/recipes/[id]/edit          Recipe edit form (protected, owner only)
```

> **Nuxt routing note:** Files in `pages/` map to routes automatically. `[id].vue` is a dynamic segment (access via `useRoute().params.id`). Protect routes with route middleware (`definePageMeta({ middleware: "auth" })`) that checks the Pinia auth state and redirects if absent.

### Design Decisions

**Login:** Dedicated page (not modal). Clean URLs, simpler SSR handling, straightforward redirect flow. Register is also a dedicated page with cross-links.

**Profile settings:** Everything unified under `/auth/profile`, organized in sections:
- Profile picture + display name + bio
- Account settings (email, password) — inline expandable forms
- My Recipes list

---

## 7. Recipe Visibility & Sharing

### Private Recipe Model

The `Recipe` table includes an `is_private` boolean (default false). Standard in recipe apps for draft/saving workflows.

### Access Rules

| Scenario | Behavior |
|----------|----------|
| Anyone (no auth) views recipe | Can see public recipes only |
| Anyone (no auth) views recipe list | Sees only public recipes |
| Owner views own recipe | Can see regardless of `is_private` |
| Owner views recipe list | Sees all own recipes + all public recipes from others |
| Owner edits recipe | Can toggle `is_private` on own recipes |

### Private Recipe UI Marking

The owner's private recipes appear mixed in with public results on the recipe list, visually distinguished by a **[Private]** tag (Heroicon: LockIcon) on the recipe card. The owner's public recipes appear identical to any other user's public recipes — no special marking.

---

## 8. Frontend Layout

### Layout Structure

```
+--------------------------------------------------+
|  Header: [App Logo] Our Recipe App               |
|         "Cook, Share, and Discover"              |
+-----------+--------------------------------------+
|           |                                       |
| Sidebar   |  Main Content Area                    |
|           |                                       |
| [mag]     |  <router-view />                      |
| [home]    |  Heroicon reference:                  |
| [user]    |  mag  = MagnifyingGlassIcon           |
| [pencil]  |  home = HomeIcon                      |
|           |  user = UserIcon                      |
| (when logged in):                                 |
| [user]    |  pencil = PencilSquareIcon            |
| [plus]    |  plus  = PlusCircleIcon               |
| [arrow]   |  arrow = ArrowLeftOnRectangleIcon     |
|           |                                       |
+-----------+--------------------------------------+
|  Footer: (copyright, links)                       |
+--------------------------------------------------+
```

### Sidebar Items by Auth State

| Auth State | Items | Heroicons |
|------------|-------|-----------|
| Logged out | Search, Home, Login, Register | MagnifyingGlassIcon, HomeIcon, UserIcon, PencilSquareIcon |
| Logged in | Search, Home, Profile, New Recipe, Logout | MagnifyingGlassIcon, HomeIcon, UserCircleIcon, PlusCircleIcon, ArrowLeftOnRectangleIcon |

> **Heroicons in Nuxt:** Use the `@heroicons/vue` package (`pnpm add @heroicons/vue`). Import icons as Vue components, e.g. `import { HomeIcon } from "@heroicons/vue/24/outline"`.

### Mobile Responsiveness

**Decision: Include basic mobile responsiveness in MVP (~2-3 hours).**

- Sidebar collapses to hamburger drawer on mobile
- Content stacks vertically
- Card grid: `grid-cols-1` (mobile) / `md:grid-cols-2` (tablet) / `lg:grid-cols-3` (desktop)
- No separate mobile version — same app, responsive CSS

---

## 9. Ingredient UI

### Ingredient Input (MVP)

Dynamic list with add/remove buttons using Vue 3 reactive arrays + `v-for`:

- Each row: name (text input), quantity (dropdown), unit (dropdown), substitution notes (text, optional), remove button
- "Add Ingredient" button appends a new empty row
- Backend accepts the full `ingredients` array in `POST /recipes` and `PUT /recipes/{id}`

> This is a standard Vue 3 reactive-array pattern: a `ref([])` plus `v-for` plus push/splice for add/remove. No Nuxt-specific knowledge required here.

### Shopping List (Post-MVP, UI Only)

No backend changes needed. Derived from the `RecipeIngredients` table:
- Full recipe print: CSS `@media print` stylesheet on the recipe detail page
- Shopping list: Filter to display only name + quantity_text + unit, rendered in a compact print-friendly layout

---

## 10. Data Flow — Key Operations

### Recipe Creation with Image

1. User fills out recipe form (title, description, ingredients, steps, etc.)
2. Image: user selects a file -> uploaded directly to Cloudinary (unsigned upload with `upload_preset`) -> Cloudinary returns a URL
3. User submits -> browser sends `POST /recipes` (with `credentials: "include"`) including the Cloudinary URL and nested ingredients/steps arrays
4. Backend opens a DB transaction -> creates Recipe -> inserts RecipeIngredients -> inserts PreparationSteps -> commits
5. Backend returns 201 with the new recipe ID

### Authentication Flow

1. User submits login form -> `POST /auth/login` with username + password
2. Backend validates credentials -> generates signed JWT -> returns `Set-Cookie` (HttpOnly, Secure, SameSite=Lax, `Domain=.<root-domain>`, 24h)
3. On next load, frontend calls `GET /auth/user` (cookie sent automatically client-side; forwarded manually during SSR) -> if 200, store user in Pinia; if 401, show logged-out UI
4. On logout -> `POST /auth/logout` -> backend clears cookie -> frontend redirects to home

---

## 11. Frontend Setup — Nuxt 4 + Tailwind CSS v4 (Vite Plugin)

Tailwind CSS v4 uses a **Vite-plugin-first** setup, not the legacy `@nuxtjs/tailwindcss` module (which targets v3 and can conflict with v4).

**1. Install:**
```bash
pnpm add tailwindcss @tailwindcss/vite
```

**2. Register the Vite plugin in `nuxt.config.ts`:**
```ts
import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  css: ["~/assets/css/main.css"],
  vite: {
    plugins: [tailwindcss()],
  },
});
```

**3. Import Tailwind in `assets/css/main.css`:**
```css
@import "tailwindcss";

/* Tailwind v4 uses CSS-first config. Customize the theme here with @theme: */
@theme {
  --color-brand: #c2410c;
}
```

**Key differences from Tailwind v3 (worth knowing):**
- No `tailwind.config.js` required — configuration is CSS-first via `@theme` and CSS variables.
- No `postcss.config.js` needed for Tailwind; the Vite plugin handles it.
- Content detection is automatic (no `content: [...]` globs to maintain).
- A single `@import "tailwindcss";` replaces the old `@tailwind base; @tailwind components; @tailwind utilities;` trio.

---

## 12. Implementation Notes for This Stack

Nuxt 4, FastAPI, async SQLAlchemy, Alembic, and the Docker surface area in this project each have a few conventions or gotchas that are easy to miss on first contact — independent of any developer's prior background. This section flags the ones most likely to surprise readers coming from non-Nuxt Vue, non-async Python, or non-Postgres relational databases.

### Nuxt 4 vs. Plain Vue 3
- **File-based routing:** `pages/` directory auto-generates routes. No manual router config.
- **Auto-imports:** Composables in `composables/`, components in `components/`, and Nuxt/Vue APIs are auto-imported — no explicit `import` needed in most files.
- **Data fetching:** Use `useFetch`/`useAsyncData` for SSR-aware fetching; `$fetch` for client-side/event-handler calls. Authed calls must set `credentials: "include"`.
- **State:** Pinia (`@pinia/nuxt`) for auth/user state. `useState` exists for lightweight SSR-safe state, but Pinia is clearer for long-lived app state like the current user.
- **Middleware:** Route middleware in `middleware/` plus `definePageMeta({ middleware: "auth" })` guards protected pages.
- **SSR cookie forwarding:** This is the single biggest Nuxt-specific pitfall in this codebase; see the gotcha note in §5.

### FastAPI Conventions
- **Async everywhere:** Endpoints are `async def`. The async SQLAlchemy session and the `asyncpg` driver are first-party; mixing sync code in the request path blocks the event loop.
- **Pydantic v2 models:** Request/response validation through Pydantic schemas — analogous to typed DTOs. Keep separate schemas for input vs output so internal-only fields can't leak back to clients.
- **Dependency injection:** `Depends(...)` provides the DB session and the current user (decoded from the JWT cookie) to endpoints; no global request context.
- **Project tooling:** Poetry for dependencies; commit `poetry.lock`. Use `ruff` (lint + format) and `mypy` for static types — both are standard Python tooling and catch the categories of bug the rest of this stack cannot.
- **Migrations:** Alembic for migrations; autogenerate from SQLAlchemy models and review the diff before committing.

### PostgreSQL
- **Identity columns:** `BIGINT GENERATED ALWAYS AS IDENTITY` (or `SERIAL`).
- **Types:** real `boolean`, `text` (no length penalty vs `varchar`), `timestamptz` for timestamps, `numeric(8,3)` for quantities (allows up to 99999.999; the MVP quantity dropdown caps at 5/8 so this is comfortably over-provisioned).
- **Search:** `ILIKE` for case-insensitive matching (used by `GET /recipes?q=`).
- **Logic in the application layer:** Business rules live in Python/FastAPI. Schema changes go through Alembic migrations.
- **No `GO` batch separators, no `BEGIN TRAN` boilerplates:** transactions are explicit and methods-based (`async with session.begin(): ...`).

### Docker Scope
- **Scope for MVP is small:** Docker runs only PostgreSQL locally via `docker-compose.yml` (a `postgres` service for dev and a `postgres-test` service for tests). The application itself is not containerized for MVP.
- **Commands in practice:** `docker compose up -d`, `docker compose down`, `docker compose logs postgres`. That covers the runtime surface area needed for local development.
- **Railway does not require a custom Dockerfile:** it builds the backend with Nixpacks. Use a `Procfile` (or `railway.json`) to declare the start command — see §1 and the Procfile discussion in earlier planning.

---

