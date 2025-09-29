import pytest
from app.services.room_service import RoomService
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock
from app.schemas.room import RoomCreate, RoomUpdate


class DummySession:
    def __init__(self):
        self.added = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        pass


@pytest.fixture
def dummy_session():
    return DummySession()


@pytest.mark.asyncio
async def test_create_room_duplicate(dummy_session):
    service = RoomService(dummy_session)

    # Simulate duplicate by raising exception in add
    def add_raise(obj):
        raise Exception("Duplicate room")

    dummy_session.add = add_raise
    with pytest.raises(Exception):
        await service.create_room(name="Room 101", capacity=30)


@pytest.mark.asyncio
async def test_get_by_id_not_found(dummy_session):
    dummy_session.get = AsyncMock(return_value=None)
    service = RoomService(dummy_session)
    with pytest.raises(HTTPException) as exc:
        await service.get_by_id(999)
    assert exc.value.status_code == 404
    assert "Room not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_create_location_not_found(dummy_session):
    dummy_session.get = AsyncMock(return_value=None)
    service = RoomService(dummy_session, current_user=MagicMock(role_id=1))
    data = RoomCreate(name="A", capacity=10, location_id=1)
    with pytest.raises(HTTPException) as exc:
        await service.create(data)
    assert exc.value.status_code == 404
    assert "Location not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_update_room_not_found(dummy_session):
    dummy_session.get = AsyncMock(return_value=None)
    service = RoomService(dummy_session, current_user=MagicMock(role_id=1))
    data = RoomUpdate(name="B")
    with pytest.raises(HTTPException) as exc:
        await service.update(1, data)
    assert exc.value.status_code == 404
    assert "Room not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_update_location_not_found(dummy_session):
    # First get returns a room, second get returns None (location not found)
    dummy_session.get = AsyncMock(side_effect=[MagicMock(), None])
    service = RoomService(dummy_session, current_user=MagicMock(role_id=1))
    data = RoomUpdate(location_id=2)
    with pytest.raises(HTTPException) as exc:
        await service.update(1, data)
    assert exc.value.status_code == 404
    assert "Location not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_delete_room_not_found(dummy_session):
    dummy_session.get = AsyncMock(return_value=None)
    service = RoomService(dummy_session, current_user=MagicMock(role_id=1))
    with pytest.raises(HTTPException) as exc:
        await service.delete(1)
    assert exc.value.status_code == 404
    assert "Room not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_permission_denied():
    session = MagicMock()
    service = RoomService(session, current_user=MagicMock(role_id=2))
    with pytest.raises(HTTPException) as exc:
        service._check_permission()
    assert exc.value.status_code == 403
    assert "not allowed" in str(exc.value.detail)
