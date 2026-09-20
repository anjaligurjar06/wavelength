"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FeedCard } from "@/components/FeedCard";
import type { FeedCandidate } from "@/types/compatibility";

export default function FeedPage() {
  const router = useRouter();
  const [candidates, setCandidates] = useState<FeedCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [matchedThreadId, setMatchedThreadId] = useState<string | null>(null);

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

  function handleMatched(candidateId: string, _matchId: string, threadId: string) {
    setCandidates((prev) => prev.filter((c) => c.candidate_id !== candidateId));
    setMatchedThreadId(threadId);
  }

  function handleDismissed(candidateId: string) {
    setCandidates((prev) => prev.filter((c) => c.candidate_id !== candidateId));
  }

  if (loading) return <main><p>Loading feed…</p></main>;
  if (error) return <main><p>{error}</p></main>;

  return (
    <main>
      <h1>Feed</h1>

      {matchedThreadId && (
        <div className="match-banner">
          <p>It&apos;s a match! 🎉</p>
          <button onClick={() => router.push(`/chat/${matchedThreadId}`)}>
            Say hi
          </button>
          <button onClick={() => setMatchedThreadId(null)}>Keep browsing</button>
        </div>
      )}

      {candidates.length === 0 ? (
        <p>No matches nearby yet — check back soon.</p>
      ) : (
        <div className="feed-list">
          {candidates.map((c) => (
            <FeedCard
              key={c.candidate_id}
              candidate={c}
              onMatched={(matchId, threadId) => handleMatched(c.candidate_id, matchId, threadId)}
              onDismissed={() => handleDismissed(c.candidate_id)}
            />
          ))}
        </div>
      )}
    </main>
  );
}