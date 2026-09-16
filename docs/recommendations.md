# Recommendations & Decision Record

**Created:** 2026-09-10
**Last Updated:** 2026-09-14
**Related:** `docs/architecture_document.md` (v1.3)

---

## Purpose

A shareable record of architecture review findings and remaining recommendations for the recipe app MVP. Contains no personal context, so it can live in the public repo.

---

## Status Summary

| # | Recommendation | Status |
|---|----------------|--------|
| 1 | Clarify `PUT /recipes/{id}` as full-state update | ✅ Applied (arch v1.1) |
| 2 | Narrow `GET /users/{id}/recipes` to owned recipes only | ✅ Applied (arch v1.1) |
| 3 | Learning-friendly implementation order | ✅ Adopted (2026-09-13) |
| 4 | Define a tighter MVP finish line | ✅ Applied (2026-09-10) |
| 5 | Add a small e2e smoke test later | 📋 Open |
| 6 | Harden unsigned Cloudinary uploads before public launch | ⚠️ Accepted risk (MVP) |
| 7 | Prioritize modern patterns over exact versions | 📋 Guiding principle |
| 8 | Adopt ESLint 10 with a lean custom flat config | ✅ Applied (2026-09-13) |

---

## Remaining Recommendations

### 1. Learning-friendly implementation order

**Status:** ✅ Adopted (2026-09-13) — implementation proceeds in this order.

The original step plan was backend-heavy before frontend work begins. The adopted order interleaves frontend and backend work:

1. backend skeleton
2. frontend scaffolding
3. frontend ↔ backend glue
4. auth backend
5. auth UI
6. recipe backend
7. recipe UI
8. deployment and polish

**Rationale:** earlier visible wins; backend learning stays tied to observable product behavior.

**Mapping to dev-steps:** 1 → Step 2 (done) · 2 → Step 6 · 3 → Step 7 · 4 → Step 3 (User model) + Step 4 · 5 → Step 9 · 6 → Step 5 · 7 → Step 10 · 8 → Steps 11–13. Auth and recipe models get separate migrations instead of one up-front migration (dev-steps Step 3 split).

### 2. Tighter MVP finish line

Complete and deployed beats broader but unfinished.

**Required for MVP:**
- register
- login
- create recipe
- view recipe
- edit recipe
- soft delete recipe
- list/search recipes
- private/public visibility works
- deployed over HTTPS

**Deferred (not required for first deployable version):**
- email/password change flows
- Sentry
- shopping list
- normalized ingredient catalog
- smart-merge recipe updates

### 3. End-to-end smoke test (post-core-MVP)

Add one small e2e flow after the core features exist:
- register → login → create recipe → open detail → logout

**Rationale:** demonstrates user-flow thinking, integration awareness, auth correctness, and regression protection.

### 4. Cloudinary upload hardening (pre-public-launch)

Unsigned uploads are acceptable for MVP. Before public launch:
- limit file size
- restrict formats
- use a dedicated preset/folder
- move to signed uploads

### 5. Guiding principle: patterns over versions

The specific framework versions matter less than demonstrating understanding of:
- Server vs Client Components
- SSR cookie handling
- `credentials: "include"`
- typed API contracts
- FastAPI schemas and dependency injection
- migration workflow
- multi-service deployment basics

---

## Milestone Plan

Three demoable vertical slices, derived from the adopted implementation order (above) and the MVP finish line.

### M1 — Auth vertical slice

register / login / logout / profile work end-to-end
(backend: Step 4 endpoints + tests · frontend: Step 9 UI)

### M2 — Recipe vertical slice

create / view / edit / soft-delete / list+search recipes, with images
(backend: Step 5 · frontend: Steps 10–11)

### M3 — Deploy + polish

