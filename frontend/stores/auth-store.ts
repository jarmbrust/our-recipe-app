"use client";

import { create } from "zustand";
import type { components } from "@/types/api";

type UserOut = components["schemas"]["UserOut"];

type AuthState = {
  user: UserOut | null;
  initialized: boolean;
  setUser: (user: UserOut | null) => void;
  setInitialized: (initialized: boolean) => void;
};

/**
 * Client-side auth state. Seeded once on app load by `StoreHydration`
 * from the server-rendered `GET /auth/user` result (SSR hydration pattern).
 */
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  initialized: false,
  setUser: (user) => set({ user }),
  setInitialized: (initialized) => set({ initialized }),
}));
