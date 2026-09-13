# Recommendations & Decision Record

**Created:** 2026-09-10
**Last Updated:** 2026-09-13
**Related:** `docs/architecture_document.md` (v1.1)

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
| 4 | Define a tighter MVP finish line | 📋 Open |
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

## Applied Changes (recorded in arch v1.1)

- **`PUT /recipes/{id}`** is a full editable recipe update. The frontend sends the complete recipe state, including full `ingredients` and `preparation_steps` arrays, on every save. Omitted child items are deleted server-side.
- **`GET /users/{id}/recipes`** returns only recipes owned by the specified user: private included for self-access, public only otherwise. Mixed discovery belongs on `GET /recipes`.

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
2. ✅ Adopted learning-friendly order (2026-09-13) — next: frontend scaffolding
3. Proceed with backend → frontend scaffolding in the chosen order
4. Add e2e smoke test after core flows exist
