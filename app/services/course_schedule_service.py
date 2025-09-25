from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import CourseSchedule, User, Room
from app.schemas.course_schedule_schema import (
    CourseScheduleCreate,
    CourseScheduleUpdate,
    CourseScheduleReadWithRoom,
)


class CourseScheduleService:
    def __init__(self, session: AsyncSession, current_user: Optional[User] = None):
        self.session = session
        self.current_user = current_user

    # --------------------------
    # GET all schedules (with room + location)
    # --------------------------
    async def get_all(self) -> List[CourseScheduleReadWithRoom]:
        result = await self.session.execute(
            select(CourseSchedule).options(
                selectinload(CourseSchedule.room).selectinload(Room.location)
            )
        )
        schedules = result.scalars().all()
        return [CourseScheduleReadWithRoom.from_orm(s) for s in schedules]

    # --------------------------
    # GET schedule by ID
    # --------------------------
    async def get_by_id(self, schedule_id: int) -> CourseScheduleReadWithRoom:
        schedule = await self.session.get(
            CourseSchedule,
            schedule_id,
            options=selectinload(CourseSchedule.room).selectinload(Room.location),
        )
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return CourseScheduleReadWithRoom.from_orm(schedule)

    # --------------------------
    # GET schedules by Course ID
    # --------------------------
    async def get_by_course_id(
        self, course_id: int
    ) -> List[CourseScheduleReadWithRoom]:
        result = await self.session.execute(
            select(CourseSchedule)
            .where(CourseSchedule.course_id == course_id)
            .options(selectinload(CourseSchedule.room).selectinload(Room.location))
        )
        schedules = result.scalars().all()
        if not schedules:
            raise HTTPException(
                status_code=404, detail="No schedules found for this course"
            )
        return [CourseScheduleReadWithRoom.from_orm(s) for s in schedules]

    # --------------------------
    # CREATE schedule
    # --------------------------
    async def create(self, data: CourseScheduleCreate) -> CourseScheduleReadWithRoom:
        self._check_permission()
        # ตรวจว่า room_id มีจริง
        room = await self.session.get(Room, data.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        new_schedule = CourseSchedule(**data.model_dump())
        self.session.add(new_schedule)
        await self.session.commit()
        await self.session.refresh(new_schedule)
        return CourseScheduleReadWithRoom.from_orm(new_schedule)

    # --------------------------
    # UPDATE schedule
    # --------------------------
    async def update(
        self, schedule_id: int, data: CourseScheduleUpdate
    ) -> CourseScheduleReadWithRoom:
        self._check_permission()
        schedule = await self.session.get(CourseSchedule, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        update_data = data.model_dump(exclude_unset=True)

        # ถ้ามี room_id ใหม่ ตรวจสอบก่อน
        if "room_id" in update_data:
            room = await self.session.get(Room, update_data["room_id"])
            if not room:
                raise HTTPException(status_code=404, detail="Room not found")

        for field, value in update_data.items():
            setattr(schedule, field, value)

        self.session.add(schedule)
        await self.session.commit()
        await self.session.refresh(schedule)
        return CourseScheduleReadWithRoom.from_orm(schedule)

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
