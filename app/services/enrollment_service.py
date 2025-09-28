from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models import Enrollment, Course, User, CourseSchedule, Room, Location
from app.schemas.enrollment_schema import (
    EnrollmentCreate,
    EnrollmentRead,
    EnrollmentUpdate,
    EnrollmentSummary,
    EnrollmentReadWithSchedule,
)
from app.schemas.course_schedule_schema import CourseScheduleReadWithRoom


class EnrollmentService:
    def __init__(self, session: AsyncSession, current_user: User):
        self.session = session
        self.current_user = current_user

    # 1. ดูผู้เรียนของ course
    async def get_course_enrollments(self, course_id: int) -> EnrollmentSummary:
        result = await self.session.execute(
            select(Enrollment)
            .options(selectinload(Enrollment.user))
            .where(Enrollment.course_id == course_id)
        )
        enrollments = result.scalars().all()

        if not enrollments:
            return EnrollmentSummary(
                course_id=course_id,
                course_code="",
                course_name="",
                total_enrolled=0,
                enrolled_users=[],
            )

        # โหลด course
        course = await self.session.get(Course, course_id)

        return EnrollmentSummary(
            course_id=course_id,
            course_code=course.course_code,
            course_name=course.course_name,
            total_enrolled=len(enrollments),
            enrolled_users=[e.user.fullname for e in enrollments],
        )

    # 2. Enroll current user
    async def enroll(self, data: EnrollmentCreate) -> EnrollmentRead:
        # ตรวจสอบว่า course มีอยู่จริงหรือไม่
        course = await self.session.get(Course, data.course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # ตรวจสอบว่าผู้ใช้ enroll แล้วหรือยัง
        result = await self.session.execute(
            select(Enrollment).where(
                Enrollment.course_id == data.course_id,
                Enrollment.user_id == self.current_user.id,
            )
        )
        existing = result.scalars().first()
        if existing:
            existing.status = "enrolled"
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return EnrollmentRead(
                id=existing.id,
                course_id=existing.course_id,
                user_id=existing.user_id,
                status=existing.status,
                enrollment_at=existing.enrollment_at,
            )

        # สร้าง enrollment ใหม่
        new_enrollment = Enrollment(
            course_id=data.course_id, user_id=self.current_user.id, status="enrolled"
        )
        self.session.add(new_enrollment)
        await self.session.commit()
        await self.session.refresh(new_enrollment)
        return EnrollmentRead(
            id=new_enrollment.id,
            course_id=new_enrollment.course_id,
            user_id=new_enrollment.user_id,
            status=new_enrollment.status,
            enrollment_at=new_enrollment.enrollment_at,
        )

    # 3. ยกเลิก enrollment
    async def cancel(self, course_id: int) -> dict:
        result = await self.session.execute(
            select(Enrollment).where(
                Enrollment.course_id == course_id,
                Enrollment.user_id == self.current_user.id,
            )
        )
        enrollment = result.scalars().first()
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        await self.session.delete(enrollment)
        await self.session.commit()
        return {"ok": True}

    # 4. ดูข้อมูล enrollment ของ user ปัจจุบัน
    async def get_user_enrollments(self) -> list[EnrollmentReadWithSchedule]:
        # Load enrollment + course + schedule + room + location
        result = await self.session.execute(
            select(Enrollment)
            .options(
                selectinload(Enrollment.course)
                .selectinload(Course.schedules)
                .selectinload(CourseSchedule.room)
                .selectinload(Room.location),
                selectinload(Enrollment.user),
            )
            .where(Enrollment.user_id == self.current_user.id)
        )
        enrollments = result.scalars().all()

        return [
            EnrollmentReadWithSchedule(
                id=e.id,
                course_id=e.course_id,
                user_id=e.user_id,
                status=e.status,
                enrollment_at=e.enrollment_at,
                fullname=e.user.fullname,
                course_code=e.course.course_code,
                course_name=e.course.course_name,
                schedules=[
                    CourseScheduleReadWithRoom.model_validate(s)
                    for s in e.course.schedules
                ],
            )
            for e in enrollments
        ]
