from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import get_session, User
from app.schemas.user_schema import SignUpRequest, LoginRequest, Token
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Token, status_code=201)
async def signup(payload: SignUpRequest, session: AsyncSession = Depends(get_session)):
    # Check username uniqueness
    username_result = await session.execute(
        select(User).where(User.username == payload.username)
    )
    if username_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check email uniqueness
    email_result = await session.execute(
        select(User).where(User.email == payload.email)
    )
    if email_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        username=payload.username,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        birth_date=payload.birth_date,
        faculty_id=payload.faculty_id,
        year_of_study=payload.year_of_study,
        role_id=payload.role_id,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    await session.commit()
    token = create_access_token({"sub": user.username})
    return Token(access_token=token)


@router.post("/signin", response_model=Token)
async def signin(creds: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == creds.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token({"sub": user.username})
    return Token(access_token=token)
