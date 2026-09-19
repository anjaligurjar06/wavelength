import os

os.environ.setdefault("SPOTIFY_CLIENT_ID", "test-client-id")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/auth/spotify/callback")
os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-long-enough-for-hs256")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest  # noqa: E402
from api.db import SessionLocal, engine  # noqa: E402
from shared.models import Base  # noqa: E402

Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
