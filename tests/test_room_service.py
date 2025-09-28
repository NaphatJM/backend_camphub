import pytest
from app.services.room_service import RoomService
from app.models.room_model import Room


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