deployed over HTTPS, responsive polish, Sentry, smoke e2e test
(Steps 12–13 + recommendation #5)

---

## Applied Changes (recorded in arch v1.1 + v1.2)

- **`PUT /recipes/{id}`** is a full editable recipe update. The frontend sends the complete recipe state, including full `ingredients` and `preparation_steps` arrays, on every save. Omitted child items are deleted server-side.
- **`GET /users/{id}/recipes`** returns only recipes owned by the specified user: private included for self-access, public only otherwise. Mixed discovery belongs on `GET /recipes`.
- **Auth cookie renamed** from `token` to `access_token` (arch v1.2, 2026-09-13). Frontend constant: `AUTH_COOKIE_NAME` in `frontend/lib/auth-cookie.ts`. Backend sets the cookie in Step 4 (`app/services/cookies.py`). Leaves room for a future `refresh_token`.

---

## Frontend Tooling Decisions

### ESLint 10 migration (2026-09-13)

**Decision:** Run ESLint 10 with a custom flat config instead of ESLint 9 + `eslint-config-next`.

**Why:** The scaffold installed `eslint@9.39.5` (line-level EOL). `eslint-config-next@16.3.5` itself allows ESLint 10, but three of its plugin dependencies do not declare ESLint 10 peer support: `eslint-plugin-react` (7.37.5), `eslint-plugin-jsx-a11y` (6.10.2), `eslint-plugin-import` (2.32.0).

**What changed:**
- Removed `eslint-config-next`
- Added direct devDeps: `@next/eslint-plugin-next@16.3.5`, `typescript-eslint@^8.70`, `eslint-plugin-react-hooks@^7.1.1`, `globals@^16`
- Upgraded `eslint` `^9` → `^10`
- Rewrote `eslint.config.mjs`: Next core-web-vitals rules + react-hooks recommended + typescript-eslint recommended + browser/node globals

**Known gaps (temporarily dropped rules):**
- `eslint-plugin-react` recommended set (incl. `react/jsx-key` — React still warns at runtime in dev)
- `eslint-plugin-jsx-a11y` six warn-level a11y rules
- `eslint-plugin-import` `no-anonymous-default-export` warn rule

**Re-add checklist** (when any of these publish an ESLint 10-compatible peer range, or `eslint-config-next` ships full ESLint 10 support):
1. `eslint-plugin-react` 7.38+/8.x → re-add `jsx-key` etc., or return to `eslint-config-next` if it supports ESLint 10 end-to-end
2. `eslint-plugin-jsx-a11y` 6.11+ → re-add the six a11y rules
3. `eslint-plugin-import` 2.33+ → re-add `no-anonymous-default-export`

---

## Backend Tooling Decisions

### passlib → direct bcrypt (2026-09-14)

**Decision:** Drop the unmaintained `passlib` wrapper and call `bcrypt` directly (`hashpw` / `checkpw` / `gensalt`) in `app/services/security.py`.

**Why:** `passlib` has been unmaintained since 2020 and its version detection is incompatible with `bcrypt` 5.x internals. Alternatives considered: `pwdlib` (maintained wrapper), `argon2-cffi` (stronger algorithm). Chose direct bcrypt for zero new dependencies; both upgrades remain cheap later (rehash-on-login migration if moving to Argon2id).

**Recorded in:** `architecture_document.md` v1.3.

---

## Product Questions (answered 2026-09-14)

1. **Portfolio vs. public use** — mainly a rehire/portfolio project, but not exclusively so.
2. **Primary users** — self, friends and family, and likely friends of friends. Wider public is far off, if ever.
3. **Core value** — primarily recipe storage and organization (meal planning, grocery shopping); secondarily sharing/discovery.

**Implications:**
- M3 scope stays lean (portfolio-first): Cloudinary signed uploads and rate limiting remain pre-public-launch items, not MVP blockers
- Post-MVP sharing features (private sharing to specific users, ingredient search) serve the secondary value
- Shopping list / print features serve the primary value — keep them near the top of post-MVP work

---

## Agent Workflow Reference

Quick reference for AI-assisted development in this repo:

- **Agent** = model + instructions + tools + action loop
- **Harness** = runtime providing tools, permissions, and safety
- **`AGENTS.md`** = repo-specific instructions for agents
- **Skill** (`SKILL.md`) = reusable instructions for a repeatable task

---

## When to Update This Document

Update when a **decision changes**, not when work progresses.

**Update on:**
- Recommendation status change:
  - `📋 Open` → `✅ Applied` (add date)
  - Rejected (add one-line reason)
  - Superseded (note the replacement)
- Architecture doc version bump — sync the `Related:` line and record new applied changes
- New decision or recommendation from a review or planning session
- MVP scope change (the finish-line list)
- Risk-accepted item resolves (e.g., signed uploads implemented before launch)

**Do not update for:**
- Routine implementation progress — that lives in `docs/dev-steps_1-14.md`
- Personal context — stays in `docs/_internal_docs/`
- Transient working notes

Every update: bump `Last Updated:` and add dates to status changes.

---

## Next Steps

1. Keep `docs/dev-steps_1-14.md` aligned with architecture doc changes
2. ✅ Learning-friendly order in progress — skeleton, scaffolding, and glue done; auth backend (Step 4) current
3. Complete the auth vertical slice: auth endpoints + tests (Step 4), then auth UI (Step 9)
4. Add e2e smoke test after recipe flows exist
