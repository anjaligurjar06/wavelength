"use client";
import { useState } from "react";
import type { FeedCandidate, ScoreBreakdown } from "@/types/compatibility";

interface FeedCardProps {
  candidate: FeedCandidate;
  onMatched?: (matchId: string) => void;
  onDismissed?: () => void;
}

export function FeedCard({ candidate, onMatched, onDismissed }: FeedCardProps) {
  const [breakdown, setBreakdown] = useState<ScoreBreakdown | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [actionPending, setActionPending] = useState(false);
  const [dismissed, setDismissed] = useState(false);

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

  async function handleInteraction(action: "like" | "pass") {
    setActionPending(true);
    try {
      const res = await fetch(`/api/matching/${candidate.candidate_id}/${action}`, {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`Failed to ${action}`);
      const data = await res.json();

      setDismissed(true);

      if (action === "like" && data.matched && data.match_id) {
        onMatched?.(data.match_id);
      } else {
        onDismissed?.();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionPending(false);
    }
  }

  if (dismissed) return null;

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

      <div className="feed-card-actions">
        <button
          disabled={actionPending}
          onClick={() => handleInteraction("pass")}
        >
          Pass
        </button>
        <button
          disabled={actionPending}
          onClick={() => handleInteraction("like")}
        >
          Like
        </button>
      </div>
    </div>
  );
}