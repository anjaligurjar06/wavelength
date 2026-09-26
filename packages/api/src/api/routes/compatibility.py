from compatibility_engine.service import (
    get_score_breakdown,
    get_score_breakdown_explanation,
    get_stored_compatibility_score,
    recompute_compatibility_score,
)
from fastapi import APIRouter, Depends, HTTPException
from shared.models import User
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user

router = APIRouter(prefix="/compatibility", tags=["compatibility"])


@router.get("/score/{candidate_id}")
def get_score(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        record = get_stored_compatibility_score(db, user.id, candidate_id)
    except ValueError:
        try:
            record = recompute_compatibility_score(db, user.id, candidate_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "user_id": user.id,
        "candidate_id": candidate_id,
        "score": record.score,
    }


@router.get("/score/{candidate_id}/breakdown")
def get_breakdown(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        breakdown = get_score_breakdown(db, user.id, candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return breakdown

@router.get("/score/{candidate_id}/explanation")
def get_explanation(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        explanation = get_score_breakdown_explanation(
            db,
            user.id,
            candidate_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return explanation


@router.post("/recompute")
def recompute_score(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        record = recompute_compatibility_score(db, user.id, candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "user_id": user.id,
        "candidate_id": candidate_id,
        "score": record.score,
    }
