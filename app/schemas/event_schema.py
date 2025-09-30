from typing import Optional
from pydantic import BaseModel
from datetime import datetime


def get_event_is_full(capacity: Optional[int], enrolled_count: int) -> bool:
    if capacity is None:
        return False
    return enrolled_count >= capacity


def get_event_available_seats(
    capacity: Optional[int], enrolled_count: int
) -> Optional[int]:
    if capacity is None:
        return None
    return max(0, capacity - enrolled_count)


def get_event_capacity_status(capacity: Optional[int], enrolled_count: int) -> str:
    if capacity is None:
        return "ไม่จำกัด"
    if get_event_is_full(capacity, enrolled_count):
        return "เต็มแล้ว"
    return f"เหลือ {get_event_available_seats(capacity, enrolled_count)} ที่นั่ง"


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    capacity: Optional[int] = None
    is_active: bool = True
    image_url: Optional[str] = None
    location: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None
    location: Optional[str] = None


class EventResponse(EventBase):
    id: int
    created_by: int
    created_at: datetime
    updated_by: int
    updated_at: datetime
    enrolled_count: int = 0

    class Config:
        from_attributes = True

    @property
    def is_full(self) -> bool:
        return get_event_is_full(self.capacity, self.enrolled_count)

    @property
    def available_seats(self) -> Optional[int]:
        return get_event_available_seats(self.capacity, self.enrolled_count)

    @property
    def capacity_status(self) -> str:
        return get_event_capacity_status(self.capacity, self.enrolled_count)


class EventListResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    capacity: Optional[int] = None
    is_active: bool = True
    image_url: Optional[str] = None
    location: Optional[str] = None
    created_by: int
    enrolled_count: int = 0

    class Config:
        from_attributes = True

    @property
    def is_full(self) -> bool:
        return get_event_is_full(self.capacity, self.enrolled_count)

    @property
    def available_seats(self) -> Optional[int]:
        return get_event_available_seats(self.capacity, self.enrolled_count)

    @property
    def capacity_status(self) -> str:
        return get_event_capacity_status(self.capacity, self.enrolled_count)
