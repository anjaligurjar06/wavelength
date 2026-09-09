from shared.models import User, UserMusicProfile
from sqlalchemy.orm import Session

from music_ingestion.spotify_client import SpotifyClient

TIME_WINDOW_MAP = {
    "4w": "short_term",
    "6m": "medium_term",
    "all": "long_term",
}
def map_time_window(time_window: str) -> str:
    if time_window not in TIME_WINDOW_MAP:
        raise ValueError(
            "Invalid time window. Use one of: 4w, 6m, all."
        )
    return TIME_WINDOW_MAP[time_window]


def sync_user_music_profile(
    db: Session,
    user: User,
    access_token: str,
    time_window: str = "6m",
) -> UserMusicProfile:
    """Fetch fresh Spotify data for a user and upsert their UserMusicProfile."""
    client = SpotifyClient(access_token)

    spotify_time_window = map_time_window(time_window)
    top_artists_response = client.get_top_artists(
    time_range=spotify_time_window
)
    top_tracks_response = client.get_top_tracks(
    time_range=spotify_time_window
)
    

    top_artists = {
        "items": [
            {"id": a["id"], "name": a["name"], "genres": a.get("genres", [])}
            for a in top_artists_response.get("items", [])
        ]
    }
    top_tracks = {
        "items": [
            {
                "id": t["id"],
                "name": t["name"],
                "artist": t["artists"][0]["name"] if t.get("artists") else None,
            }
            for t in top_tracks_response.get("items", [])
        ]
    }
    top_genres = {
        "genres": sorted(
            {
                genre
                for artist in top_artists_response.get("items", [])
                for genre in artist.get("genres", [])
            }
        )
    }

    profile = db.query(UserMusicProfile).filter_by(user_id=user.id).one_or_none()
    if profile is None:
        profile = UserMusicProfile(user_id=user.id)
        db.add(profile)

    profile.top_artists = top_artists
    profile.top_tracks = top_tracks
    profile.top_genres = top_genres
    profile.time_window = time_window
    profile.is_stale = False

    db.commit()
    db.refresh(profile)
    return profile
def sync_top_artists(
    db: Session,
    user: User,
    access_token: str,
    time_window: str = "6m",
) -> UserMusicProfile:
    """Fetch and sync a user's top Spotify artists."""

    client = SpotifyClient(access_token)

    spotify_time_window = map_time_window(time_window)

    top_artists_response = client.get_top_artists(
    time_range=spotify_time_window
)

    top_artists = {
        "items": [
            {
                "id": artist["id"],
                "name": artist["name"],
                "genres": artist.get("genres", []),
            }
            for artist in top_artists_response.get("items", [])
        ]
    }

    top_genres = {
        "genres": sorted(
            {
                genre
                for artist in top_artists_response.get("items", [])
                for genre in artist.get("genres", [])
            }
        )
    }

    profile = (
        db.query(UserMusicProfile)
        .filter_by(user_id=user.id)
        .one_or_none()
    )

    if profile is None:
        profile = UserMusicProfile(user_id=user.id)
        db.add(profile)

    profile.top_artists = top_artists
    profile.top_genres = top_genres
    profile.time_window = time_window
    profile.is_stale = False

    db.commit()
    db.refresh(profile)

    return profile
def sync_top_tracks(
    db: Session,
    user: User,
    access_token: str,
    time_window: str = "6m",
) -> UserMusicProfile:
    """Fetch and sync a user's top Spotify tracks."""

    client = SpotifyClient(access_token)

    spotify_time_window = map_time_window(time_window)
    top_tracks_response = client.get_top_tracks(
    time_range=spotify_time_window
)

    top_tracks = {
        "items": [
            {
                "id": track["id"],
                "name": track["name"],
                "artist": (
                    track["artists"][0]["name"]
                    if track.get("artists")
                    else None
                ),
            }
            for track in top_tracks_response.get("items", [])
        ]
    }

    profile = (
        db.query(UserMusicProfile)
        .filter_by(user_id=user.id)
        .one_or_none()
    )

    if profile is None:
        profile = UserMusicProfile(user_id=user.id)
        db.add(profile)

    profile.top_tracks = top_tracks
    profile.time_window = time_window
    profile.is_stale = False

    db.commit()
    db.refresh(profile)

    return profile
def sync_recently_played(
    db: Session,
    user: User,
    access_token: str,
) -> UserMusicProfile:
    """Fetch and sync a user's recently played Spotify tracks."""

    client = SpotifyClient(access_token)

    recently_played_response = client.get_recently_played()

    recently_played = {
        "items": [
            {
                "id": item["track"]["id"],
                "name": item["track"]["name"],
                "artist": (
                    item["track"]["artists"][0]["name"]
                    if item["track"].get("artists")
                    else None
                ),
                "played_at": item.get("played_at"),
            }
            for item in recently_played_response.get("items", [])
        ]
    }

    profile = (
        db.query(UserMusicProfile)
        .filter_by(user_id=user.id)
        .one_or_none()
    )

    if profile is None:
        profile = UserMusicProfile(user_id=user.id)
        db.add(profile)

    profile.recently_played = recently_played
    profile.is_stale = False

    db.commit()
    db.refresh(profile)

    return profile
def sync_manual_music_profile(
    db: Session,
    user: User,
    top_artists: dict | None = None,
    top_tracks: dict | None = None,
    top_genres: dict | None = None,
) -> UserMusicProfile:
    """Save manually entered music data for a user."""

    profile = (
        db.query(UserMusicProfile)
        .filter_by(user_id=user.id)
        .one_or_none()
    )

    if profile is None:
        profile = UserMusicProfile(user_id=user.id)
        db.add(profile)

    if top_artists is not None:
        profile.top_artists = top_artists

    if top_tracks is not None:
        profile.top_tracks = top_tracks

    if top_genres is not None:
        profile.top_genres = top_genres

    profile.is_stale = False

    db.commit()
    db.refresh(profile)

    return profile
