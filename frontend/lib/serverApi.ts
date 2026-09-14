import { cookies } from "next/headers";
import createClient from "openapi-fetch";
import type { paths } from "@/types/api";
import { AUTH_COOKIE_NAME } from "@/lib/auth-cookie";

/**
 * Typed API client for server-side (Server Component) usage.
 *
 * Server-side fetch has no browser cookie jar, so the JWT cookie must be
 * read from the request and forwarded manually (see AGENTS.md SSR gotcha).
 * Client Components should use `lib/api.ts` instead — the browser sends
 * cookies automatically.
 */
export async function serverApi() {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;

  // Missing/empty token = anonymous request; the backend 401s where auth is required.
  const headers = token
    ? { Cookie: `${AUTH_COOKIE_NAME}=${token}` }
    : undefined;

  return createClient<paths>({
    baseUrl: process.env.NEXT_PUBLIC_API_URL,
    headers,
  });
}
