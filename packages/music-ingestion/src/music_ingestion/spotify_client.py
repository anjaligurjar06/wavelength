import requests


class SpotifyClient:
    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def _get(self, endpoint: str, params: dict | None = None):
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.get(
            f"{self.BASE_URL}{endpoint}",
            headers=headers,
            params=params,
            timeout=10,
        )

        response.raise_for_status()
        return response.json()

    def get_top_artists(
        self,
        limit: int = 20,
        time_range: str = "medium_term",
    ):
        return self._get(
            "/me/top/artists",
            params={
                "limit": limit,
                "time_range": time_range,
            },
        )

    def get_top_tracks(
        self,
        limit: int = 20,
        time_range: str = "medium_term",
    ):
        return self._get(
            "/me/top/tracks",
            params={
                "limit": limit,
                "time_range": time_range,
            },
        )

    def get_recently_played(self, limit: int = 20):
        return self._get(
            "/me/player/recently-played",
            params={
                "limit": limit,
            },
        )