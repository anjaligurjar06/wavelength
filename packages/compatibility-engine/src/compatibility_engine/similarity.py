import math


def cosine_similarity(
    vector_a: dict[str, float],
    vector_b: dict[str, float],
) -> float:
    """Calculate cosine similarity between two sparse genre vectors."""

    if not vector_a or not vector_b:
        return 0.0

    all_genres = set(vector_a) | set(vector_b)

    dot_product = sum(
        vector_a.get(genre, 0.0) * vector_b.get(genre, 0.0)
        for genre in all_genres
    )

    magnitude_a = math.sqrt(
        sum(value**2 for value in vector_a.values())
    )

    magnitude_b = math.sqrt(
        sum(value**2 for value in vector_b.values())
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)