from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.models import User
from app.core.deps import get_current_user
from app.schemas.event_enrollment_schema import EventEnrollmentCreate
from app.services.event_enrollment_service import EventEnrollmentService

router = APIRouter(prefix="/event-enrollments", tags=["event-enrollments"])


@router.get("/event/{event_id}")
async def get_event_enrollments(
    event_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = EventEnrollmentService(session=session, current_user=current_user)
    return await service.get_event_enrollments(event_id)


@router.post("/enroll")
async def enroll_event(
    data: EventEnrollmentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = EventEnrollmentService(session=session, current_user=current_user)
    return await service.enroll(data)


@router.delete("/cancel/{event_id}")
async def cancel_event_enroll(
    event_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = EventEnrollmentService(session=session, current_user=current_user)
    return await service.cancel(event_id)


@router.get("/user")
async def get_user_event_enrollments(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = EventEnrollmentService(session=session, current_user=current_user)
    return await service.get_user_event_enrollments()


@router.get("/capacity/{event_id}")
async def check_event_capacity(
    event_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """ตรวจสอบ capacity และสถานะของ event"""
    service = EventEnrollmentService(session=session, current_user=current_user)
    return await service.check_event_capacity(event_id)


@router.get("/capacity-status")
async def get_events_capacity_status(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """ดูสถานะ capacity ของ events ทั้งหมด"""
    service = EventEnrollmentService(session=session, current_user=current_user)
    return await service.get_events_with_capacity_status()
