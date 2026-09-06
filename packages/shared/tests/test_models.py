from shared.models import Base


def test_all_tables_registered() -> None:
    table_names = {t.name for t in Base.metadata.sorted_tables}
    expected = {
        "users",
        "user_music_profiles",
        "artist_genre_cache",
        "compatibility_scores",
        "matches",
        "threads",
        "messages",
    }
    assert expected.issubset(table_names)
