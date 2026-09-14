/**
 * Browser-side fetch wrapper: always includes credentials so the JWT auth
 * cookie is sent to the backend on same-site cross-origin requests.
 */
export function fetchWithCredentials(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  return fetch(input, { ...init, credentials: "include" });
}
