from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.models.users import User
from app.services.auth_service import decode_auth_token


bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

    token = credentials.credentials

    try:
        user_id = decode_auth_token(token)

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )

    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user
