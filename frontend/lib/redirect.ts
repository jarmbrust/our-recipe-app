/**
 * Open-redirect guard. Only internal paths may be used as redirect targets:
 * - must start with `/`
 * - must not start with `//` (protocol-relative)
 * - must not contain `:` before the first `/` (blocks `javascript:`, `https:`, …)
 * Falls back to `/`.
 */
export function validateRedirect(raw: string | null | undefined): string {
  if (!raw) return "/";
  if (!raw.startsWith("/")) return "/";
  if (raw.startsWith("//")) return "/";
  const firstSlash = raw.indexOf("/");
  const colon = raw.indexOf(":");
  if (colon !== -1 && colon < firstSlash) return "/";
  return raw;
}
