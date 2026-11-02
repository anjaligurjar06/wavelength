import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from shared.models import User
from sqlalchemy.orm import Session

from api.config import settings
from api.db import get_db
from api.jwt_utils import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    cookie_token = request.cookies.get("wavelength_session")
    token = credentials.credentials if credentials is not None else cookie_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    if credentials is None and request.method.upper() in UNSAFE_METHODS:
        origin = request.headers.get("origin")
        # A browser cannot set Origin arbitrarily. Reject missing/foreign origins
        # for cookie-authenticated mutations, including form submissions.
        allowed = settings.frontend_url.rstrip("/")
        if origin != allowed:
            raise HTTPException(status_code=403, detail="CSRF origin check failed")

    try:
        user_id = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
