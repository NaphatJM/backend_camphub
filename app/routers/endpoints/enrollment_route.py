from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.models import User
from app.core.deps import get_current_user
from app.schemas.enrollment_schema import EnrollmentCreate
from app.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.get("/course/{course_id}")
async def get_course_enrollments(
    course_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = EnrollmentService(session=session, current_user=current_user)
    return await service.get_course_enrollments(course_id)


@router.post("/enroll")
async def enroll_course(
    data: EnrollmentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = EnrollmentService(session=session, current_user=current_user)
    return await service.enroll(data)


@router.delete("/cancel/{course_id}")
async def cancel_enroll(
    course_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = EnrollmentService(session=session, current_user=current_user)
    return await service.cancel(course_id)


@router.get("/user")
async def get_user_enrollments(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = EnrollmentService(session=session, current_user=current_user)
    return await service.get_user_enrollments()
