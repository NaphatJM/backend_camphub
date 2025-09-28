import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.course_schedule_service import CourseScheduleService
from app.schemas.course_schedule_schema import (
    CourseScheduleCreate,
    CourseScheduleUpdate,
)
from fastapi import HTTPException
import datetime
from types import SimpleNamespace


@pytest.mark.asyncio
async def test_create_schedule_room_not_found():
    session = MagicMock()
    session.get = AsyncMock(return_value=None)  # Room not found
    # ต้องกำหนด role_id=1 เพื่อผ่าน permission check
    service = CourseScheduleService(session=session, current_user=MagicMock(role_id=1))
    data = CourseScheduleCreate(
        room_id=999,
        course_id=1,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        day_of_week="Monday",  # Changed from 'MON' to 'Monday'
    )
    with pytest.raises(HTTPException) as exc:
        await service.create(data)
    assert exc.value.status_code == 404
    assert "Room not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    session = MagicMock()
    session.get = AsyncMock(return_value=None)
    service = CourseScheduleService(session=session)
    with pytest.raises(HTTPException) as exc:
        await service.get_by_id(123)
    assert exc.value.status_code == 404
    assert "Schedule not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_get_all_success():
    session = MagicMock()
    fake_course = SimpleNamespace(
        id=1, course_code="CS101", course_name="Test", credits=3
    )
    fake_schedule = SimpleNamespace(
        id=1,
        course_id=1,
        room_id=1,
        day_of_week="Monday",
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        course=fake_course,
        room=None,
    )
    session.exec = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=lambda: [fake_schedule]))
        )
    )
    service = CourseScheduleService(session=session)
    result = await service.get_all()
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_all_empty():
    session = MagicMock()
    session.exec = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=lambda: []))
        )
    )
    service = CourseScheduleService(session=session)
    result = await service.get_all()
    assert result == []


@pytest.mark.asyncio
async def test_get_by_course_id_success():
    session = MagicMock()
    fake_course = SimpleNamespace(
        id=1, course_code="CS101", course_name="Test", credits=3
    )
    fake_schedule = SimpleNamespace(
        id=1,
        course_id=1,
        room_id=1,
        day_of_week="Monday",
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        course=fake_course,
        room=None,
    )
    session.exec = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=lambda: [fake_schedule]))
        )
    )
    service = CourseScheduleService(session=session)
    result = await service.get_by_course_id(1)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_by_course_id_not_found():
    session = MagicMock()
    session.exec = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=lambda: []))
        )
    )
    service = CourseScheduleService(session=session)
    with pytest.raises(HTTPException) as exc:
        await service.get_by_course_id(1)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_success():
    session = MagicMock()
    session.get = AsyncMock(return_value=MagicMock())
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    service = CourseScheduleService(session=session, current_user=MagicMock(role_id=1))
    data = CourseScheduleCreate(
        room_id=1,
        course_id=1,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        day_of_week="Monday",
    )
    # Mock schedule object for _to_read_with_room
    fake_course = SimpleNamespace(
        id=1, course_code="CS101", course_name="Test", credits=3
    )
    fake_schedule = SimpleNamespace(
        id=1,
        course_id=1,
        room_id=1,
        day_of_week="Monday",
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        course=fake_course,
        room=None,
    )
    session.refresh = AsyncMock(side_effect=lambda obj: obj)
    service._to_read_with_room = MagicMock(return_value=fake_schedule)
    result = await service.create(data)
    assert result is not None


@pytest.mark.asyncio
async def test_update_success():
    session = MagicMock()
    fake_course = SimpleNamespace(
        id=1, course_code="CS101", course_name="Test", credits=3
    )
    fake_schedule = SimpleNamespace(
        id=1,
        course_id=1,
        room_id=1,
        day_of_week="Monday",
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        course=fake_course,
        room=None,
    )
    session.get = AsyncMock(side_effect=[fake_schedule, MagicMock()])
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    service = CourseScheduleService(session=session, current_user=MagicMock(role_id=1))
    data = CourseScheduleUpdate(room_id=1)
    service._to_read_with_room = MagicMock(return_value=fake_schedule)
    result = await service.update(1, data)
    assert result is not None


@pytest.mark.asyncio
async def test_update_room_not_found():
    session = MagicMock()
    fake_schedule = SimpleNamespace(
        id=1,
        course_id=1,
        room_id=1,
        day_of_week="Monday",
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        course=None,
        room=None,
    )
    # First get returns schedule, second get returns None (room not found)
    session.get = AsyncMock(side_effect=[fake_schedule, None])
    service = CourseScheduleService(session=session, current_user=MagicMock(role_id=1))
    data = CourseScheduleUpdate(room_id=2)
    with pytest.raises(HTTPException) as exc:
        await service.update(1, data)
    assert exc.value.status_code == 404
    assert "Room not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_update_schedule_not_found():
    session = MagicMock()
    session.get = AsyncMock(return_value=None)
    service = CourseScheduleService(session=session, current_user=MagicMock(role_id=1))
    data = CourseScheduleUpdate(room_id=1)
    with pytest.raises(HTTPException) as exc:
        await service.update(1, data)
    assert exc.value.status_code == 404
    assert "Schedule not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_delete_success():
    session = MagicMock()
    fake_schedule = SimpleNamespace(
        id=1,
        course_id=1,
        room_id=1,
        day_of_week="Monday",
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        course=None,
        room=None,
    )
    session.get = AsyncMock(return_value=fake_schedule)
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    service = CourseScheduleService(session=session, current_user=MagicMock(role_id=1))
    result = await service.delete(1)
    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_delete_not_found():
    session = MagicMock()
    session.get = AsyncMock(return_value=None)
    service = CourseScheduleService(session=session, current_user=MagicMock(role_id=1))
    with pytest.raises(HTTPException) as exc:
        await service.delete(1)
    assert exc.value.status_code == 404
    assert "Schedule not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_get_all_for_user_success():
    session = MagicMock()
    fake_course = SimpleNamespace(
        id=1, course_code="CS101", course_name="Test", credits=3
    )
    fake_schedule = SimpleNamespace(
        id=1,
        course_id=1,
        room_id=1,
        day_of_week="Monday",
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
        course=fake_course,
        room=None,
    )
    session.exec = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(
                    unique=MagicMock(
                        return_value=MagicMock(all=lambda: [fake_schedule])
                    )
                )
            )
        )
    )
    service = CourseScheduleService(session=session, current_user=MagicMock(id=1))
    result = await service.get_all_for_user()
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_all_for_user_empty():
    session = MagicMock()
    session.exec = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(
                    unique=MagicMock(return_value=MagicMock(all=lambda: []))
                )
            )
        )
    )
    service = CourseScheduleService(session=session, current_user=MagicMock(id=1))
    result = await service.get_all_for_user()
    assert result == []
