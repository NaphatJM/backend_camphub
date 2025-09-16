from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models import get_session, Announcement
from app.core.deps import get_current_user
from app.schemas.announcement_schema import (
    AnnouncementRead,
    AnnouncementCreate,
    AnnouncementUpdate,
)

router = APIRouter(
    prefix="/annc", tags=["announcements"], dependencies=[Depends(get_current_user)]
)


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
        raise HTTPException(status_code=404, detail="Announcement not found")
    return announcement


@router.post("/", response_model=AnnouncementRead)
async def create_announcement(
    announcement: AnnouncementCreate, session: AsyncSession = Depends(get_session)
):
    new_announcement = Announcement(**announcement.model_dump())
    session.add(new_announcement)
    await session.commit()
    await session.refresh(new_announcement)
    return new_announcement


@router.put("/{announcement_id}", response_model=AnnouncementRead)
async def update_announcement(
    announcement_id: int,
    announcement_update: AnnouncementUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update an existing announcement.
    """
    # Get the existing announcement
    announcement = await session.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Update only the fields that were provided
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
    announcement_id: int, session: AsyncSession = Depends(get_session)
):
    announcement = await session.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    await session.delete(announcement)
    await session.commit()

    return {"message": "Announcement deleted successfully"}
