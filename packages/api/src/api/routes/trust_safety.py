from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from shared.models import User
from sqlalchemy.orm import Session
from trust_safety.service import block_user, report_user

from api.db import get_db
from api.deps import get_current_user

router = APIRouter(prefix="/trust-safety", tags=["trust-safety"])


class ReportRequest(BaseModel):
    reported_user_id: str
    reason: str
    details: str | None = None


class ReportResponse(BaseModel):
    id: str
    reason: str


class BlockRequest(BaseModel):
    blocked_user_id: str


class BlockResponse(BaseModel):
    id: str
    blocked_user_id: str


@router.post("/report")
def report(
    payload: ReportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportResponse:
    try:
        result = report_user(
            db,
            user.id,
            payload.reported_user_id,
            payload.reason,
            payload.details,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReportResponse(id=result.id, reason=result.reason)


@router.post("/block")
def block(
    payload: BlockRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BlockResponse:
    try:
        result = block_user(db, user.id, payload.blocked_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BlockResponse(id=result.id, blocked_user_id=result.blocked_user_id)
