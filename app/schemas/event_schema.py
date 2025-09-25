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

    @property
    def is_full(self) -> bool:
        """ตรวจสอบว่า event เต็มแล้วหรือยัง"""
        if self.capacity is None:
            return False
        return self.enrolled_count >= self.capacity

    @property
    def available_seats(self) -> Optional[int]:
        """จำนวนที่นั่งที่เหลือ"""
        if self.capacity is None:
            return None
        return max(0, self.capacity - self.enrolled_count)

    @property
    def capacity_status(self) -> str:
        """สถานะ capacity"""
        if self.capacity is None:
            return "ไม่จำกัด"
        if self.is_full:
            return "เต็มแล้ว"
        return f"เหลือ {self.available_seats} ที่นั่ง"


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

    @property
    def is_full(self) -> bool:
        """ตรวจสอบว่า event เต็มแล้วหรือยัง"""
        if self.capacity is None:
            return False
        return self.enrolled_count >= self.capacity

    @property
    def available_seats(self) -> Optional[int]:
        """จำนวนที่นั่งที่เหลือ"""
        if self.capacity is None:
            return None
        return max(0, self.capacity - self.enrolled_count)

    @property
    def capacity_status(self) -> str:
        """สถานะ capacity"""
        if self.capacity is None:
            return "ไม่จำกัด"
        if self.is_full:
            return "เต็มแล้ว"
        return f"เหลือ {self.available_seats} ที่นั่ง"
