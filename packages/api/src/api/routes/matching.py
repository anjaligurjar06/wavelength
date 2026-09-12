from fastapi import APIRouter, Depends
from pydantic import BaseModel
from shared.models import User
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user

router = APIRouter(prefix="/matching", tags=["matching"])


class FiltersResponse(BaseModel):
    latitude: float | None
    longitude: float | None
    max_distance_km: float


class UpdateFiltersRequest(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    max_distance_km: float | None = None


@router.get("/filters")
def get_filters(user: User = Depends(get_current_user)) -> FiltersResponse:
    return FiltersResponse(
        latitude=user.latitude,
        longitude=user.longitude,
        max_distance_km=user.max_distance_km,
    )


@router.put("/filters")
def update_filters(
    payload: UpdateFiltersRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FiltersResponse:
    if payload.latitude is not None:
        user.latitude = payload.latitude
    if payload.longitude is not None:
        user.longitude = payload.longitude
    if payload.max_distance_km is not None:
        user.max_distance_km = payload.max_distance_km

    db.commit()
    db.refresh(user)

    return FiltersResponse(
        latitude=user.latitude,
        longitude=user.longitude,
        max_distance_km=user.max_distance_km,
    )
