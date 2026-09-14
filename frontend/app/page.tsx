const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type HealthResponse = {
  status: string;
  version: string;
  env: string;
};

/**
 * Step 6 placeholder: proves the frontend can reach the FastAPI backend.
 * Will be replaced by the real recipe list in Step 10.
 */
export default async function Home() {
  let health: HealthResponse | null = null;
  let error: string | null = null;

  try {
    const res = await fetch(`${API_URL}/api/health`, { cache: "no-store" });
    if (!res.ok) {
      error = `Backend responded with ${res.status}`;
    } else {
      health = (await res.json()) as HealthResponse;
    }
  } catch {
    error = `Could not reach backend at ${API_URL}`;
  }

  return (
    <main className="flex min-h-full flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-3xl font-semibold tracking-tight">Our Recipe App</h1>

      {health ? (
        <dl className="flex gap-6 rounded-lg border border-zinc-200 p-4 text-sm">
          <div>
            <dt className="text-zinc-500">status</dt>
            <dd className="font-mono">{health.status}</dd>
          </div>
          <div>
            <dt className="text-zinc-500">version</dt>
            <dd className="font-mono">{health.version}</dd>
          </div>
          <div>
            <dt className="text-zinc-500">env</dt>
            <dd className="font-mono">{health.env}</dd>
          </div>
        </dl>
      ) : (
        <p className="max-w-md text-center text-sm text-red-600">{error}</p>
      )}

      <p className="text-xs text-zinc-500">frontend ↔ backend smoke check</p>
    </main>
  );
}
