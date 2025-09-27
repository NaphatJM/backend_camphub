from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.models import User
from app.schemas.user_schema import MeRead, MeUpdate
from app.core.deps import get_current_user
from app.services.user_service import UserService

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/upload-profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload/update user profile image"""
    user_service = UserService(session)
    return await user_service.update_profile_image(current_user.id, file)


@router.get("/me", response_model=MeRead)
async def get_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get current user profile with relations"""
    user_service = UserService(session)
    return await user_service.get_by_id_with_relations(current_user.id)


@router.put("/me", response_model=MeRead)
async def update_me(
    user_update: MeUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update current user profile"""
    user_service = UserService(session)
    return await user_service.update_profile(current_user.id, user_update)


@router.put("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Change user password with current password verification"""
    user_service = UserService(session)
    await user_service.change_password(current_user.id, current_password, new_password)
    return {"message": "รหัสผ่านถูกเปลี่ยนแปลงเรียบร้อยแล้ว"}
