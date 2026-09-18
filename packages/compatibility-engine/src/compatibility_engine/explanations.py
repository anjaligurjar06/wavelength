from collections.abc import Mapping


def _format_list(items: list[str]) -> str:
    
    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} and {items[1]}"

    return f"{', '.join(items[:-1])}, and {items[-1]}"


def render_score_breakdown(
    breakdown: Mapping,
    artist_names: list[str] | None = None,
) -> dict:
    """Convert a compatibility breakdown into frontend-readable text."""

    shared_artists = artist_names or breakdown.get("shared_artists", [])
    shared_genres = breakdown.get("shared_genres", [])

    shared_artists = [
        str(artist).strip()
        for artist in shared_artists
        if str(artist).strip()
    ]

    shared_genres = [
        str(genre).strip()
        for genre in shared_genres
        if str(genre).strip()
    ]

    if shared_artists and shared_genres:
        headline = "You have music in common!"
        summary = (
            f"You both listen to {_format_list(shared_artists)} "
            f"and share similar tastes in {_format_list(shared_genres)}."
        )

    elif shared_artists:
        headline = "You have music in common!"
        summary = (
            f"You both listen to {_format_list(shared_artists)}."
        )

    elif shared_genres:
        headline = "Your music tastes are similar!"
        summary = (
            f"You share similar tastes in {_format_list(shared_genres)}."
        )

    else:
        headline = "Your music tastes are different."
        summary = (
            "You don't have any shared artists or genres yet."
        )

    return {
        "headline": headline,
        "summary": summary,
        "shared_artists": shared_artists,
        "shared_genres": shared_genres,
    }