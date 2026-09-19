"use client";
import { useEffect, useState } from "react";
import { FeedCard } from "@/components/FeedCard";
import type { FeedCandidate } from "@/types/compatibility";

export default function FeedPage() {
  const [candidates, setCandidates] = useState<FeedCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadFeed() {
      try {
        const res = await fetch("/api/matching/feed", { credentials: "include" });
        if (!res.ok) throw new Error(`Feed request failed: ${res.status}`);
        const data: FeedCandidate[] = await res.json();
        setCandidates(data);
      } catch (err) {
        console.error(err);
        setError("Couldn't load your feed. Try refreshing.");
      } finally {
        setLoading(false);
      }
    }
    loadFeed();
  }, []);

  if (loading) return <main><p>Loading feed…</p></main>;
  if (error) return <main><p>{error}</p></main>;
  if (candidates.length === 0) return <main><p>No matches nearby yet — check back soon.</p></main>;

  return (
    <main>
      <h1>Feed</h1>
      <div className="feed-list">
        {candidates.map((c) => (
          <FeedCard key={c.candidate_id} candidate={c} />
        ))}
      </div>
    </main>
  );
}
