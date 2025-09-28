from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.announcement_model import Announcement


class AnnouncementBookmark(SQLModel, table=True):
    __tablename__ = "announcement_bookmarks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    announcement_id: int = Field(foreign_key="announcements.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # ✅ แก้ไขเป็น __table_args__ แทน Config class
    __table_args__ = (
        UniqueConstraint(
            "user_id", "announcement_id", name="unique_user_announcement_bookmark"
        ),
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="bookmarked_announcements")
    announcement: Optional["Announcement"] = Relationship(back_populates="bookmarks")
