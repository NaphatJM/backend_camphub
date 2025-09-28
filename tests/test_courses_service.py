import pytest
from app.services.courses_service import CourseService
from app.models.user_model import User
from app.schemas.course_schema import CourseCreate
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_create_duplicate_course_code(session: AsyncSession):
    user = User(id=1, role_id=1)  # Professor
    service = CourseService(session=session, current_user=user)
    course_data = {
        "course_code": "CS999",
        "course_name": "Test",
        "credits": 3,
        "available_seats": 10,
        "description": "desc",
    }
    await service.create(data=CourseCreate(**course_data))
    with pytest.raises(HTTPException) as exc:
        await service.create(data=CourseCreate(**course_data))
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_student_cannot_create_course(session: AsyncSession):
    user = User(id=2, role_id=2)  # Student
    service = CourseService(session=session, current_user=user)
    course_data = {
        "course_code": "CS888",
        "course_name": "Test2",
        "credits": 3,
        "available_seats": 10,
        "description": "desc",
    }
    with pytest.raises(HTTPException) as exc:
        await service.create(data=CourseCreate(**course_data))
    assert exc.value.status_code == 403
