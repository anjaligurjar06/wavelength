from unittest.mock import Mock, patch

from music_ingestion.spotify_client import SpotifyClient


def test_get_top_artists():
    client = SpotifyClient("test-token")

    fake_response = Mock()
    fake_response.json.return_value = {
        "items": [
            {
                "id": "artist-1",
                "name": "Test Artist",
            }
        ]
    }
    fake_response.raise_for_status.return_value = None

    with patch("music_ingestion.spotify_client.requests.get") as mock_get:
        mock_get.return_value = fake_response

        result = client.get_top_artists(
            limit=10,
            time_range="short_term",
        )

    assert result["items"][0]["name"] == "Test Artist"

    mock_get.assert_called_once_with(
        "https://api.spotify.com/v1/me/top/artists",
        headers={
            "Authorization": "Bearer test-token"
        },
        params={
            "limit": 10,
            "time_range": "short_term",
        },
        timeout=10,
    )


def test_get_top_tracks():
    client = SpotifyClient("test-token")

    fake_response = Mock()
    fake_response.json.return_value = {
        "items": [
            {
                "id": "track-1",
                "name": "Test Track",
            }
        ]
    }
    fake_response.raise_for_status.return_value = None

    with patch("music_ingestion.spotify_client.requests.get") as mock_get:
        mock_get.return_value = fake_response

        result = client.get_top_tracks(
            limit=5,
            time_range="long_term",
        )

    assert result["items"][0]["name"] == "Test Track"

    mock_get.assert_called_once_with(
        "https://api.spotify.com/v1/me/top/tracks",
        headers={
            "Authorization": "Bearer test-token"
        },
        params={
            "limit": 5,
            "time_range": "long_term",
        },
        timeout=10,
    )
def test_get_recently_played():
    client = SpotifyClient("test-token")

    fake_response = Mock()
    fake_response.json.return_value = {
        "items": [
            {
                "track": {
                    "id": "track-1",
                    "name": "Recently Played Song",
                },
                "played_at": "2026-09-06T10:00:00Z",
            }
        ]
    }
    fake_response.raise_for_status.return_value = None

    with patch("music_ingestion.spotify_client.requests.get") as mock_get:
        mock_get.return_value = fake_response

        result = client.get_recently_played(limit=10)

    assert result["items"][0]["track"]["name"] == "Recently Played Song"

    mock_get.assert_called_once_with(
        "https://api.spotify.com/v1/me/player/recently-played",
        headers={
            "Authorization": "Bearer test-token"
        },
        params={
            "limit": 10,
        },
        timeout=10,
    )
