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
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import math

from app.models import get_session
from app.models.event_model import Event
from app.models.user_model import User
from app.schemas.event_schema import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    EventListPaginationResponse,
)
from app.core.deps import get_current_user
from app.services import event_image_service
from app.utils import make_naive_datetime, validate_datetime_range

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    start_date: datetime = Form(...),
    end_date: datetime = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new event with optional image upload"""

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
        image_url, _ = await event_image_service.save_image(image, "event")

    # Create event
    event = Event(
        title=title,
        description=description,
        start_date=start_date,
        end_date=end_date,
        image_url=image_url,
        created_by=current_user.id,
        updated_by=current_user.id,
    )

    try:
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event
    except Exception as e:
        await session.rollback()
        # Clean up uploaded file if event creation fails
        if image_url:
            event_image_service.delete_image(image_url)
        raise HTTPException(
            status_code=500, detail=f"เกิดข้อผิดพลาดในการสร้างกิจกรรม: {str(e)}"
        )


@router.post("/{event_id}/upload-image")
async def upload_event_image(
    event_id: int,
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload image for an existing event"""

    # Get event
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบกิจกรรมนี้")

    # Check if user has permission to update this event
    if event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="คุณไม่มีสิทธิ์แก้ไขกิจกรรมนี้"
        )

    try:
        # Replace image using service
        image_url, _ = await event_image_service.replace_image(
            image, event.image_url, "event"
        )

        # Update event image URL
        event.image_url = image_url
        event.updated_by = current_user.id
        event.updated_at = datetime.now()

        session.add(event)
        await session.commit()
        await session.refresh(event)

        return {
            "message": "อัปโหลดรูปภาพกิจกรรมสำเร็จ",
            "image_url": event.image_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"เกิดข้อผิดพลาดในการอัปโหลดไฟล์: {str(e)}"
        )


@router.delete("/{event_id}/image")
async def delete_event_image(
    event_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete image of an existing event"""

    # Get event
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบกิจกรรมนี้")

    # Check if user has permission to update this event
    if event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="คุณไม่มีสิทธิ์แก้ไขกิจกรรมนี้"
        )

    if not event.image_url:
        raise HTTPException(status_code=400, detail="กิจกรรมนี้ไม่มีรูปภาพ")

    try:
        # Delete image using service
        event_image_service.delete_image(event.image_url)

        # Update event
        event.image_url = None
        event.updated_by = current_user.id
        event.updated_at = datetime.now()

        session.add(event)
        await session.commit()

        return {"message": "ลบรูปภาพกิจกรรมสำเร็จ"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"เกิดข้อผิดพลาดในการลบรูปภาพ: {str(e)}"
        )


@router.get("/", response_model=EventListPaginationResponse)
async def get_events(
    page: int = Query(1, ge=1, description="หมายเลขหน้า"),
    per_page: int = Query(10, ge=1, le=100, description="จำนวนรายการต่อหน้า"),
    session: AsyncSession = Depends(get_session),
):
    """Get all events with pagination"""
    # Count total events
    count_statement = select(func.count(Event.id))
    count_result = await session.execute(count_statement)
    total = count_result.scalar_one()

    # Calculate pagination values
    total_pages = math.ceil(total / per_page)
    offset = (page - 1) * per_page

    # Get events for current page
    statement = (
        select(Event).offset(offset).limit(per_page).order_by(Event.created_at.desc())
    )
    result = await session.execute(statement)
    events = result.scalars().all()

    return EventListPaginationResponse(
        items=events,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event_by_id(event_id: int, session: AsyncSession = Depends(get_session)):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบกิจกรรมนี้")
    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบกิจกรรมนี้")

    # Update only provided fields
    update_data = event_data.model_dump(exclude_unset=True)

    # Convert timezone-aware datetime to naive datetime for database
    if "start_date" in update_data:
        update_data["start_date"] = make_naive_datetime(update_data["start_date"])
    if "end_date" in update_data:
        update_data["end_date"] = make_naive_datetime(update_data["end_date"])

    # Validate datetime range if both dates are provided
    if "start_date" in update_data and "end_date" in update_data:
        try:
            validate_datetime_range(update_data["start_date"], update_data["end_date"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif "start_date" in update_data and event.end_date:
        try:
            validate_datetime_range(update_data["start_date"], event.end_date)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif "end_date" in update_data and event.start_date:
        try:
            validate_datetime_range(event.start_date, update_data["end_date"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    for field, value in update_data.items():
        setattr(event, field, value)

    event.updated_by = current_user.id
    event.updated_at = datetime.now()

    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบกิจกรรมนี้")

    await session.delete(event)
    await session.commit()
    return None


@router.get("/user/{user_id}", response_model=EventListPaginationResponse)
async def get_user_events(
    user_id: int,
    page: int = Query(1, ge=1, description="หมายเลขหน้า"),
    per_page: int = Query(10, ge=1, le=100, description="จำนวนรายการต่อหน้า"),
    session: AsyncSession = Depends(get_session),
):
    """Get all events created by a specific user with pagination"""
    # Count total events for the user
    count_statement = select(func.count(Event.id)).where(Event.created_by == user_id)
    count_result = await session.execute(count_statement)
    total = count_result.scalar_one()

    # Calculate pagination values
    total_pages = math.ceil(total / per_page)
    offset = (page - 1) * per_page

    # Get events for current page
    statement = (
        select(Event)
        .where(Event.created_by == user_id)
        .offset(offset)
        .limit(per_page)
        .order_by(Event.created_at.desc())
    )
    result = await session.execute(statement)
    events = result.scalars().all()

    return EventListPaginationResponse(
        items=events,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
