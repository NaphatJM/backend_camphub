from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel
from datetime import datetime

T = TypeVar("T")


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    image_url: Optional[str] = None
    capacity: Optional[int] = None
    is_active: bool = True


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    image_url: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None


class EventResponse(EventBase):
    id: int
    created_by: int
    created_at: datetime
    updated_by: int
    updated_at: datetime
    enrolled_count: int = 0  # เพิ่มจำนวนผู้ลงทะเบียน

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    id: int
    title: str
    start_date: datetime
    end_date: datetime
    image_url: Optional[str] = None
    created_by: int
    capacity: Optional[int] = None
    is_active: bool = True
    enrolled_count: int = 0  # เพิ่มจำนวนผู้ลงทะเบียน

    class Config:
        from_attributes = True


class PaginationResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class EventListPaginationResponse(PaginationResponse[EventListResponse]):
    pass
