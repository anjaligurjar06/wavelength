import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from shared.models import User
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import settings
from api.db import get_db
from api.jwt_utils import create_access_token

router = APIRouter(prefix="/auth/spotify", tags=["auth"])

SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_ME_URL = "https://api.spotify.com/v1/me"
SCOPES = "user-read-email user-top-read user-read-recently-played"


@router.get("/authorize")
def authorize() -> RedirectResponse:
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": SCOPES,
        "state": state,
    }
    url = f"{SPOTIFY_AUTHORIZE_URL}?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/callback")
def callback(code: str, db: Session = Depends(get_db)) -> dict[str, str]:
    token_response = httpx.post(
        SPOTIFY_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.spotify_redirect_uri,
            "client_id": settings.spotify_client_id,
            "client_secret": settings.spotify_client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    access_token = token_response.json()["access_token"]

    profile_response = httpx.get(
        SPOTIFY_ME_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if profile_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch Spotify profile")

    profile = profile_response.json()
    spotify_id = profile["id"]
    email = profile.get("email", f"{spotify_id}@spotify.placeholder")
    display_name = profile.get("display_name", spotify_id)

    user = db.scalar(select(User).where(User.spotify_id == spotify_id))
    if user is None:
        user = User(spotify_id=spotify_id, email=email, display_name=display_name)
        db.add(user)
    else:
        user.email = email
        user.display_name = display_name
    db.commit()
    db.refresh(user)

    jwt_token = create_access_token(user.id)
    return {"access_token": jwt_token, "user_id": user.id}
