from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from datetime import datetime

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

    async def _get_enrollment_count(self, event_id: int) -> int:
        """ฟังก์ชันกลางสำหรับนับจำนวนคนที่สมัครในกิจกรรม"""
        result = await self.session.execute(
            select(func.count(EventEnrollment.id)).where(
                EventEnrollment.event_id == event_id
            )
        )
        return result.scalar_one()

    async def _get_enrollment_counts_batch(
        self, event_ids: list[int]
    ) -> dict[int, int]:
        """ฟังก์ชันนับจำนวนคนสำหรับหลาย events พร้อมกัน (เพื่อประสิทธิภาพ)"""
        if not event_ids:
            return {}

        result = await self.session.execute(
            select(
                EventEnrollment.event_id, func.count(EventEnrollment.id).label("count")
            )
            .where(EventEnrollment.event_id.in_(event_ids))
            .group_by(EventEnrollment.event_id)
        )

        return {row.event_id: row.count for row in result}

    async def get_event_enrollments(self, event_id: int) -> EventEnrollmentSummary:
        # ดึงรายชื่อคนที่สมัคร
        result = await self.session.execute(
            select(EventEnrollment)
            .options(selectinload(EventEnrollment.user))
            .where(EventEnrollment.event_id == event_id)
        )
        enrollments = result.scalars().all()
        fullname = [e.user.fullname for e in enrollments]

        # ใช้ฟังก์ชันกลางในการนับ (แม้ว่าจะได้ผลเหมือนกัน แต่เพื่อความสอดคล้อง)
        total_enrolled = await self._get_enrollment_count(event_id)

        return EventEnrollmentSummary(
            event_id=event_id,
            total_enrolled=total_enrolled,
            enrolled_users=fullname,
        )

    async def enroll(self, data: EventEnrollmentCreate) -> EventEnrollmentRead:
        # ตรวจสอบ event
        event = await self.session.get(Event, data.event_id)
        if not event:
            raise HTTPException(status_code=404, detail="ไม่พบกิจกรรมนี้")
        if not event.is_active:
            raise HTTPException(status_code=400, detail="กิจกรรมนี้ปิดรับสมัครแล้ว")

        # ตรวจสอบว่าเคยสมัครแล้วหรือยัง
        existing_enrollment = await self.session.execute(
            select(EventEnrollment).where(
                EventEnrollment.event_id == data.event_id,
                EventEnrollment.user_id == self.current_user.id,
            )
        )
        if existing_enrollment.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="คุณได้สมัครกิจกรรมนี้แล้ว")

        # 🆕 ตรวจสอบ capacity - จำกัดจำนวนคน
        if event.capacity is not None:  # มี capacity จำกัด
            # ใช้ฟังก์ชันกลางในการนับ
            current_enrolled = await self._get_enrollment_count(data.event_id)

            if current_enrolled >= event.capacity:
                raise HTTPException(
                    status_code=400,
                    detail=f"กิจกรรมนี้เต็มแล้ว (รับได้สูงสุด {event.capacity} คน, สมัครแล้ว {current_enrolled} คน)",
                )

        # สร้าง enrollment ใหม่
        new_enrollment = EventEnrollment(
            event_id=data.event_id,
            user_id=self.current_user.id,
            status="enrolled",
            enrollment_at=datetime.now(),
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
            raise HTTPException(status_code=404, detail="ไม่พบการลงทะเบียนกิจกรรมนี้")
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

    async def check_event_capacity(self, event_id: int) -> dict:
        """ตรวจสอบ capacity และสถานะของ event"""
        # ดึงข้อมูล event
        event = await self.session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="ไม่พบกิจกรรมนี้")

        # ใช้ฟังก์ชันกลางในการนับ
        current_enrolled = await self._get_enrollment_count(event_id)

        # คำนวณข้อมูล capacity
        capacity_info = {
            "event_id": event_id,
            "event_title": event.title,
            "current_enrolled": current_enrolled,
            "capacity": event.capacity,  # None = unlimited
            "is_full": False,
            "available_seats": None,
            "is_active": event.is_active,
            "can_enroll": event.is_active,
        }

        if event.capacity is not None:
            capacity_info["available_seats"] = max(0, event.capacity - current_enrolled)
            capacity_info["is_full"] = current_enrolled >= event.capacity
            capacity_info["can_enroll"] = (
                event.is_active and not capacity_info["is_full"]
            )

        return capacity_info

    async def get_events_with_capacity_status(self) -> list[dict]:
        """ดึงรายการ events พร้อมข้อมูล capacity"""
        # ดึงทุก events ที่เปิดใช้งาน
        events_result = await self.session.execute(
            select(Event).where(Event.is_active == True)
        )
        events = events_result.scalars().all()

        result = []
        for event in events:
            capacity_info = await self.check_event_capacity(event.id)
            result.append(capacity_info)

        return result

    @classmethod
    async def get_enrollment_count_for_event(
        cls, session: AsyncSession, event_id: int
    ) -> int:
        """Static method สำหรับใช้ใน routes โดยไม่ต้องสร้าง service instance"""
        result = await session.execute(
            select(func.count(EventEnrollment.id)).where(
                EventEnrollment.event_id == event_id
            )
        )
        return result.scalar_one()

    @classmethod
    async def get_enrollment_counts_for_events(
        cls, session: AsyncSession, event_ids: list[int]
    ) -> dict[int, int]:
        """Static method สำหรับนับหลาย events พร้อมกัน ใช้ใน routes"""
        if not event_ids:
            return {}

        result = await session.execute(
            select(
                EventEnrollment.event_id, func.count(EventEnrollment.id).label("count")
            )
            .where(EventEnrollment.event_id.in_(event_ids))
            .group_by(EventEnrollment.event_id)
        )

        return {row.event_id: row.count for row in result}
