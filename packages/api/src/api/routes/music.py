from fastapi import APIRouter, Depends, HTTPException
from music_ingestion.sync import (
    sync_manual_music_profile,
    sync_recently_played,
    sync_top_artists,
    sync_top_tracks,
)
from pydantic import BaseModel
from shared.models import User, UserMusicProfile
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user

router = APIRouter(prefix="/music", tags=["music"])


@router.post("/sync")
def sync_music(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not user.spotify_access_token:
        raise HTTPException(
            status_code=400, detail="No Spotify account connected for this user"
        )

    sync_top_artists(
        db,
        user,
        user.spotify_access_token,
    )

    sync_top_tracks(
        db,
        user,
        user.spotify_access_token,
    )

    sync_recently_played(
        db,
        user,
        user.spotify_access_token,
    )

    return {"status": "synced"}


@router.get("/profile")
def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    profile = db.query(UserMusicProfile).filter_by(user_id=user.id).one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="No music profile found. Sync first.")
    return {
    "top_artists": profile.top_artists,
    "top_tracks": profile.top_tracks,
    "recently_played": profile.recently_played,
    "top_genres": profile.top_genres,
    "time_window": profile.time_window,
    "is_stale": profile.is_stale,
}


@router.get("/top-artists")
def get_top_artists(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    profile = db.query(UserMusicProfile).filter_by(user_id=user.id).one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="No music profile found. Sync first.")
    return profile.top_artists

@router.get("/top-tracks")
def get_top_tracks(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    profile = db.query(UserMusicProfile).filter_by(user_id=user.id).one_or_none()

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="No music profile found. Sync first.",
        )

    return profile.top_tracks

@router.get("/recently-played")
def get_recently_played(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    profile = db.query(UserMusicProfile).filter_by(user_id=user.id).one_or_none()

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="No music profile found. Sync first.",
        )

    return profile.recently_played


@router.get("/genres")
def get_genres(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    profile = db.query(UserMusicProfile).filter_by(user_id=user.id).one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="No music profile found. Sync first.")
    return profile.top_genres

class ManualEntryRequest(BaseModel):
    artists: list[str]
    genres: list[str]


@router.post("/manual-entry")
def manual_entry(
    payload: ManualEntryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    top_artists = {
        "items": [
            {"id": None, "name": name, "genres": []}
            for name in payload.artists
        ]
    }

    top_genres = {
        "genres": sorted(set(payload.genres))
    }

    sync_manual_music_profile(
        db=db,
        user=user,
        top_artists=top_artists,
        top_genres=top_genres,
    )

    return {"status": "saved"}