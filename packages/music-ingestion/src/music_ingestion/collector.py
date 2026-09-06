from music_ingestion.spotify_client import SpotifyClient
from music_ingestion.snapshot import save_snapshot


def collect_recently_played(access_token: str):
    client = SpotifyClient(access_token)

    data = client.get_recently_played()

    save_snapshot(data)

    return data