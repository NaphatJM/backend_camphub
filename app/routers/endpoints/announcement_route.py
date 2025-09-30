from typing import Optional, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import math

from app.core.db import get_session
from app.models import Announcement, User
from app.core.deps import get_current_user
from app.schemas.announcement_schema import (
    AnnouncementRead,
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementListResponse,
)
from app.services import announcement_image_service
from app.utils import make_naive_datetime, validate_datetime_range
from app.models.announcement_model import AnnouncementCategory

router = APIRouter(prefix="/annc", tags=["announcements"])

# Define constant for repeated message
NOT_FOUND_ANNOUNCEMENT_MSG = "ไม่พบข่าวประกาศ"


@router.get("/", response_model=AnnouncementListResponse)
async def get_announcements(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    category: Optional[AnnouncementCategory] = Query(
        None, description="Filter by category"
    ),
    session: AsyncSession = Depends(get_session),
):
    """Get announcements with optional category filter and pagination"""

    stmt = select(Announcement).where(
        Announcement.start_date <= datetime.now(),
        Announcement.end_date >= datetime.now(),
    )

    if category:
        stmt = stmt.where(Announcement.category == category)

    count_stmt = select(Announcement).where(
        Announcement.start_date <= datetime.now(),
        Announcement.end_date >= datetime.now(),
    )
    if category:
        count_stmt = count_stmt.where(Announcement.category == category)

    count_result = await session.exec(count_stmt)
    total = len(count_result.scalars().all())

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page).order_by(Announcement.created_at.desc())

    result = await session.exec(stmt)
    announcements = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return AnnouncementListResponse(
        announcements=announcements,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/categories")
async def get_announcement_categories():
    """Get all available announcement categories"""
    return {
        "categories": [
            {"value": AnnouncementCategory.ACADEMIC, "label": "วิชาการ"},
            {"value": AnnouncementCategory.ACTIVITY, "label": "กิจกรรม"},
            {"value": AnnouncementCategory.GENERAL, "label": "ทั่วไป"},
        ]
    }


@router.get("/by-category/{category}", response_model=AnnouncementListResponse)
async def get_announcements_by_category(
    category: AnnouncementCategory,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """Get announcements by specific category"""

    # Query announcements by category
    stmt = select(Announcement).where(
        Announcement.category == category,
        Announcement.start_date <= datetime.now(),
        Announcement.end_date >= datetime.now(),
    )

    # Count total
    count_result = await session.exec(stmt)
    total = len(count_result.scalars().all())

    # Apply pagination
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page).order_by(Announcement.created_at.desc())

    result = await session.exec(stmt)
    announcements = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return AnnouncementListResponse(
        announcements=announcements,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{announcement_id}", response_model=AnnouncementRead)
async def get_announcement_by_id(
    announcement_id: int, session: AsyncSession = Depends(get_session)
):
    announcement = await session.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail=NOT_FOUND_ANNOUNCEMENT_MSG)
    return announcement


@router.post("/", response_model=AnnouncementRead, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    title: str = Form(...),
    description: str = Form(...),
    category: AnnouncementCategory = Form(AnnouncementCategory.GENERAL),
    start_date: datetime = Form(...),
    end_date: datetime = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # เช็ค role: เฉพาะ Teacher/Admin เท่านั้น
    if getattr(current_user, "role_id", None) == 2:
        raise HTTPException(status_code=403, detail="นักศึกษาไม่มีสิทธิ์สร้างข่าวประกาศ")

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
        # ===== ตรวจสอบขนาดไฟล์ (สูงสุด 10MB) =====
        MAX_SIZE = 10 * 1024 * 1024  # 10MB
        contents = await image.read()
        if len(contents) > MAX_SIZE:
            raise HTTPException(status_code=413, detail="ไฟล์รูปภาพใหญ่เกิน 10MB")
        # reset file pointer for downstream
        image.file.seek(0)
        image_url, _ = await announcement_image_service.save_image(
            image, "announcement"
        )

    new_announcement = Announcement(
        title=title,
        description=description,
        category=category,
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
        raise HTTPException(status_code=404, detail=NOT_FOUND_ANNOUNCEMENT_MSG)

    # ตรวจสอบ ownership
    if announcement.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="คุณไม่มีสิทธิ์แก้ไขข่าวประกาศนี้")

    update_data = announcement_update.model_dump(exclude_unset=True)

    # Convert timezone-aware datetime to naive datetime for database
    if "start_date" in update_data:
        update_data["start_date"] = make_naive_datetime(update_data["start_date"])
    if "end_date" in update_data:
        update_data["end_date"] = make_naive_datetime(update_data["end_date"])

    # Validate datetime range if dates are being updated
    if "start_date" in update_data or "end_date" in update_data:
        try:
            validate_datetime_range(
                update_data.get("start_date", announcement.start_date),
                update_data.get("end_date", announcement.end_date),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if update_data:
        for field, value in update_data.items():
            setattr(announcement, field, value)
        announcement.updated_at = datetime.now()

        try:
            await session.commit()
            await session.refresh(announcement)
        except IntegrityError as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการอัปเดตข้อมูล")
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=500, detail=f"เกิดข้อผิดพลาดในการอัปเดตข่าวประกาศ: {str(e)}"
            )

    return announcement


@router.patch("/{announcement_id}", response_model=AnnouncementRead)
async def patch_announcement(
    announcement_id: int,
    announcement_update: AnnouncementUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    announcement = await session.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail=NOT_FOUND_ANNOUNCEMENT_MSG)
    if announcement.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="คุณไม่มีสิทธิ์แก้ไขข่าวประกาศนี้")
    update_data = announcement_update.model_dump(exclude_unset=True)
    if "start_date" in update_data:
        update_data["start_date"] = make_naive_datetime(update_data["start_date"])
    if "end_date" in update_data:
        update_data["end_date"] = make_naive_datetime(update_data["end_date"])
    if "start_date" in update_data or "end_date" in update_data:
        try:
            validate_datetime_range(
                update_data.get("start_date", announcement.start_date),
                update_data.get("end_date", announcement.end_date),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    if update_data:
        for field, value in update_data.items():
            setattr(announcement, field, value)
        announcement.updated_at = datetime.now()
        try:
            await session.commit()
            await session.refresh(announcement)
        except IntegrityError as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการอัปเดตข้อมูล")
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=500, detail=f"เกิดข้อผิดพลาดในการอัปเดตข่าวประกาศ: {str(e)}"
            )
    return announcement


@router.delete("/{announcement_id}", status_code=204, response_model=None)
async def delete_announcement(
    announcement_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    announcement = await session.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail=NOT_FOUND_ANNOUNCEMENT_MSG)
    if announcement.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="คุณไม่มีสิทธิ์ลบข่าวประกาศนี้")
    if announcement.image_url:
        announcement_image_service.delete_image(announcement.image_url)
    try:
        await session.delete(announcement)
        await session.commit()
        return  # 204 No Content
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=400, detail="ไม่สามารถลบข่าวประกาศได้ เนื่องจากมีข้อมูลที่เกี่ยวข้อง"
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"เกิดข้อผิดพลาดในการลบข่าวประกาศ: {str(e)}"
        )
