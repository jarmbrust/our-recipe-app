import type { Metadata } from "next";
import { RegisterForm } from "@/components/RegisterForm";

export const metadata: Metadata = { title: "Register" };

export default function RegisterPage() {
  return (
    <main className="flex flex-1 items-center justify-center p-8">
      <RegisterForm />
    </main>
  );
}
