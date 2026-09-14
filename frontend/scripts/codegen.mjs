import { readFileSync } from "node:fs";
import { writeFile } from "node:fs/promises";
import { execSync } from "node:child_process";

/**
 * Regenerates `types/api.d.ts` from the backend's live OpenAPI spec.
 * Requires the backend to be running (defaults to http://localhost:8000).
 * Reads NEXT_PUBLIC_API_URL from .env.local if present.
 */

function loadEnvLocal() {
  try {
    const raw = readFileSync(new URL("../.env.local", import.meta.url), "utf8");
    for (const line of raw.split("\n")) {
      const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
      if (match) {
        process.env[match[1]] ??= match[2].trim();
      }
    }
  } catch {
    // no .env.local — fall back to the default base URL
  }
}

loadEnvLocal();

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const specUrl = `${baseUrl}/openapi.json`;

console.log(`Fetching OpenAPI spec from ${specUrl}`);
const res = await fetch(specUrl);
if (!res.ok) {
  console.error(`Failed to fetch spec: ${res.status} ${res.statusText}`);
  console.error(
    "Is the backend running? (cd backend && poetry run uvicorn app.main:app --reload)",
  );
  process.exit(1);
}

const spec = await res.json();
await writeFile(
  new URL("../openapi.json", import.meta.url),
  JSON.stringify(spec, null, 2),
);

console.log("Generating types/api.d.ts with openapi-typescript");
execSync("pnpm exec openapi-typescript openapi.json -o types/api.d.ts", {
  stdio: "inherit",
  cwd: new URL("..", import.meta.url),
});

console.log(
  "Done. Review the diff and commit types/api.d.ts alongside API changes.",
);
