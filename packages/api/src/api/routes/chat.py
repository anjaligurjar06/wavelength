from datetime import UTC, datetime

from chat.rate_limit import check_rate_limit
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from redis import Redis
from shared.models import Match, Message, Thread, User
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user
from api.redis import get_redis

router = APIRouter(prefix="/chat", tags=["chat"])


class ThreadResponse(BaseModel):
    id: str
    other_user_id: str
    other_display_name: str
    last_message: str | None
    last_message_at: datetime | None


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    content: str
    sent_at: datetime


class SendMessageRequest(BaseModel):
    content: str


def _get_thread_or_404(db: Session, thread_id: str) -> Thread:
    thread = db.query(Thread).filter_by(id=thread_id).one_or_none()
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


def _assert_participant(thread: Thread, user: User) -> Match:
    match = thread.match
    if match is None or user.id not in (match.user_a_id, match.user_b_id):
        raise HTTPException(status_code=403, detail="Not a participant in this thread")
    return match


@router.get("/threads")
def list_threads(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ThreadResponse]:
    threads = (
        db.query(Thread)
        .join(Match, Thread.match_id == Match.id)
        .filter((Match.user_a_id == user.id) | (Match.user_b_id == user.id))
        .all()
    )

    result = []
    for t in threads:
        match = t.match
        other_id = match.user_b_id if match.user_a_id == user.id else match.user_a_id
        other_user = db.query(User).filter_by(id=other_id).one_or_none()
        if other_user is None:
            continue

        last_msg = (
            db.query(Message)
            .filter_by(thread_id=t.id)
            .order_by(Message.sent_at.desc())
            .first()
        )

        result.append(
            ThreadResponse(
                id=t.id,
                other_user_id=other_id,
                other_display_name=other_user.display_name,
                last_message=last_msg.content if last_msg else None,
                last_message_at=last_msg.sent_at if last_msg else None,
            )
        )

    result.sort(
        key=lambda t: t.last_message_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return result


@router.get("/threads/{thread_id}/messages")
def get_messages(
    thread_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MessageResponse]:
    thread = _get_thread_or_404(db, thread_id)
    _assert_participant(thread, user)

    messages = (
        db.query(Message)
        .filter_by(thread_id=thread_id)
        .order_by(Message.sent_at.asc())
        .all()
    )
    return [
        MessageResponse(id=m.id, sender_id=m.sender_id, content=m.content, sent_at=m.sent_at)
        for m in messages
    ]


@router.post("/threads/{thread_id}/messages")
def send_message(
    thread_id: str,
    payload: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> MessageResponse:
    thread = _get_thread_or_404(db, thread_id)
    _assert_participant(thread, user)

    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if not check_rate_limit(redis_client, user.id):
        raise HTTPException(
            status_code=429,
            detail="You're sending messages too quickly. Please slow down.",
        )

    message = Message(
        thread_id=thread_id,
        sender_id=user.id,
        content=payload.content.strip(),
        sent_at=datetime.now(UTC),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return MessageResponse(
        id=message.id, sender_id=message.sender_id, content=message.content, sent_at=message.sent_at
    )
