from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.db import get_session
from app.models.user_model import User
from app.schemas.event_schema import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
)
from app.core.deps import get_current_user
from app.services.event_service import EventService
from app.utils import make_naive_datetime, validate_datetime_range

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    start_date: datetime = Form(...),
    end_date: datetime = Form(...),
    capacity: Optional[int] = Form(None),
    is_active: bool = Form(True),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new event with optional image upload"""
    event_service = EventService(session)

    # Convert timezone-aware datetime to naive datetime for database
    start_date = make_naive_datetime(start_date)
    end_date = make_naive_datetime(end_date)

    # Validate datetime range
    try:
        validate_datetime_range(start_date, end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create event data
    event_data = EventCreate(
        title=title,
        description=description,
        start_date=start_date,
        end_date=end_date,
        capacity=capacity,
        is_active=is_active,
    )

    return await event_service.create_with_image(event_data, current_user.id, image)


@router.get("/", response_model=List[EventListResponse])
async def get_events(
    q: Optional[str] = Query(None, description="Search in event title"),
    created_by: Optional[int] = Query(None, description="Filter by creator user ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    date_from: Optional[datetime] = Query(
        None, description="Filter events from this date"
    ),
    date_to: Optional[datetime] = Query(None, description="Filter events to this date"),
    limit: int = Query(50, ge=1, le=100, description="Limit number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_session),
):
    """Get events with optional filtering and pagination"""
    event_service = EventService(session)

    filters = {
        "search": q,
        "created_by": created_by,
        "is_active": is_active,
        "date_from": date_from,
        "date_to": date_to,
    }

    return await event_service.get_events_list(
        limit=limit, offset=offset, filters=filters
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event_detail(
    event_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific event by ID with enrollment count"""
    event_service = EventService(session)
    return await event_service.get_by_id_detailed(event_id)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete an event (soft delete by setting is_active=False)"""
    event_service = EventService(session)
    await event_service.delete_with_cleanup(event_id, current_user.id)
    return None


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    capacity: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update an event with optional image replacement"""
    event_service = EventService(session)

    # Prepare update data
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if start_date is not None:
        update_data["start_date"] = make_naive_datetime(start_date)
    if end_date is not None:
        update_data["end_date"] = make_naive_datetime(end_date)
    if capacity is not None:
        update_data["capacity"] = capacity
    if is_active is not None:
        update_data["is_active"] = is_active

    if not update_data and not image:
        raise HTTPException(status_code=400, detail="ไม่ได้ส่งข้อมูลมาเพื่ออัปเดต")

    event_update = EventUpdate(**update_data)
    return await event_service.update_with_image(
        event_id, event_update, current_user.id, image
    )
