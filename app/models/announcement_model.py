from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime

if TYPE_CHECKING:
    from .user_model import User


class Announcement(SQLModel, table=True):
    __tablename__ = "announcement"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    image_url: Optional[str] = None
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: datetime
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    creator: "User" = Relationship(back_populates="announcements")
