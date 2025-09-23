from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    capacity: Optional[int] = None
    is_active: bool = True
    image_url: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None


class EventResponse(EventBase):
    id: int
    created_by: int
    created_at: datetime
    updated_by: int
    updated_at: datetime
    enrolled_count: int = 0

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    capacity: Optional[int] = None
    is_active: bool = True
    image_url: Optional[str] = None
    created_by: int
    enrolled_count: int = 0

    class Config:
        from_attributes = True
