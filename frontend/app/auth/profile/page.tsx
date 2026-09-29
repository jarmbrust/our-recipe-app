import type { Metadata } from "next";
import { serverApi } from "@/lib/serverApi";

export const metadata: Metadata = { title: "Profile" };

export default async function ProfilePage() {
  const client = await serverApi();
  const { data } = await client.GET("/api/auth/user");

  // middleware.ts protects this route — data should always be present.
  if (!data) return null;

  return (
    <main className="flex flex-1 items-start justify-center p-8">
      <section className="flex w-full max-w-md flex-col gap-3 rounded-lg border border-zinc-200 p-6">
        <h1 className="text-xl font-semibold">Profile</h1>

        <dl className="flex flex-col gap-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-zinc-500">Username</dt>
            <dd>{data.username}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-zinc-500">Email</dt>
            <dd>{data.email}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-zinc-500">Display name</dt>
            <dd>{data.display_name ?? "—"}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-zinc-500">Member since</dt>
            <dd>{new Date(data.created_at).toLocaleDateString()}</dd>
          </div>
        </dl>

        <p className="text-xs text-zinc-400">
          Account settings (email/password change) arrive post-MVP.
        </p>
      </section>
    </main>
  );
}
