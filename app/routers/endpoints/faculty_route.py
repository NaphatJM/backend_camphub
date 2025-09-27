from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.models.user_model import User
from app.schemas.faculty_schema import FacultyRead, FacultyCreate, FacultyUpdate
from app.core.deps import get_current_user
from app.services.faculty_service import FacultyService

router = APIRouter(prefix="/faculty", tags=["faculty"])


@router.get("", response_model=list[FacultyRead])
async def get_all_faculties(session: AsyncSession = Depends(get_session)):
    """ดึงข้อมูลคณะทั้งหมด (มี cache เพื่อประสิทธิภาพ)"""
    faculty_service = FacultyService(session)
    return await faculty_service.get_all_faculties()


@router.get("/{faculty_id}", response_model=FacultyRead)
async def get_faculty_by_id(
    faculty_id: int,
    session: AsyncSession = Depends(get_session),
):
    """ดึงข้อมูลคณะตาม ID"""
    faculty_service = FacultyService(session)
    return await faculty_service.get_by_id(faculty_id)


@router.post("", response_model=FacultyRead, status_code=status.HTTP_201_CREATED)
async def create_faculty(
    faculty_data: FacultyCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """สร้างคณะใหม่ (เฉพาะ Admin)"""
    faculty_service = FacultyService(session)
    return await faculty_service.create_faculty(faculty_data, current_user.id)


@router.put("/{faculty_id}", response_model=FacultyRead)
async def update_faculty(
    faculty_id: int,
    faculty_data: FacultyUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update faculty (Admin only)"""
    faculty_service = FacultyService(session)
    return await faculty_service.update_faculty(
        faculty_id, faculty_data, current_user.id
    )


@router.delete("/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faculty(
    faculty_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete faculty (Admin only, checks for user relationships)"""
    faculty_service = FacultyService(session)
    await faculty_service.delete_faculty(faculty_id, current_user.id)
    return None


@router.get("/{faculty_id}/statistics")
async def get_faculty_statistics(
    faculty_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get faculty statistics (Admin only)"""
    faculty_service = FacultyService(session)
    return await faculty_service.get_faculty_statistics(faculty_id, current_user.id)
