from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from sqlalchemy import Index
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.announcement_model import Announcement


class AnnouncementBookmark(SQLModel, table=True):
    __tablename__ = "announcement_bookmarks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    announcement_id: int = Field(foreign_key="announcements.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)

    # Performance indexes
    __table_args__ = (
        UniqueConstraint(
            "user_id", "announcement_id", name="unique_user_announcement_bookmark"
        ),
        Index("idx_bookmark_user_announcement", "user_id", "announcement_id"),
        Index("idx_bookmark_created_at", "created_at"),
    )
