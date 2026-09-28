import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Header } from "@/components/Header";
import { StoreHydration } from "@/components/StoreHydration";
import { serverApi } from "@/lib/serverApi";
import type { components } from "@/types/api";
import "./globals.css";

type UserOut = components["schemas"]["UserOut"];

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Our Recipe App",
  description: "Cook, share, and discover recipes.",
};

/**
 * Resolves the current user once, server-side, from the JWT cookie —
 * used both to seed the client store and to render auth-aware UI.
 * 401 (no/invalid cookie) → null.
 */
async function getInitialUser(): Promise<UserOut | null> {
  try {
    const client = await serverApi();
    const { data, error } = await client.GET("/api/auth/user");
    if (error || !data) return null;
    return data;
  } catch {
    return null;
  }
}

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const initialUser = await getInitialUser();

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <StoreHydration initialUser={initialUser} />
        <Header />
        {children}
      </body>
    </html>
  );
}
