/**
 * Auth cookie contract for server-side code.
 * Must match the cookie name set by the FastAPI backend (Step 4,
 * app/services/cookies.py).
 *
 * Renamed from "token" to "access_token" (2026-09-13) to leave room for a
 * future refresh_token cookie without ambiguity.
 */
export const AUTH_COOKIE_NAME = "access_token";
