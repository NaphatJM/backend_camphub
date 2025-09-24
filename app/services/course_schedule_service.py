from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import CourseSchedule, User
from app.schemas.course_schedule_schema import (
    CourseScheduleCreate,
    CourseScheduleRead,
    CourseScheduleUpdate,
)


class CourseScheduleService:
    def __init__(self, session: AsyncSession, current_user: Optional[User] = None):
        self.session = session
        self.current_user = current_user

    # --------------------------
    # GET all schedules
    # --------------------------
    async def get_all(self) -> List[CourseScheduleRead]:
        result = await self.session.execute(select(CourseSchedule))
        schedules = result.scalars().all()
        return [CourseScheduleRead.from_orm(s) for s in schedules]

    # --------------------------
    # GET schedule by ID
    # --------------------------
    async def get_by_id(self, schedule_id: int) -> CourseScheduleRead:
        schedule = await self.session.get(CourseSchedule, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return CourseScheduleRead.from_orm(schedule)

    # --------------------------
    # GET schedules by Course ID
    # --------------------------
    async def get_by_course_id(self, course_id: int) -> List[CourseScheduleRead]:
        result = await self.session.execute(
            select(CourseSchedule).where(CourseSchedule.course_id == course_id)
        )
        schedules = result.scalars().all()
        if not schedules:
            raise HTTPException(
                status_code=404, detail="No schedules found for this course"
            )
        return [CourseScheduleRead.from_orm(s) for s in schedules]

    # --------------------------
    # CREATE schedule
    # --------------------------
    async def create(self, data: CourseScheduleCreate) -> CourseScheduleRead:
        self._check_permission()
        new_schedule = CourseSchedule(**data.model_dump())
        self.session.add(new_schedule)
        await self.session.commit()
        await self.session.refresh(new_schedule)
        return CourseScheduleRead.from_orm(new_schedule)

    # --------------------------
    # UPDATE schedule
    # --------------------------
    async def update(
        self, schedule_id: int, data: CourseScheduleUpdate
    ) -> CourseScheduleRead:
        self._check_permission()
        schedule = await self.session.get(CourseSchedule, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)

        self.session.add(schedule)
        await self.session.commit()
        await self.session.refresh(schedule)
        return CourseScheduleRead.from_orm(schedule)

    # --------------------------
    # DELETE schedule
    # --------------------------
    async def delete(self, schedule_id: int) -> dict:
        self._check_permission()
        schedule = await self.session.get(CourseSchedule, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        await self.session.delete(schedule)
        await self.session.commit()
        return {"ok": True}

    # --------------------------
    # PRIVATE: ตรวจสอบสิทธิ์
    # --------------------------
    def _check_permission(self):
        if not self.current_user or self.current_user.role_id not in [1, 3]:
            raise HTTPException(
                status_code=403, detail="You are not allowed to manage schedules"
            )
