from compatibility_engine.explanations import render_score_breakdown


def test_render_artists_and_genres():
    breakdown = {
        "shared_artists": ["artist_1", "artist_2"],
        "shared_genres": ["pop", "indian pop"],
    }

    result = render_score_breakdown(
        breakdown,
        artist_names=["Arijit Singh", "The Weeknd"],
    )

    assert result["headline"] == "You have music in common!"
    assert "Arijit Singh" in result["summary"]
    assert "The Weeknd" in result["summary"]
    assert "pop" in result["summary"]
    assert "indian pop" in result["summary"]


def test_render_only_shared_artists():
    breakdown = {
        "shared_artists": ["artist_1"],
        "shared_genres": [],
    }

    result = render_score_breakdown(
        breakdown,
        artist_names=["Arijit Singh"],
    )

    assert "Arijit Singh" in result["summary"]
    assert result["shared_artists"] == ["Arijit Singh"]


def test_render_only_shared_genres():
    breakdown = {
        "shared_artists": [],
        "shared_genres": ["pop", "rock"],
    }

    result = render_score_breakdown(breakdown)

    assert "pop" in result["summary"]
    assert "rock" in result["summary"]


def test_render_no_overlap():
    breakdown = {
        "shared_artists": [],
        "shared_genres": [],
    }

    result = render_score_breakdown(breakdown)

    assert result["headline"] == "Your music tastes are different."
    assert result["summary"]


def test_render_three_artists():
    breakdown = {
        "shared_artists": ["artist_1", "artist_2", "artist_3"],
        "shared_genres": [],
    }

    result = render_score_breakdown(
        breakdown,
        artist_names=[
            "Arijit Singh",
            "The Weeknd",
            "Adele",
        ],
    )

    assert "Arijit Singh" in result["summary"]
    assert "The Weeknd" in result["summary"]
    assert "Adele" in result["summary"]