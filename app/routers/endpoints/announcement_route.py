from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models import get_session, Announcement, User
from app.core.deps import get_current_user
from app.schemas.announcement_schema import (
    AnnouncementRead,
    AnnouncementCreate,
    AnnouncementUpdate,
)
from app.services import announcement_image_service
from app.utils import make_naive_datetime, validate_datetime_range

router = APIRouter(prefix="/annc", tags=["announcements"])


@router.get("/", response_model=list[AnnouncementRead])
async def get_all_announcements(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Announcement))
    announcements = result.scalars().all()
    return announcements


@router.get("/{announcement_id}", response_model=AnnouncementRead)
async def get_announcement_by_id(
    announcement_id: int, session: AsyncSession = Depends(get_session)
):
    announcement = await session.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="ไม่พบข่าวประกาศ")
    return announcement


@router.post("/", response_model=AnnouncementRead, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    title: str = Form(...),
    description: str = Form(...),
    start_date: datetime = Form(...),
    end_date: datetime = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):

    # Convert timezone-aware datetime to naive datetime for database
    start_date = make_naive_datetime(start_date)
    end_date = make_naive_datetime(end_date)

    # Validate datetime range
    try:
        validate_datetime_range(start_date, end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle image upload if provided
    image_url = None
    if image:
        image_url, _ = await announcement_image_service.save_image(
            image, "announcement"
        )

    new_announcement = Announcement(
        title=title,
        description=description,
        start_date=start_date,
        end_date=end_date,
        image_url=image_url,
        created_by=current_user.id,
    )

    try:
        session.add(new_announcement)
        await session.commit()
        await session.refresh(new_announcement)
        return new_announcement

    except Exception as e:
        await session.rollback()
        if image_url:
            announcement_image_service.delete_image(image_url)
        raise HTTPException(
            status_code=500, detail=f"เกิดข้อผิดพลาดในการสร้างข่าวประกาศ: {str(e)}"
        )


@router.put("/{announcement_id}", response_model=AnnouncementRead)
async def update_announcement(
    announcement_id: int,
    announcement_update: AnnouncementUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):

    announcement = await session.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="ไม่พบข่าวประกาศ")

    update_data = announcement_update.model_dump(exclude_unset=True)
    if update_data:
        for field, value in update_data.items():
            setattr(announcement, field, value)
        announcement.updated_at = datetime.now()

        await session.commit()
        await session.refresh(announcement)

    return announcement


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    announcement = await session.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="ไม่พบข่าวประกาศ")

    # Delete associated image if exists
    if announcement.image_url:
        announcement_image_service.delete_image(announcement.image_url)

    await session.delete(announcement)
    await session.commit()

    return {"message": "ลบข่าวประกาศเรียบร้อยแล้ว"}
