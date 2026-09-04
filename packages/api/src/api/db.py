from collections.abc import Generator

from shared.db import get_sessionmaker
from sqlalchemy.orm import Session

from api.config import settings

SessionLocal = get_sessionmaker(settings.database_url)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
