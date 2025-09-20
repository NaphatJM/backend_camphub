from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import get_session, User
from app.schemas.user_schema import MeRead, MeUpdate
from app.core.deps import get_current_user
from app.core.security import verify_password, hash_password
from sqlalchemy.orm import joinedload
from uuid import uuid4
import os
from pathlib import Path


router = APIRouter(prefix="/user", tags=["user"])

UPLOAD_DIR = Path("static/profile_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="ไฟล์ต้องเป็นรูปภาพเท่านั้น")

    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="ไฟล์ต้องมีขนาดไม่เกิน 10MB")

    try:
        filename = f"{uuid4().hex}_{file.filename}"
        file_path = UPLOAD_DIR / filename

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        current_user.profile_image_url = f"/static/profile_images/{filename}"
        session.add(current_user)
        await session.commit()

        return {
            "message": "อัปโหลดรูปภาพสำเร็จ",
            "image_url": current_user.profile_image_url,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"เกิดข้อผิดพลาดในการอัปโหลดไฟล์: {str(e)}"
        )


@router.get("", response_model=MeRead)
async def get_me(current: User = Depends(get_current_user)):
    return MeRead(
        id=current.id,
        username=current.username,
        email=current.email,
        first_name=current.first_name,
        last_name=current.last_name,
        birth_date=current.birth_date,
        age=current.age,
        faculty_id=current.faculty_id,
        faculty_name=current.faculty.name if current.faculty else None,
        year_of_study=current.year_of_study,
        role_id=current.role_id,
        role_name=current.role.name if current.role else None,
        profile_image_url=current.profile_image_url,
    )


@router.get("/{user_id}", response_model=MeRead)
async def get_user_by_id(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(User)
        .options(joinedload(User.role), joinedload(User.faculty))
        .where(User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return MeRead(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        birth_date=user.birth_date,
        faculty_id=user.faculty_id,
        faculty_name=user.faculty.name if user.faculty else None,
        year_of_study=user.year_of_study,
        role_id=user.role_id,
        role_name=user.role.name if user.role else None,
        age=user.age,
        fullname=user.fullname,
        profile_image_url=user.profile_image_url,
    )


@router.put("", response_model=MeRead)
async def update_me(
    payload: MeUpdate,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check username uniqueness
    if payload.username and payload.username != current.username:
        username_result = await session.execute(
            select(User).where(User.username == payload.username)
        )
        if username_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists")
        current.username = payload.username

    # Check email uniqueness
    if payload.email and payload.email != current.email:
        email_result = await session.execute(
            select(User).where(User.email == payload.email)
        )
        if email_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists")
        current.email = payload.email

    # Update other fields
    if payload.first_name is not None:
        current.first_name = payload.first_name

    if payload.last_name is not None:
        current.last_name = payload.last_name

    if payload.birth_date is not None:
        current.birth_date = payload.birth_date

    if payload.faculty_id is not None:
        current.faculty_id = payload.faculty_id

    if payload.role_id is not None:
        current.role_id = payload.role_id

    if payload.year_of_study is not None:
        current.year_of_study = payload.year_of_study

    # Update password if provided
    if payload.new_password is not None:
        current.hashed_password = hash_password(payload.new_password)

    session.add(current)
    await session.commit()
    await session.refresh(current)

    return MeRead(
        id=current.id,
        username=current.username,
        email=current.email,
        first_name=current.first_name,
        last_name=current.last_name,
        birth_date=current.birth_date,
        age=current.age,
        faculty_id=current.faculty_id,
        faculty_name=current.faculty.name if current.faculty else None,
        year_of_study=current.year_of_study,
        role_id=current.role_id,
        role_name=current.role.name if current.role else None,
        profile_image_url=current.profile_image_url,
    )
