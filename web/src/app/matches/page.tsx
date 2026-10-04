"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import type { Thread } from "@/types/chat";

export default function MatchesPage() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await apiFetch("/chat/threads");
        if (!res.ok) throw new Error(`Threads request failed: ${res.status}`);
        setThreads(await res.json());
      } catch (err) {
        console.error(err);
        setError("Couldn't load your matches. Try refreshing.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <main><p>Loading matches…</p></main>;
  if (error) return <main><p>{error}</p></main>;

  return (
    <main>
      <h1>Matches</h1>
      <p><Link href="/feed">Back to feed</Link></p>
      {threads.length === 0 ? (
        <p>No matches yet. Like someone in your feed!</p>
      ) : (
        <ul>
          {threads.map((t) => (
            <li key={t.id}>
              <Link href={`/chat/${t.id}`}>
                <strong>{t.other_display_name}</strong>
                {" — "}
                {t.last_message ?? "Say hi!"}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}