from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.dependencies import get_db
from app.models.users import User
from app.schemas.auth import (
    AuthResponse,
    CurrentUserResponse,
    LoginRequest,
    RegisterRequest,
)
from app.services.auth_service import create_auth_token
from app.services.password_service import (
    hash_password,
    verify_password,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"],
)

@router.post(
    "/register",
    response_model=AuthResponse,
)
async def register(
        data : RegisterRequest,
        db: AsyncSession = Depends(get_db),
):
    existing_user = await db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    token = create_auth_token(user.id)

    return {
        "access_token" : token,
        "token_type" : "bearer",
    }



@router.post(
    "/login",
    response_model=AuthResponse,
)
async def login(
        data : LoginRequest,
        db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(
        select(User).where(User.email == data.email)
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_auth_token(user.id)

    return {
        "access_token" : token,
        "token_type" : "bearer",
    }

@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
async def me(
    current_user: User = Depends(get_current_user),
):
    return current_user
