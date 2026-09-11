# Recommendations & Decision Record

**Created:** 2026-09-10
**Last Updated:** 2026-09-10
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
| 3 | Consider frontend-earlier implementation order | 📋 Open |
| 4 | Define a tighter MVP finish line | 📋 Open |
| 5 | Add a small e2e smoke test later | 📋 Open |
| 6 | Harden unsigned Cloudinary uploads before public launch | ⚠️ Accepted risk (MVP) |
| 7 | Prioritize modern patterns over exact versions | 📋 Guiding principle |

---

## Remaining Recommendations

### 1. Learning-friendly implementation order

The current step plan is backend-heavy before frontend work begins. Consider an order that interleaves frontend and backend work:

1. backend skeleton
2. frontend scaffolding
3. frontend ↔ backend glue
4. auth backend
5. auth UI
6. recipe backend
7. recipe UI
8. deployment and polish

**Rationale:** earlier visible wins; backend learning stays tied to observable product behavior.

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
2. Decide implementation order (recommendation #1)
3. Proceed with backend → frontend scaffolding in the chosen order
4. Add e2e smoke test after core flows exist
