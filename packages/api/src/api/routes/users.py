from fastapi import APIRouter, Depends
from shared.models import User

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
