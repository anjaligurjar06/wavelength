import time

from matching.batch import run_batch_scorer
from shared.models import Base, User, UserMusicProfile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

PROFILE_COUNT = 500
ARTISTS_PER_PROFILE = 20
ARTIST_POOL_SIZE = 200

GENRE_POOL = [
    "pop",
    "rock",
    "indie",
    "hip-hop",
    "electronic",
    "jazz",
    "classical",
    "metal",
    "r&b",
    "folk",
]


def build_synthetic_artists(profile_index: int) -> list[dict]:
    """Create deterministic artist data for one synthetic profile."""

    artists = []

    for rank in range(ARTISTS_PER_PROFILE):
        artist_index = (
            profile_index * 7 + rank * 3
        ) % ARTIST_POOL_SIZE

        first_genre = GENRE_POOL[
            artist_index % len(GENRE_POOL)
        ]

        second_genre = GENRE_POOL[
            (artist_index + 3) % len(GENRE_POOL)
        ]

        artists.append(
            {
                "id": f"artist-{artist_index}",
                "name": f"Artist {artist_index}",
                "genres": [
                    first_genre,
                    second_genre,
                ],
            }
        )

    return artists


def seed_profiles(db: Session) -> None:
    """Insert 500 deterministic synthetic users and music profiles."""

    for index in range(PROFILE_COUNT):
        user_id = f"benchmark-user-{index:03d}"

        user = User(
            id=user_id,
            email=f"benchmark-{index:03d}@example.com",
            display_name=f"Benchmark User {index:03d}",
        )

        profile = UserMusicProfile(
            user_id=user_id,
            top_artists={
                "items": build_synthetic_artists(index),
            },
            top_tracks={"items": []},
            recently_played={"items": []},
            top_genres={},
            time_window="6m",
            is_stale=False,
        )

        db.add(user)
        db.add(profile)

    db.commit()


def main() -> None:
    """Generate synthetic profiles and benchmark batch scoring."""

    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        print(
            f"Generating {PROFILE_COUNT} synthetic profiles..."
        )

        seed_profiles(db)

        expected_pairs = (
            PROFILE_COUNT
            * (PROFILE_COUNT - 1)
            // 2
        )

        print(f"Profiles generated: {PROFILE_COUNT}")
        print(f"Expected pairs: {expected_pairs}")
        print("Running baseline batch scorer...")

        start = time.perf_counter()

        result = run_batch_scorer(db)

        elapsed = time.perf_counter() - start

        print()
        print("=== Cycle 8 Batch Scoring Benchmark ===")
        print(f"Profiles: {PROFILE_COUNT}")
        print(f"Expected pairs: {expected_pairs}")
        print(f"Pairs scored: {result.pairs_scored}")
        print(f"Pairs skipped: {result.pairs_skipped}")
        print(f"Elapsed seconds: {elapsed:.3f}")

        if elapsed > 0:
            pairs_per_second = (
                result.pairs_scored / elapsed
            )

            print(
                "Pairs per second: "
                f"{pairs_per_second:.2f}"
            )


if __name__ == "__main__":
    main()