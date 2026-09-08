from fastapi import APIRouter, Depends
from pydantic import BaseModel
from shared.models import User
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def read_current_user(user: User = Depends(get_current_user)) -> dict[str, str | None]:
    return {
        "id": user.id,
        "spotify_id": user.spotify_id,
        "email": user.email,
        "display_name": user.display_name,
    }

class UpdateUserRequest(BaseModel):
    display_name: str | None = None
    email: str | None = None


@router.patch("/me")
def update_current_user(
    payload: UpdateUserRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.email is not None:
        user.email = payload.email

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "spotify_id": user.spotify_id,
        "email": user.email,
        "display_name": user.display_name,
    }
