"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/stores/auth-store";
import type { components } from "@/types/api";

type UserOut = components["schemas"]["UserOut"];

/**
 * Seeds the client Zustand store with the user the server already resolved
 * during SSR — avoids a hydration flash and a duplicate /auth/user request.
 */
export function StoreHydration({
  initialUser,
}: {
  initialUser: UserOut | null;
}) {
  useEffect(() => {
    useAuthStore.setState({ user: initialUser, initialized: true });
  }, [initialUser]);

  return null;
}
