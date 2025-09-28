import pytest
from app.services.location_service import LocationService
from app.models.location_model import Location


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
