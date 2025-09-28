from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_session
from app.models import User
from app.schemas.user_schema import SignUpRequest, LoginRequest, Token
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Token, status_code=201)
async def signup(payload: SignUpRequest, session: AsyncSession = Depends(get_session)):
    try:
        # Check username uniqueness
        username_result = await session.exec(
            select(User).where(User.username == payload.username)
        )
        if username_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="ชื่อผู้ใช้นี้ถูกใช้แล้ว")

        # Check email uniqueness
        email_result = await session.exec(
            select(User).where(User.email == payload.email)
        )
        if email_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="อีเมลนี้ถูกใช้แล้ว")

        # Validate foreign key constraints if provided
        if payload.faculty_id is not None:
            from app.models.faculty_model import Faculty

            faculty_result = await session.exec(
                select(Faculty).where(Faculty.id == payload.faculty_id)
            )
            if not faculty_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="กรุณากรอกคณะให้ถูกต้อง")

        if payload.role_id is not None:
            from app.models.role_model import Role

            role_result = await session.exec(
                select(Role).where(Role.id == payload.role_id)
            )
            if not role_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="กรุณากรอกบทบาทให้ถูกต้อง")

        # Create user with validated data
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
        await session.refresh(
            user
        )  # Refresh the user object to reattach it to the session

        # Get username safely after refresh
        username = user.username
        token = create_access_token({"sub": username})
        return Token(access_token=token)

    except HTTPException:
        # Re-raise HTTPExceptions (validation errors)
        raise
    except Exception as e:
        # Handle database errors and other unexpected errors
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")


@router.post("/signin", response_model=Token)
async def signin(creds: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User).where(User.email == creds.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง",
        )
    # Access username before any potential session issues
    username = user.username
    token = create_access_token({"sub": username})
    return Token(access_token=token)
