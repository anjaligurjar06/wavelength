import json

from discovery.snapshot import save_snapshot


def test_save_snapshot(tmp_path):
    data = {
        "items": [
            {
                "track": {
                    "id": "track-1",
                    "name": "Test Song",
                },
                "played_at": "2026-09-06T10:00:00Z",
            }
        ]
    }

    file_path = save_snapshot(data, directory=str(tmp_path))

    assert file_path.exists()

    with file_path.open("r", encoding="utf-8") as file:
        saved_data = json.load(file)

    assert saved_data == data