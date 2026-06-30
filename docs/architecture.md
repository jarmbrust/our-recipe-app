# Our Recipe App — Architecture Document

**Version:** 1.0 (MVP Draft)  
**Date:** June 23, 2026  
**Status:** Architecture draft for MVP development

---

## 1. Technology Stack

| Component | Technology | Hosting |
|-----------|------------|---------|
| Frontend | Nuxt 4 + Tailwind CSS v4 | Vercel (Hobby tier, $0/mo) |
| Backend | FastAPI (Python) + Poetry | Railway ($0-5/mo) |
| Database | PostgreSQL 16 | Neon (Free tier, $0/mo) |
| Image Storage | Cloudinary (unsigned uploads for MVP) | Cloudinary (Free tier, $0/mo) |
| Error Tracking | Sentry | Sentry (Free tier, $0/mo) |
| Version Control | GitHub | Free |
| **Total monthly cost** | | **$0-5/mo (hard cap $15/mo)** |

**Monorepo structure:** Single GitHub repository with `backend/` and `frontend/` directories.

---

## 2. Data Model

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
  quantity              numeric (4, 3), nullable (for calculations/conversion)
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
| Build time | ~10 minutes | ~2-3 hours + migration |
| Consistency | User-dependent | Canonical names enforced |
| "Recipes with flour" query | `ILIKE '%flour%'` | Direct FK lookup |
| Migration path | N/A | Create catalog, migrate names, add FK |

---

## 3. API Endpoints

### Auth Endpoints

**POST /auth/register** — Create account and auto-login

```
Request:
{
  "username": "jchef",
  "email": "james@example.com",
  "display_name": "James Chef",     // optional, defaults to username
  "password": "securePassword123"
}

Response (201):
{ "id": 1, "username": "jchef", "email": "james@example.com", "display_name": "James Chef" }
// Set-Cookie: token=<JWT>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400
```

Errors: 409 (username/email exists), 422 (validation).

---

**POST /auth/login** — Authenticate and set JWT cookie

```
Request:
{
  "username": "jchef",
  "password": "securePassword123"
}

Response (200):
{
  "id": 1, "username": "jchef", "email": "james@example.com",
  "display_name": "James Chef", "avatar_url": "https://res.cloudinary.com/..."
}
// Set-Cookie: token=<JWT>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400
```

Errors: 401 (invalid credentials).

---

**POST /auth/logout** — Clear JWT cookie

```
Response (200):
{ "message": "Logged out" }
// Set-Cookie: token=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0
```

---

**GET /auth/user** — Get current user profile (auth required)

```
Response (200):
{
  "id": 1, "username": "jchef", "email": "james@example.com",
  "display_name": "James Chef", "about": "Home cook and baker",
  "avatar_url": "https://res.cloudinary.com/..."
}
```

Errors: 401 (no valid JWT).

---

**PUT /auth/user** — Update display name, bio, avatar (auth required)

```
Request:
{
  "display_name": "Chef James",
  "about": "Professional baker turned home cook",
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
  "current_password": "oldPassword123"
}

Response (200): { "message": "Email updated" }
```

Errors: 401 (wrong password).

---

**PUT /auth/password** — Change password (requires current password)

```
Request:
{
  "current_password": "oldPassword123",
  "new_password": "newPassword456"
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
      "id": 1, "title": "Grandma's Cookies", "description": "A family favorite",
      "image_url": "https://res.cloudinary.com/...",
      "prep_time_minutes": 30, "cook_time_minutes": 15, "servings": 12,
      "tags": "dessert, cookies",
      "is_private": false,
      "user": { "id": 1, "username": "jchef", "display_name": "James Chef", "avatar_url": "..." },
      "created_at": "2026-06-23T12:00:00Z"
    }
  ],
  "total": 42, "page": 1, "limit": 20, "total_pages": 3
}
```

Access: No auth required. Returns public recipes (`is_private = false`). If authenticated, includes the current user's private recipes mixed in with results.

---

**GET /recipes/{id}** — Get recipe detail with ingredients + steps

```
Response (200):
{
  "id": 1, "title": "Grandma's Cookies", "description": "A family favorite",
  "image_url": "...", "prep_time_minutes": 30, "cook_time_minutes": 15,
  "servings": 12, "notes": "Best served warm", "tags": "dessert, cookies",
  "is_private": false,
  "user": { "id": 1, "username": "jchef", "display_name": "James Chef", "avatar_url": "..." },
  "ingredients": [
    { "id": 1, "name": "Flour", "quantity": 2.5, "quantity_text": "2 1/2",
      "unit": { "id": 1, "name": "cup", "abbreviation": "c" },
      "substitution_notes": null, "sort_order": 1 },
    { "id": 2, "name": "Sugar", "quantity": 1.0, "quantity_text": "1",
      "unit": { "id": 1, "name": "cup", "abbreviation": "c" },
      "substitution_notes": "can use coconut sugar", "sort_order": 2 }
  ],
  "preparation_steps": [
    { "step_number": 1, "instructions": "Preheat oven to 350F" },
    { "step_number": 2, "instructions": "Mix dry ingredients" }
  ],
  "created_at": "2026-06-23T12:00:00Z", "updated_at": "2026-06-23T14:00:00Z"
}
```

Access: No auth required for public recipes. Returns 403 if private and not the owner. Returns 404 if soft-deleted.

---

**POST /recipes** — Create recipe (auth required, owner)

