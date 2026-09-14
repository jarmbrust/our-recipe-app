import createClient from "openapi-fetch";
import type { paths } from "@/types/api";
import { fetchWithCredentials } from "@/lib/fetcher";

/**
 * Typed API client for browser-side (Client Component) usage.
 * Types are generated from the backend's OpenAPI spec via `pnpm run codegen`.
 */
export const api = createClient<paths>({
  baseUrl: process.env.NEXT_PUBLIC_API_URL,
  fetch: fetchWithCredentials,
});
