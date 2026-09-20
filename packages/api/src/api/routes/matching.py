from chat.service import create_thread_for_match
from fastapi import APIRouter, Depends
from matching.feed import build_ranked_feed
from matching.state_machine import record_interaction
from pydantic import BaseModel
from redis import Redis
from shared.models import Match, User
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user
from api.redis import get_redis

router = APIRouter(prefix="/matching", tags=["matching"])


class FiltersResponse(BaseModel):
    latitude: float | None
    longitude: float | None
    max_distance_km: float


class UpdateFiltersRequest(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    max_distance_km: float | None = None


class InteractionResponse(BaseModel):
    action: str
    matched: bool
    match_id: str | None
    thread_id: str | None


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


@router.get("/feed")
def get_matching_feed(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> list[dict]:
    """Return distance-filtered candidates ranked by compatibility."""

    candidates = (
        db.query(User)
        .filter(User.id != user.id)
        .all()
    )

    ranked_candidates = build_ranked_feed(
        db,
        redis_client,
        user,
        candidates,
    )

    return [
        {
            "candidate_id": candidate.user_id,
            "display_name": candidate.display_name,
            "score": candidate.score,
        }
        for candidate in ranked_candidates
    ]


@router.post("/{candidate_id}/like")
def like_candidate(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InteractionResponse:
    result = record_interaction(
        db,
        user.id,
        candidate_id,
        "like",
    )

    db.commit()

    thread_id = None

    if result.matched and result.match_id is not None:
        match = db.get(Match, result.match_id)
        if match is not None:
            thread = create_thread_for_match(db, match)
            thread_id = thread.id

    return InteractionResponse(
        action=result.action,
        matched=result.matched,
        match_id=result.match_id,
        thread_id=thread_id,
    )


@router.post("/{candidate_id}/pass")
def pass_candidate(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InteractionResponse:
    result = record_interaction(
        db,
        user.id,
        candidate_id,
        "pass",
    )

    db.commit()

    return InteractionResponse(
        action=result.action,
        matched=result.matched,
        match_id=result.match_id,
        thread_id=None,
    )