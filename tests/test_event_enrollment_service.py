import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.event_enrollment_service import EventEnrollmentService
from app.schemas.event_enrollment_schema import EventEnrollmentCreate
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_enroll_event_not_found():
    session = MagicMock()
    session.get = AsyncMock(return_value=None)  # Event not found
    service = EventEnrollmentService(session=session, current_user=MagicMock(id=1))
    data = EventEnrollmentCreate(event_id=123)
    with pytest.raises(HTTPException) as exc:
        await service.enroll(data)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_event_enrollments_empty():
    session = MagicMock()
    session.exec = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=lambda: []))
        )
    )
    service = EventEnrollmentService(session=session, current_user=MagicMock(id=1))
    with patch.object(
        EventEnrollmentService, "_get_enrollment_count", AsyncMock(return_value=0)
    ):
        result = await service.get_event_enrollments(event_id=1)
    assert result.total_enrolled == 0
    assert result.enrolled_users == []
