import pytest
from app.services.enrollment_service import EnrollmentService
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock
from app.schemas.enrollment_schema import EnrollmentCreate


@pytest.mark.asyncio
async def test_get_course_enrollments_empty():
    session = MagicMock()
    session.exec = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=lambda: []))
        )
    )
    service = EnrollmentService(session, current_user=MagicMock(id=1))
    result = await service.get_course_enrollments(course_id=1)
    assert result.total_enrolled == 0
    assert result.enrolled_users == []


@pytest.mark.asyncio
async def test_enroll_course_not_found():
    session = MagicMock()
    session.get = AsyncMock(return_value=None)
    service = EnrollmentService(session, current_user=MagicMock(id=1))
    data = EnrollmentCreate(course_id=1)
    with pytest.raises(HTTPException) as exc:
        await service.enroll(data)
    assert exc.value.status_code == 404
    assert "Course not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_cancel_enrollment_not_found():
    session = MagicMock()
    session.exec = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=lambda: None))
        )
    )
    service = EnrollmentService(session, current_user=MagicMock(id=1))
    with pytest.raises(HTTPException) as exc:
        await service.cancel(course_id=1)
    assert exc.value.status_code == 404
    assert "Enrollment not found" in str(exc.value.detail)
