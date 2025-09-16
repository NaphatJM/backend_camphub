from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel
from .user_schema import UserSimple


class AnnouncementBase(SQLModel):
    title: str
    description: str
    image_url: Optional[str] = None
    start_date: datetime
    end_date: datetime


class AnnouncementCreate(AnnouncementBase):
    created_by: int


class AnnouncementUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AnnouncementRead(AnnouncementBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime


class AnnouncementSimple(SQLModel):
    id: int
    title: str
    description: str
    start_date: datetime
    end_date: datetime


class AnnouncementListResponse(SQLModel):
    announcements: List[AnnouncementRead]
    total: int
    page: int
    per_page: int
    total_pages: int
