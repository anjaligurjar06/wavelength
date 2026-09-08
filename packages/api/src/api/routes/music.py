from fastapi import APIRouter, Depends, HTTPException
from music_ingestion.sync import sync_user_music_profile
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
    sync_user_music_profile(db, user, user.spotify_access_token)
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
    profile = db.query(UserMusicProfile).filter_by(user_id=user.id).one_or_none()
    if profile is None:
        profile = UserMusicProfile(user_id=user.id)
        db.add(profile)

    profile.top_artists = {
        "items": [{"id": None, "name": name, "genres": []} for name in payload.artists]
    }
    profile.top_genres = {"genres": sorted(set(payload.genres))}
    profile.time_window = "manual"
    profile.is_stale = False

    db.commit()
    return {"status": "saved"}
