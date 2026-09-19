"use client";
import { useState } from "react";
import type { FeedCandidate, ScoreBreakdown } from "@/types/compatibility";

export function FeedCard({ candidate }: { candidate: FeedCandidate }) {
  const [breakdown, setBreakdown] = useState<ScoreBreakdown | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  async function handleExpand() {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (breakdown) return;

    setLoading(true);
    try {
      const res = await fetch(`/api/compatibility/score/${candidate.candidate_id}/breakdown`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to load breakdown");
      const data: ScoreBreakdown = await res.json();
      setBreakdown(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="feed-card">
      <div className="feed-card-header" onClick={handleExpand}>
        <span>{candidate.display_name}</span>
        <span className="score-badge">{candidate.score}</span>
      </div>

      {expanded && (
        <div className="feed-card-breakdown">
          {loading && <p>Loading breakdown…</p>}
          {breakdown && (
            <>
              <p>Artist overlap: {(breakdown.artist_overlap * 100).toFixed(0)}%</p>
              <p>Genre similarity: {(breakdown.genre_similarity * 100).toFixed(0)}%</p>
              {breakdown.shared_artists.length > 0 && (
                <p>Shared artists: {breakdown.shared_artists.join(", ")}</p>
              )}
              {breakdown.shared_genres.length > 0 && (
                <p>Shared genres: {breakdown.shared_genres.join(", ")}</p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
