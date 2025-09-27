from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum


# Category Enum
class AnnouncementCategory(str, Enum):
    ACADEMIC = "วิชาการ"
    ACTIVITY = "กิจกรรม"
    GENERAL = "ทั่วไป"


if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.bookmark_model import AnnouncementBookmark


class Announcement(SQLModel, table=True):
    __tablename__ = "announcements"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200, index=True)
    description: str
    category: AnnouncementCategory = Field(
        default=AnnouncementCategory.GENERAL, index=True
    )
    image_url: Optional[str] = None
    start_date: datetime = Field(index=True)
    end_date: datetime = Field(index=True)
    created_by: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Performance indexes
    __table_args__ = (
        Index("idx_announcement_active_period", "start_date", "end_date"),
        Index("idx_announcement_category_dates", "category", "start_date", "end_date"),
        Index("idx_announcement_title_search", "title"),
    )

    # Relationships
    creator: Optional["User"] = Relationship(back_populates="announcements")
    bookmarks: List["AnnouncementBookmark"] = Relationship(
        back_populates="announcement"
    )
