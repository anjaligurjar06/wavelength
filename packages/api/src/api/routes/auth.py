import logging
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
logger = logging.getLogger("wavelength.auth")

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
def callback(code: str, db: Session = Depends(get_db)) -> RedirectResponse:
    try:
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
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        logger.error("Spotify token exchange unreachable: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Spotify is unreachable") from exc

    if token_response.status_code != 200:
        logger.warning(
            "Spotify token exchange failed: upstream_status=%s",
            token_response.status_code,
        )
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    access_token = token_response.json()["access_token"]

    try:
        profile_response = httpx.get(
            SPOTIFY_ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        logger.error("Spotify profile fetch unreachable: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Spotify is unreachable") from exc

    if profile_response.status_code != 200:
        logger.warning(
            "Spotify profile fetch failed: upstream_status=%s",
            profile_response.status_code,
        )
        raise HTTPException(status_code=400, detail="Failed to fetch Spotify profile")

    profile = profile_response.json()
    spotify_id = profile["id"]
    email = profile.get("email", f"{spotify_id}@spotify.placeholder")
    display_name = profile.get("display_name", spotify_id)

    refresh_token = token_response.json().get("refresh_token")

    user = db.scalar(select(User).where(User.spotify_id == spotify_id))
    if user is None:
        user = User(
            spotify_id=spotify_id,
            email=email,
            display_name=display_name,
            spotify_access_token=access_token,
            spotify_refresh_token=refresh_token,
        )
        db.add(user)
    else:
        user.email = email
        user.display_name = display_name
        user.spotify_access_token = access_token
        if refresh_token:
            user.spotify_refresh_token = refresh_token
    db.commit()
    db.refresh(user)

    jwt_token = create_access_token(user.id)
    redirect_url = f"{settings.frontend_url}/auth/callback?token={jwt_token}&user_id={user.id}"
    return RedirectResponse(redirect_url)