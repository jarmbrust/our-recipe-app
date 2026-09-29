import type { Metadata } from "next";
import { LoginForm } from "@/components/LoginForm";
import { validateRedirect } from "@/lib/redirect";

export const metadata: Metadata = { title: "Login" };

type LoginPageProps = {
  searchParams: Promise<{ redirect?: string }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = await searchParams;
  const redirectTo = validateRedirect(params.redirect);

  return (
    <main className="flex flex-1 items-center justify-center p-8">
      <LoginForm redirectTo={redirectTo} />
    </main>
  );
}
