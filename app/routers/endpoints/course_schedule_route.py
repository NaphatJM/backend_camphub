from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.models import User
from app.schemas.course_schedule_schema import (
    CourseScheduleCreate,
    CourseScheduleRead,
    CourseScheduleUpdate,
)
from app.services.course_schedule_service import CourseScheduleService
from app.core.deps import get_current_user


router = APIRouter(prefix="/course_schedules", tags=["course_schedules"])


@router.get("/", response_model=List[CourseScheduleRead])
async def get_schedules(session: AsyncSession = Depends(get_session)):
    service = CourseScheduleService(session)
    return await service.get_all()


@router.get("/{schedule_id}", response_model=CourseScheduleRead)
async def get_schedule(schedule_id: int, session: AsyncSession = Depends(get_session)):
    service = CourseScheduleService(session)
    return await service.get_by_id(schedule_id)


@router.get("/course/{course_id}", response_model=List[CourseScheduleRead])
async def get_course_schedules(
    course_id: int, session: AsyncSession = Depends(get_session)
):
    service = CourseScheduleService(session)
    return await service.get_by_course_id(course_id)


@router.post("/", response_model=CourseScheduleRead)
async def create_schedule(
    data: CourseScheduleCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = CourseScheduleService(session, current_user)
    return await service.create(data)


@router.put("/{schedule_id}", response_model=CourseScheduleRead)
async def update_schedule(
    schedule_id: int,
    data: CourseScheduleUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = CourseScheduleService(session, current_user)
    return await service.update(schedule_id, data)


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = CourseScheduleService(session, current_user)
    return await service.delete(schedule_id)
