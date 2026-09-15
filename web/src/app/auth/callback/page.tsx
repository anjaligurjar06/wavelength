"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      localStorage.setItem("wavelength_token", token);
      router.replace("/feed");
    } else {
      router.replace("/login");
    }
  }, [router, searchParams]);

  return (
    <main className="flex flex-1 items-center justify-center p-8">
      <p className="text-sm text-neutral-500">Connecting your account…</p>
    </main>
  );
}