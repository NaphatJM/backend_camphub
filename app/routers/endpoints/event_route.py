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
from sqlalchemy import and_
from datetime import datetime

from app.models import get_session
from app.models.event_model import Event
from app.models.event_enrollment_model import EventEnrollment
from app.models.user_model import User
from app.schemas.event_schema import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
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
    capacity: Optional[int] = Form(None),
    is_active: bool = Form(True),
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
        capacity=capacity,
        is_active=is_active,
        image_url=image_url,
        created_by=current_user.id,
        updated_by=current_user.id,
    )

    try:
        session.add(event)
        await session.commit()
        await session.refresh(event)

        # Create response from event object
        return EventResponse.model_validate(event.__dict__ | {"enrolled_count": 0})
    except Exception as e:
        await session.rollback()
        # Clean up uploaded file if event creation fails
        if image_url:
            event_image_service.delete_image(image_url)
        raise HTTPException(
            status_code=500, detail=f"เกิดข้อผิดพลาดในการสร้างกิจกรรม: {str(e)}"
        )


@router.get("/", response_model=List[EventListResponse])
async def get_events(
    created_by: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    q: Optional[str] = Query(None, description="ค้นหาชื่อกิจกรรม"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    include_enrolled_count: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    """Get all events"""
    filters = []
    if created_by is not None:
        filters.append(Event.created_by == created_by)
    if is_active is not None:
        filters.append(Event.is_active == is_active)
    if q:
        filters.append(func.lower(Event.title).like(f"%{q.lower()}%"))
    if date_from:
        filters.append(Event.start_date >= date_from)
    if date_to:
        filters.append(Event.end_date <= date_to)

    stmt = select(Event)
    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.order_by(Event.created_at.desc())
    events = (await session.execute(stmt)).scalars().all()

    # Convert to response format with enrolled_count
    response_items = []
    if include_enrolled_count and events:
        event_ids = [e.id for e in events]
        counts_stmt = (
            select(EventEnrollment.event_id, func.count(EventEnrollment.id).label("c"))
            .where(EventEnrollment.event_id.in_(event_ids))
            .group_by(EventEnrollment.event_id)
        )
        rows = await session.execute(counts_stmt)
        counts_map = {r.event_id: r.c for r in rows}

        for e in events:
            response_items.append(
                EventListResponse.model_validate(
                    e.__dict__ | {"enrolled_count": counts_map.get(e.id, 0)}
                )
            )
    else:
        for e in events:
            response_items.append(
                EventListResponse.model_validate(e.__dict__ | {"enrolled_count": 0})
            )

    return response_items


@router.get("/{event_id}", response_model=EventResponse)
async def get_event_by_id(event_id: int, session: AsyncSession = Depends(get_session)):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบกิจกรรมนี้")

    # Get enrolled_count
    result = await session.execute(
        select(func.count(EventEnrollment.id)).where(
            EventEnrollment.event_id == event_id
        )
    )
    enrolled_count = result.scalar_one()

    return EventResponse.model_validate(
        event.__dict__ | {"enrolled_count": enrolled_count}
    )


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate = Depends(),
    image: Optional[UploadFile] = File(None),
    remove_image: bool = Form(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบกิจกรรมนี้")

    if event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="คุณไม่มีสิทธิ์แก้ไขกิจกรรมนี้"
        )

    update_data = event_data.model_dump(exclude_unset=True)

    if "start_date" in update_data:
        update_data["start_date"] = make_naive_datetime(update_data["start_date"])
    if "end_date" in update_data:
        update_data["end_date"] = make_naive_datetime(update_data["end_date"])

    if ("start_date" in update_data) or ("end_date" in update_data):
        try:
            validate_datetime_range(
                update_data.get("start_date", event.start_date),
                update_data.get("end_date", event.end_date),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    for field, value in update_data.items():
        setattr(event, field, value)

    if image:
        new_url, _ = await event_image_service.replace_image(
            image, event.image_url, "event"
        )
        event.image_url = new_url
    elif remove_image and event.image_url:
        event_image_service.delete_image(event.image_url)
        event.image_url = None

    event.updated_by = current_user.id
    event.updated_at = datetime.now()

    session.add(event)
    await session.commit()
    await session.refresh(event)

    result = await session.execute(
        select(func.count(EventEnrollment.id)).where(
            EventEnrollment.event_id == event_id
        )
    )
    enrolled_count = result.scalar_one()

    return EventResponse.model_validate(
        event.__dict__ | {"enrolled_count": enrolled_count}
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบกิจกรรมนี้")

    if event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="คุณไม่มีสิทธิ์ลบกิจกรรมนี้"
        )

    await session.delete(event)
    await session.commit()
    return {"message": "ลบข่าวประกาศเรียบร้อยแล้ว"}
