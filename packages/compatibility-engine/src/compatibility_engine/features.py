from collections import defaultdict


def build_genre_vector(
    ranked_genres: list[list[str]],
) -> dict[str, float]:
    """Build an L1-normalized genre vector from ranked genre lists."""

    if not ranked_genres:
        return {}

    genre_weights: dict[str, float] = defaultdict(float)

    for rank, genres in enumerate(ranked_genres, start=1):
        if not genres:
            continue

        unique_genres = set(genres)

        rank_weight = 1.0 / rank
        weight_per_genre = rank_weight / len(unique_genres)

        for genre in unique_genres:
            genre_weights[genre] += weight_per_genre

    total_weight = sum(genre_weights.values())

    if total_weight == 0:
        return {}

    return {
        genre: weight / total_weight
        for genre, weight in genre_weights.items()
    }