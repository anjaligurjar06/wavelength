export interface FeedCandidate {
  candidate_id: string;
  display_name: string;
  score: number;
}

export interface ScoreBreakdown {
  artist_overlap: number;
  genre_similarity: number;
  shared_artists: string[];
  shared_genres: string[];
}
