from unittest.mock import patch

from music_ingestion.collector import collect_recently_played


def test_collect_recently_played():
    fake_data = {
        "items": [
            {
                "track": {
                    "id": "track-1",
                    "name": "Test Song",
                }
            }
        ]
    }

    with patch(
        "music_ingestion.collector.SpotifyClient.get_recently_played",
        return_value=fake_data,
    ):
        with patch(
            "music_ingestion.collector.save_snapshot"
        ) as mock_save:
            result = collect_recently_played("fake-token")

    assert result == fake_data
    mock_save.assert_called_once_with(fake_data)
