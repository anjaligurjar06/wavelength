from shared.models import User, UserMusicProfile
from sqlalchemy.orm import Session

from music_ingestion.spotify_client import SpotifyClient


def sync_user_music_profile(
    db: Session,
    user: User,
    access_token: str,
    time_window: str = "medium_term",
) -> UserMusicProfile:
    """Fetch fresh Spotify data for a user and upsert their UserMusicProfile."""
    client = SpotifyClient(access_token)

    top_artists_response = client.get_top_artists(time_range=time_window)
    top_tracks_response = client.get_top_tracks(time_range=time_window)

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