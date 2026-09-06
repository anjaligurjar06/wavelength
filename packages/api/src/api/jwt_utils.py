from datetime import UTC, datetime, timedelta

import jwt

from api.config import settings

ALGORITHM = "HS256"
EXPIRY_HOURS = 24 * 7  # 1 week


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(hours=EXPIRY_HOURS),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Returns the user_id (sub claim). Raises jwt exceptions if invalid/expired."""
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    return payload["sub"]
