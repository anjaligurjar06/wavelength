import json
from datetime import datetime, timezone
from pathlib import Path


def save_snapshot(data: dict, directory: str = "snapshots") -> Path:
    snapshot_dir = Path(directory)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H-%M-%S-%fZ"
    )

    file_path = snapshot_dir / f"{timestamp}.json"

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    return file_path