import json

from compatibility_engine.scoring import (
    adaptive_composite_score,
    adaptive_weights,
    genre_coverage,
    needs_manual_genre_fallback,
)
from compatibility_engine.similarity import (
    cosine_similarity,
    jaccard_similarity,
)
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg://wavelength:wavelength@localhost:5432/wavelength"

SIMRAN_ID = "355ce34a-5153-47e0-b241-05c42b6280e4"
SHERLIN_ID = "967d0652-3ed4-4b26-95df-22d7091b9cb6"


def get_profile(connection, user_id):
    query = text(
        """
        SELECT top_artists, top_tracks, top_genres
        FROM user_music_profiles
        WHERE user_id = :user_id
        """
    )

    row = connection.execute(
        query,
        {"user_id": user_id},
    ).mappings().first()

    if row is None:
        raise ValueError(f"No profile found for {user_id}")

    return row


def parse_json(value):
    if isinstance(value, str):
        return json.loads(value)

    return value


def extract_names(data):
    data = parse_json(data)

    return [
        item["name"]
        for item in data.get("items", [])
        if item.get("name")
    ]


def extract_genres(data):
    data = parse_json(data)

    return data.get("genres", [])


def make_genre_vector(genres):
    return {genre: 1.0 for genre in genres}


def validate_pair(connection, name_a, id_a, name_b, id_b):
    profile_a = get_profile(connection, id_a)
    profile_b = get_profile(connection, id_b)

    artists_a = extract_names(profile_a["top_artists"])
    artists_b = extract_names(profile_b["top_artists"])

    tracks_a = extract_names(profile_a["top_tracks"])
    tracks_b = extract_names(profile_b["top_tracks"])

    genres_a = extract_genres(profile_a["top_genres"])
    genres_b = extract_genres(profile_b["top_genres"])

    artist_overlap = jaccard_similarity(
        artists_a,
        artists_b,
    )

    track_overlap = jaccard_similarity(
        tracks_a,
        tracks_b,
    )

    genre_vector_a = make_genre_vector(genres_a)
    genre_vector_b = make_genre_vector(genres_b)

    genre_similarity = cosine_similarity(
        genre_vector_a,
        genre_vector_b,
    )

    coverage_a = genre_coverage(
        [
            {"genres": genres_a}
            for _ in artists_a
        ]
    )

    coverage_b = genre_coverage(
        [
            {"genres": genres_b}
            for _ in artists_b
        ]
    )

    artist_weight, genre_weight = adaptive_weights(
        coverage_a,
        coverage_b,
    )

    final_score = adaptive_composite_score(
        artist_overlap=artist_overlap,
        genre_similarity=genre_similarity,
        coverage_a=coverage_a,
        coverage_b=coverage_b,
    )

    shared_artists = sorted(
        set(artists_a) & set(artists_b)
    )

    shared_tracks = sorted(
        set(tracks_a) & set(tracks_b)
    )

    fallback_needed = needs_manual_genre_fallback(
        coverage_a,
        coverage_b,
    )

    print("\n" + "=" * 65)
    print(f"{name_a}  <->  {name_b}")
    print("=" * 65)

    print("\nPROFILE")
    print(f"{name_a} artists : {len(artists_a)}")
    print(f"{name_b} artists : {len(artists_b)}")
    print(f"{name_a} tracks  : {len(tracks_a)}")
    print(f"{name_b} tracks  : {len(tracks_b)}")

    print("\nMANUAL OVERLAP CHECK")
    print(f"Shared artists: {shared_artists}")
    print(f"Shared tracks : {shared_tracks}")

    print("\nSIMILARITY")
    print(f"Artist Jaccard : {artist_overlap:.4f}")
    print(f"Artist %       : {artist_overlap * 100:.2f}%")
    print(f"Track Jaccard  : {track_overlap:.4f}")
    print(f"Track %        : {track_overlap * 100:.2f}%")
    print(f"Genre cosine   : {genre_similarity:.4f}")

    print("\nGENRE COVERAGE")
    print(f"{name_a}: {coverage_a:.4f}")
    print(f"{name_b}: {coverage_b:.4f}")

    print("\nADAPTIVE WEIGHTS")
    print(f"Artist weight: {artist_weight:.2f}")
    print(f"Genre weight : {genre_weight:.2f}")

    print("\nFINAL COMPATIBILITY")
    print(f"Score: {final_score:.4f}")
    print(f"Score: {final_score * 100:.2f}/100")

    print("\nMANUAL GENRE FALLBACK")
    print(f"Needed: {fallback_needed}")


def main():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as connection:
        validate_pair(
            connection,
            "Simran",
            SIMRAN_ID,
            "Sherlin",
            SHERLIN_ID,
        )


if __name__ == "__main__":
    main()