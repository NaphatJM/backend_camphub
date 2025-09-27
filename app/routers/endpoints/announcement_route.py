from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    status,
    UploadFile,
    File,
    Form,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.db import get_session
from app.models import User
from app.core.deps import get_current_user
from app.schemas.announcement_schema import (
    AnnouncementRead,
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementListResponse,
)
from app.services.announcement_service import AnnouncementService
from app.utils import make_naive_datetime, validate_datetime_range
from app.models.announcement_model import AnnouncementCategory

router = APIRouter(prefix="/annc", tags=["announcements"])


@router.get("/", response_model=AnnouncementListResponse)
async def get_announcements(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    category: Optional[AnnouncementCategory] = Query(
        None, description="Filter by category"
    ),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get active announcements with optional category filter and pagination"""
    service = AnnouncementService(session, current_user)
    return await service.get_active_announcements(
        page=page, per_page=per_page, category=category.value if category else None
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
    current_user: User = Depends(get_current_user),
):
    """Get announcements by specific category"""
    service = AnnouncementService(session, current_user)
    return await service.get_active_announcements(
        page=page, per_page=per_page, category=category.value
    )


@router.get("/{announcement_id}", response_model=AnnouncementRead)
async def get_announcement_by_id(
    announcement_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get announcement by ID"""
    service = AnnouncementService(session, current_user)
    return await service.get_by_id(announcement_id)


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
    """Create a new announcement with optional image upload"""

    # Convert timezone-aware datetime to naive datetime for database
    start_date = make_naive_datetime(start_date)
    end_date = make_naive_datetime(end_date)

    # Validate datetime range
    validate_datetime_range(start_date, end_date)

    # Create announcement using service
    service = AnnouncementService(session, current_user)
    create_data = AnnouncementCreate(
        title=title,
        description=description,
        category=category,
        start_date=start_date,
        end_date=end_date,
    )

    return await service.create_with_image(create_data, image)


@router.put("/{announcement_id}", response_model=AnnouncementRead)
async def update_announcement(
    announcement_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[AnnouncementCategory] = Form(None),
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    image: Optional[UploadFile] = File(None),
    remove_image: bool = Form(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update announcement with optional image management"""

    # Prepare update data
    update_data = AnnouncementUpdate()
    if title is not None:
        update_data.title = title
    if description is not None:
        update_data.description = description
    if category is not None:
        update_data.category = category
    if start_date is not None:
        update_data.start_date = make_naive_datetime(start_date)
    if end_date is not None:
        update_data.end_date = make_naive_datetime(end_date)

    # Validate datetime range if both dates are provided
    if update_data.start_date and update_data.end_date:
        validate_datetime_range(update_data.start_date, update_data.end_date)

    service = AnnouncementService(session, current_user)
    return await service.update_with_image(
        announcement_id, update_data, image, remove_image
    )


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete announcement with proper cleanup"""
    service = AnnouncementService(session, current_user)
    return await service.delete_with_cleanup(announcement_id)
