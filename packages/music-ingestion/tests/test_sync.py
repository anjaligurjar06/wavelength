import pytest
from music_ingestion.sync import (
    map_time_window,
    sync_manual_music_profile,
    sync_recently_played,
    sync_top_artists,
    sync_top_tracks,
)
from shared.models import User


def test_sync_top_artists(db_session, monkeypatch):
    
    user = User(
        email="test@example.com",
        display_name="Test User",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    
    fake_response = {
        "items": [
            {
                "id": "artist1",
                "name": "Artist One",
                "genres": ["pop", "dance"],
            },
            {
                "id": "artist2",
                "name": "Artist Two",
                "genres": ["rock"],
            },
        ]
    }

    
    class FakeSpotifyClient:
        def __init__(self, access_token):
            self.access_token = access_token

        def get_top_artists(self, time_range="medium_term"):
            return fake_response

    monkeypatch.setattr(
        "music_ingestion.sync.SpotifyClient",
        FakeSpotifyClient,
    )

   
    profile = sync_top_artists(
        db=db_session,
        user=user,
        access_token="fake-token",
        time_window="6m",
    )

    
    assert profile.top_artists == {
        "items": [
            {
                "id": "artist1",
                "name": "Artist One",
                "genres": ["pop", "dance"],
            },
            {
                "id": "artist2",
                "name": "Artist Two",
                "genres": ["rock"],
            },
        ]
    }

    assert profile.top_genres == {
        "genres": ["dance", "pop", "rock"]
    }

   
    assert profile.time_window == "6m"

    
    assert profile.is_stale is False
def test_sync_top_artists_updates_existing_profile(db_session, monkeypatch):
    user = User(
        email="update@example.com",
        display_name="Update User",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    class FakeSpotifyClient:
        def __init__(self, access_token):
            self.access_token = access_token

        def get_top_artists(self, time_range="medium_term"):
            return {
                "items": [
                    {
                        "id": "artist1",
                        "name": "Artist One",
                        "genres": ["pop"],
                    }
                ]
            }

    monkeypatch.setattr(
        "music_ingestion.sync.SpotifyClient",
        FakeSpotifyClient,
    )

    profile1 = sync_top_artists(
        db=db_session,
        user=user,
        access_token="fake-token",
        time_window="6m",
    )

    profile2 = sync_top_artists(
        db=db_session,
        user=user,
        access_token="fake-token",
        time_window="6m",
    )

    assert profile1.id == profile2.id
    assert profile2.top_artists["items"][0]["name"] == "Artist One"
def test_sync_top_tracks(db_session, monkeypatch):
    user = User(
        email="tracks@example.com",
        display_name="Tracks User",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    fake_response = {
        "items": [
            {
                "id": "track1",
                "name": "Song One",
                "artists": [
                    {
                        "id": "artist1",
                        "name": "Artist One",
                    }
                ],
            },
            {
                "id": "track2",
                "name": "Song Two",
                "artists": [
                    {
                        "id": "artist2",
                        "name": "Artist Two",
                    }
                ],
            },
        ]
    }

    class FakeSpotifyClient:
        def __init__(self, access_token):
            self.access_token = access_token

        def get_top_tracks(self, time_range="medium_term"):
            return fake_response

    monkeypatch.setattr(
        "music_ingestion.sync.SpotifyClient",
        FakeSpotifyClient,
    )

    profile = sync_top_tracks(
        db=db_session,
        user=user,
        access_token="fake-token",
        time_window="6m",
    )

    assert profile.top_tracks == {
        "items": [
            {
                "id": "track1",
                "name": "Song One",
                "artist": "Artist One",
            },
            {
                "id": "track2",
                "name": "Song Two",
                "artist": "Artist Two",
            },
        ]
    }

    assert profile.time_window == "6m"
    assert profile.is_stale is False
def test_sync_recently_played(db_session, monkeypatch):
    user = User(
        email="recent@example.com",
        display_name="Recent User",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    fake_response = {
        "items": [
            {
                "track": {
                    "id": "track1",
                    "name": "Recent Song",
                    "artists": [
                        {
                            "id": "artist1",
                            "name": "Recent Artist",
                        }
                    ],
                },
                "played_at": "2026-09-10T10:00:00Z",
            }
        ]
    }

    class FakeSpotifyClient:
        def __init__(self, access_token):
            self.access_token = access_token

        def get_recently_played(self, limit=20):
            return fake_response

    monkeypatch.setattr(
        "music_ingestion.sync.SpotifyClient",
        FakeSpotifyClient,
    )

    profile = sync_recently_played(
        db=db_session,
        user=user,
        access_token="fake-token",
    )

    assert profile.recently_played == {
        "items": [
            {
                "id": "track1",
                "name": "Recent Song",
                "artist": "Recent Artist",
                "played_at": "2026-09-10T10:00:00Z",
            }
        ]
    }

    assert profile.is_stale is False
def test_sync_manual_music_profile(db_session):
    user = User(
        email="manual@example.com",
        display_name="Manual User",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    top_artists = {
        "items": [
            {
                "id": "artist1",
                "name": "Artist One",
                "genres": ["pop"],
            }
        ]
    }

    top_tracks = {
        "items": [
            {
                "id": "track1",
                "name": "Song One",
                "artist": "Artist One",
            }
        ]
    }

    top_genres = {
        "genres": ["pop"]
    }

    profile = sync_manual_music_profile(
        db=db_session,
        user=user,
        top_artists=top_artists,
        top_tracks=top_tracks,
        top_genres=top_genres,
    )

    assert profile.top_artists == top_artists
    assert profile.top_tracks == top_tracks
    assert profile.top_genres == top_genres
    assert profile.is_stale is False
def test_sync_manual_music_profile_keeps_existing_data(db_session):
    user = User(
        email="partial@example.com",
        display_name="Partial User",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    profile = sync_manual_music_profile(
        db=db_session,
        user=user,
        top_tracks={
            "items": [
                {
                    "id": "old-track",
                    "name": "Old Song",
                    "artist": "Old Artist",
                }
            ]
        },
    )

    profile = sync_manual_music_profile(
        db=db_session,
        user=user,
        top_artists={
            "items": [
                {
                    "id": "new-artist",
                    "name": "New Artist",
                    "genres": ["rock"],
                }
            ]
        },
    )

    assert profile.top_artists["items"][0]["name"] == "New Artist"

    assert profile.top_tracks["items"][0]["name"] == "Old Song"
def test_map_time_window():
    assert map_time_window("4w") == "short_term"
    assert map_time_window("6m") == "medium_term"
    assert map_time_window("all") == "long_term"
def test_map_time_window_invalid():
    with pytest.raises(ValueError):
        map_time_window("invalid")