from unittest.mock import patch

from discovery.collector import collect_recently_played


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
        "discovery.collector.SpotifyClient.get_recently_played",
        return_value=fake_data,
    ):
        with patch(
            "discovery.collector.save_snapshot"
        ) as mock_save:
            result = collect_recently_played("fake-token")

    assert result == fake_data
    mock_save.assert_called_once_with(fake_data)