"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export function LoginForm({ redirectTo }: { redirectTo: string }) {
  const router = useRouter();
  const setUser = useAuthStore((state) => state.setUser);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const { data, error } = await api.POST("/api/auth/login", {
      body: { username, password },
    });

    if (error || !data) {
      setError("Invalid username or password");
      setSubmitting(false);
      return;
    }

    setUser(data);
    router.push(redirectTo);
    router.refresh();
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex w-full max-w-sm flex-col gap-4 rounded-lg border border-zinc-200 p-6"
    >
      <h1 className="text-xl font-semibold">Login</h1>

      <label className="flex flex-col gap-1 text-sm">
        Username
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          autoComplete="username"
          className="rounded border border-zinc-300 px-2 py-1.5"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        Password
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
          className="rounded border border-zinc-300 px-2 py-1.5"
        />
      </label>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Logging in…" : "Login"}
      </button>

      <p className="text-sm text-zinc-500">
        No account?{" "}
        <Link href="/auth/register" className="underline">
          Register
        </Link>
      </p>
    </form>
  );
}
