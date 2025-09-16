from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.models import get_session, Course
from app.schemas.course_schedule_schema import (
    CourseReadWithSchedule,
    CourseScheduleRead,
)

router = APIRouter(prefix="/courses", tags=["courses"])


# ✅ ดึง course ตาม id
@router.get("/{course_id}", response_model=CourseReadWithSchedule)
async def get_course_by_id(
    course_id: int, session: AsyncSession = Depends(get_session)
):
    course = await session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    schedules = [
        CourseScheduleRead(
            id=s.id,
            course_id=s.course_id,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            room=s.room,
        )
        for s in course.schedules
    ]

    return CourseReadWithSchedule(
        id=course.id,
        course_code=course.course_code,
        course_name=course.course_name,
        credits=course.credits,
        available_seats=course.available_seats,
        description=course.description,
        schedules=schedules,
    )


@router.get("/code/{course_code}", response_model=CourseReadWithSchedule)
async def get_course_by_code(
    course_code: str, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Course)
        .options(selectinload(Course.schedules))
        .where(Course.course_code == course_code)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    schedules = [
        CourseScheduleRead(
            id=s.id,
            course_id=s.course_id,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            room=s.room,
        )
        for s in course.schedules
    ]

    return CourseReadWithSchedule(
        id=course.id,
        course_code=course.course_code,
        course_name=course.course_name,
        credits=course.credits,
        available_seats=course.available_seats,
        description=course.description,
        schedules=schedules,
    )
