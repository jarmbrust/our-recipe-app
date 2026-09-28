"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export function Header() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);

  async function handleLogout() {
    await api.POST("/api/auth/logout");
    setUser(null);
    router.push("/");
    router.refresh();
  }

  return (
    <header className="flex items-center justify-between border-b border-zinc-200 px-6 py-3 text-sm">
      <Link href="/" className="font-semibold">
        Our Recipe App
      </Link>
      <nav className="flex items-center gap-4">
        {user ? (
          <>
            <Link href="/auth/profile" className="hover:underline">
              {user.display_name ?? user.username}
            </Link>
            <button
              type="button"
              onClick={handleLogout}
              className="hover:underline"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link href="/auth/login" className="hover:underline">
              Login
            </Link>
            <Link href="/auth/register" className="hover:underline">
              Register
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}
