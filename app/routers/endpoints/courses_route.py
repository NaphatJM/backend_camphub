from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_session
from app.models import User
from app.schemas.course_schema import CourseCreate, CourseRead, CourseUpdate
from app.services.courses_service import CourseService  # <- class-based

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/", response_model=list[CourseRead])
async def get_courses(
    session: AsyncSession = Depends(get_session),
):
    service = CourseService(session)
    return await service.get_all()


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(
    course_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = CourseService(session)
    return await service.get_by_id(course_id)


@router.post("/", response_model=CourseRead)
async def create_course(
    data: CourseCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = CourseService(session, current_user)
    return await service.create(data)


@router.put("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = CourseService(session, current_user)
    return await service.update(course_id, data)


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = CourseService(session, current_user)
    return await service.delete(course_id)
