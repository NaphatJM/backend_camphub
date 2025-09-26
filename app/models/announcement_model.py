from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.bookmark_model import AnnouncementBookmark


class Announcement(SQLModel, table=True):
    __tablename__ = "announcements"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    description: str
    image_url: Optional[str] = None
    start_date: datetime
    end_date: datetime
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    creator: Optional["User"] = Relationship(back_populates="announcements")
    bookmarks: List["AnnouncementBookmark"] = Relationship(
        back_populates="announcement"
    )
