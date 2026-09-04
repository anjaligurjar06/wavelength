from collections.abc import Generator

from shared.db import get_engine
from sqlalchemy.orm import Session, sessionmaker

from api.config import settings

engine = get_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
