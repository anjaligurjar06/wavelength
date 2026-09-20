from dataclasses import dataclass
from typing import Literal

from shared.models import Match, UserInteraction
from sqlalchemy import select
from sqlalchemy.orm import Session

Action = Literal["like", "pass"]


@dataclass(frozen=True)
class InteractionResult:
    action: Action
    matched: bool
    match_id: str | None


def record_interaction(
    db: Session,
    user_id: str,
    target_user_id: str,
    action: Action,
) -> InteractionResult:
    if user_id == target_user_id:
        raise ValueError("A user cannot interact with themselves")

    interaction = db.scalar(
        select(UserInteraction).where(
            UserInteraction.user_id == user_id,
            UserInteraction.target_user_id == target_user_id,
        )
    )

    if interaction is None:
        interaction = UserInteraction(
            user_id=user_id,
            target_user_id=target_user_id,
            action=action,
        )
        db.add(interaction)
    else:
        interaction.action = action

    db.flush()

    if action == "pass":
        return InteractionResult(
            action="pass",
            matched=False,
            match_id=None,
        )

    reverse_like = db.scalar(
        select(UserInteraction).where(
            UserInteraction.user_id == target_user_id,
            UserInteraction.target_user_id == user_id,
            UserInteraction.action == "like",
        )
    )

    if reverse_like is None:
        return InteractionResult(
            action="like",
            matched=False,
            match_id=None,
        )

    user_a_id, user_b_id = sorted((user_id, target_user_id))

    existing_match = db.scalar(
        select(Match).where(
            Match.user_a_id == user_a_id,
            Match.user_b_id == user_b_id,
        )
    )

    if existing_match is not None:
        return InteractionResult(
            action="like",
            matched=True,
            match_id=existing_match.id,
        )

    match = Match(
        user_a_id=user_a_id,
        user_b_id=user_b_id,
    )
    db.add(match)
    db.flush()

    return InteractionResult(
        action="like",
        matched=True,
        match_id=match.id,
    )