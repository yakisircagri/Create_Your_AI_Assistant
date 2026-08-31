from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings



def create_auth_token(
        user_id: int,
) -> str :

    expires_at = (
        datetime.now(timezone.utc) +
        timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    pay_load = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(
        pay_load,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_auth_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if not user_id:
            raise InvalidTokenError()

        return int(user_id)

    except (InvalidTokenError, ValueError):
        raise ValueError("Invalid or expired token")






