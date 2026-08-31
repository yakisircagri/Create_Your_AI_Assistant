from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.models.users import User
from app.schemas.user import UserCreate, UserResponse
from app.services.password_service import hash_password

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)

@router.post("", response_model = UserResponse)
async def create_user(
        data: UserCreate,
        db: AsyncSession = Depends(get_db),
):
    existing_user = await db.scalar(
        select(User).where(
            User.email == data.email,
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user