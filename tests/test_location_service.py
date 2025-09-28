import pytest
from app.services.location_service import LocationService
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock
from app.schemas.location import LocationCreate, LocationUpdate


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
async def test_create_location_duplicate(dummy_session):
    service = LocationService(dummy_session)

    # Simulate duplicate by raising exception in add
    def add_raise(obj):
        raise Exception("Duplicate location")

    dummy_session.add = add_raise
    with pytest.raises(Exception):
        await service.create_location(name="Test Location", address="123 Test St")


@pytest.mark.asyncio
async def test_get_by_id_not_found(dummy_session):
    dummy_session.get = AsyncMock(return_value=None)
    service = LocationService(dummy_session)
    with pytest.raises(HTTPException) as exc:
        await service.get_by_id(999)
    assert exc.value.status_code == 404
    assert "Location not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_update_location_not_found(dummy_session):
    dummy_session.get = AsyncMock(return_value=None)
    service = LocationService(dummy_session, current_user=MagicMock(role_id=1))
    data = LocationUpdate(name="B")
    with pytest.raises(HTTPException) as exc:
        await service.update(1, data)
    assert exc.value.status_code == 404
    assert "Location not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_delete_location_not_found(dummy_session):
    dummy_session.get = AsyncMock(return_value=None)
    service = LocationService(dummy_session, current_user=MagicMock(role_id=1))
    with pytest.raises(HTTPException) as exc:
        await service.delete(1)
    assert exc.value.status_code == 404
    assert "Location not found" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_permission_denied():
    session = MagicMock()
    service = LocationService(session, current_user=MagicMock(role_id=2))
    with pytest.raises(HTTPException) as exc:
        service._check_permission()
    assert exc.value.status_code == 403
    assert "not allowed" in str(exc.value.detail)