```
Request:
{
  "title": "Grandma's Cookies",
  "description": "A family favorite",
  "image_url": "https://res.cloudinary.com/...",
  "prep_time_minutes": 30, "cook_time_minutes": 15, "servings": 12,
  "notes": "Best served warm", "tags": "dessert, cookies",
  "is_private": false,
  "ingredients": [
    { "name": "Flour", "quantity": 2.5, "quantity_text": "2 1/2",
      "unit_id": 1, "substitution_notes": null, "sort_order": 1 },
    { "name": "Sugar", "quantity": 1.0, "quantity_text": "1",
      "unit_id": 1, "substitution_notes": "can use coconut sugar", "sort_order": 2 }
  ],
  "preparation_steps": [
    { "step_number": 1, "instructions": "Preheat oven to 350F" },
    { "step_number": 2, "instructions": "Mix dry ingredients" },
    { "step_number": 3, "instructions": "Bake for 15 minutes" }
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

Errors: 401, 403 (not owner), 404 (not found).

---

**DELETE /recipes/{id}** — Soft-delete recipe (auth required, owner only)

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

No auth required. Returns only non-deleted, public recipes (plus the requesting user's own private recipes if authenticated).

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

## 4. Authentication Flow

### Token Strategy

**Decision: Single JWT with 24-hour expiry.** No refresh tokens for MVP.

| Approach | Chosen? | Rationale |
|----------|---------|-----------|
| Single JWT (24h) | **MVP** | Simpler to implement. No `/auth/refresh` endpoint. No refresh token DB storage. |
| Refresh tokens | Post-MVP | Adds ~2 days of work for no meaningful benefit in a demo context. |

### Auth State Detection

**Decision: Check `GET /auth/user` on app mount + store result in Pinia.**

Flow:
1. App mounts -> calls `GET /auth/user`
2. If 200 -> user is logged in. Store user data in Pinia.
3. If 401 -> user is logged out. Show login/register links.
4. On route change -> check Pinia state. If protected route and no state -> redirect to `/auth/login`.

### Redirect Behavior

| Scenario | Behavior |
|----------|----------|
| Login success | Redirect to `/` (home) |
| Register success | Auto-login + redirect to `/` |
| Logout | Clear cookie + redirect to `/` |
| Protected page (not logged in) | Redirect to `/auth/login?redirect=/recipes/create` |
| Login with redirect param | Redirect to original page |

---

## 5. Frontend Routes (Nuxt File-based)

```
/                           Recipe list (SSR)
/auth/login                 Login form (dedicated page)
/auth/register              Registration form (dedicated page)
/auth/profile               User profile + My Recipes + settings (protected)
/recipes/create             New recipe form (protected)
/recipes/[id]               Recipe detail (SSR, public)
/recipes/[id]/edit          Recipe edit form (protected, owner only)
```

### Design Decisions

**Login:** Dedicated page (not modal). Ensures clean URLs, simple SSR handling, and straightforward redirect flow. Register page is also a dedicated page with cross-links between the two.

**Profile settings:** Everything unified under `/auth/profile`, organized in sections:
- Profile picture + display name + bio
- Account settings (email, password) — inline expandable forms
- My Recipes list

---

## 6. Recipe Visibility & Sharing

### Private Recipe Model

The `Recipe` table includes an `is_private` boolean (default false). This is standard in recipe applications for draft/saving workflows.

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

## 7. Frontend Layout

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

### Mobile Responsiveness

**Decision: Include basic mobile responsiveness in MVP (~2-3 hours).**

- Sidebar collapses to hamburger drawer on mobile
- Content stacks vertically
- Card grid: `grid-cols-1` (mobile) / `md:grid-cols-2` (tablet) / `lg:grid-cols-3` (desktop)
- No separate mobile version — same app, responsive CSS

---

## 8. Ingredient UI

### Ingredient Input (MVP)

Dynamic list with add/remove buttons using Vue 3 reactive arrays + `v-for`:

- Each row: name (text input), quantity (dropdown), unit (dropdown), substitution notes (text, optional), remove button
- "Add Ingredient" button appends a new empty row
- Backend accepts the full `ingredients` array in `POST /recipes` and `PUT /recipes/{id}`

### Shopping List (Post-MVP, UI Only)

No backend changes needed. The shopping list is derived from the `RecipeIngredients` table:
- Full recipe print: CSS `@media print` stylesheet on the recipe detail page
- Shopping list: Filter to display only name + quantity_text + unit from the same ingredient data, rendered in a compact print-friendly layout

---

## 9. Data Flow — Key Operations

### Recipe Creation with Image

1. User fills out recipe form (title, description, ingredients, steps, etc.)
2. For the image: user selects a file -> uploaded directly to Cloudinary (unsigned upload with upload_preset) -> Cloudinary returns a URL
3. User submits the form -> browser sends POST /recipes with JSON body including the Cloudinary URL and nested ingredients/steps arrays
4. Backend opens a database transaction -> creates Recipe row -> inserts RecipeIngredients rows -> inserts PreparationSteps rows -> commits transaction
5. Backend returns 201 with the new recipe ID

### Authentication Flow

1. User submits login form -> POST /auth/login with username + password
2. Backend validates credentials -> generates signed JWT -> returns Set-Cookie header (httpOnly, Secure, SameSite=Lax, 24h expiry)
3. Frontend app mounts on next page load -> GET /auth/user (cookie sent automatically) -> if 200, store user in Pinia; if 401, show logged-out UI
4. On logout -> POST /auth/logout -> backend clears cookie -> frontend redirects to home
