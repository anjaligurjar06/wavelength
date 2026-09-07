from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass

def _uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    spotify_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    display_name: Mapped[str] = mapped_column(String(255))
    spotify_access_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    spotify_refresh_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    music_profile: Mapped[UserMusicProfile | None] = relationship(
        back_populates="user", uselist=False
    )


class UserMusicProfile(Base):
    __tablename__ = "user_music_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    top_artists: Mapped[dict] = mapped_column(JSON, default=dict)
    top_tracks: Mapped[dict] = mapped_column(JSON, default=dict)
    top_genres: Mapped[dict] = mapped_column(JSON, default=dict)
    time_window: Mapped[str] = mapped_column(String(16), default="6m")
    is_stale: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="music_profile")


class ArtistGenreCache(Base):
    __tablename__ = "artist_genre_cache"

    artist_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    genres: Mapped[list[str]] = mapped_column(JSON, default=list)
    cached_at: Mapped[datetime] = mapped_column(server_default=func.now())


class CompatibilityScore(Base):
    __tablename__ = "compatibility_scores"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id", name="uq_score_pair"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_a_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    user_b_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    score: Mapped[float] = mapped_column()
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id", name="uq_match_pair"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_a_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    user_b_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    matched_at: Mapped[datetime] = mapped_column(server_default=func.now())

    thread: Mapped[Thread | None] = relationship(back_populates="match", uselist=False)


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    match: Mapped[Match] = relationship(back_populates="thread")
    messages: Mapped[list[Message]] = relationship(back_populates="thread")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    thread_id: Mapped[str] = mapped_column(ForeignKey("threads.id"))
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(String(4000))
    sent_at: Mapped[datetime] = mapped_column(server_default=func.now())

    thread: Mapped[Thread] = relationship(back_populates="messages")
