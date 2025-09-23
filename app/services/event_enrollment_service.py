from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models import EventEnrollment, Event, User
from app.schemas.event_enrollment_schema import (
    EventEnrollmentCreate,
    EventEnrollmentRead,
    EventEnrollmentUpdate,
    EventEnrollmentSummary,
)


class EventEnrollmentService:
    def __init__(self, session: AsyncSession, current_user: User):
        self.session = session
        self.current_user = current_user

    async def get_event_enrollments(self, event_id: int) -> EventEnrollmentSummary:
        result = await self.session.execute(
            select(EventEnrollment)
            .options(selectinload(EventEnrollment.user))
            .where(EventEnrollment.event_id == event_id)
        )
        enrollments = result.scalars().all()
        fullname = [e.user.fullname for e in enrollments]
        return EventEnrollmentSummary(
            event_id=event_id,
            total_enrolled=len(enrollments),
            enrolled_users=fullname,
        )

    async def enroll(self, data: EventEnrollmentCreate) -> EventEnrollmentRead:
        # ตรวจสอบ event
        event = await self.session.get(Event, data.event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        if not event.is_active:
            raise HTTPException(status_code=400, detail="Event is not active")

        # ตรวจ capacity
        if event.capacity is not None:
            result_count = await self.session.execute(
                select(EventEnrollment).where(EventEnrollment.event_id == data.event_id)
            )
            total = len(result_count.scalars().all())
            if total >= event.capacity:
                raise HTTPException(status_code=400, detail="Event is full")

        # ตรวจสอบว่าลงแล้วหรือยัง
        result = await self.session.execute(
            select(EventEnrollment).where(
                EventEnrollment.event_id == data.event_id,
                EventEnrollment.user_id == self.current_user.id,
            )
        )
        existing = result.scalars().first()
        if existing:
            existing.status = "enrolled"
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return EventEnrollmentRead(
                id=existing.id,
                event_id=existing.event_id,
                user_id=existing.user_id,
                status=existing.status,
                enrollment_at=existing.enrollment_at,
                fullname=self.current_user.fullname,
                title=event.title,
            )

        new_enrollment = EventEnrollment(
            event_id=data.event_id, user_id=self.current_user.id, status="enrolled"
        )
        self.session.add(new_enrollment)
        await self.session.commit()
        await self.session.refresh(new_enrollment)
        return EventEnrollmentRead(
            id=new_enrollment.id,
            event_id=new_enrollment.event_id,
            user_id=new_enrollment.user_id,
            status=new_enrollment.status,
            enrollment_at=new_enrollment.enrollment_at,
            fullname=self.current_user.fullname,
            title=event.title,
        )

    async def cancel(self, event_id: int) -> dict:
        result = await self.session.execute(
            select(EventEnrollment).where(
                EventEnrollment.event_id == event_id,
                EventEnrollment.user_id == self.current_user.id,
            )
        )
        enrollment = result.scalars().first()
        if not enrollment:
            raise HTTPException(status_code=404, detail="Event enrollment not found")
        await self.session.delete(enrollment)
        await self.session.commit()
        return {"ok": True}

    async def get_user_event_enrollments(self) -> list[EventEnrollmentRead]:
        result = await self.session.execute(
            select(EventEnrollment)
            .options(selectinload(EventEnrollment.event))
            .where(EventEnrollment.user_id == self.current_user.id)
        )
        enrollments = result.scalars().all()
        return [
            EventEnrollmentRead(
                id=e.id,
                event_id=e.event_id,
                user_id=e.user_id,
                status=e.status,
                enrollment_at=e.enrollment_at,
                fullname=e.user.fullname,
                title=e.event.title,
            )
            for e in enrollments
        ]
