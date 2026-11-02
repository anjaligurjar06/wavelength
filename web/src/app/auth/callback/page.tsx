"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AuthCallbackPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/feed");
  }, [router]);
  return <main className="flex flex-1 items-center justify-center p-8">Connecting your account...</main>;
}
