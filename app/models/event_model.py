from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index
from datetime import datetime


if TYPE_CHECKING:
    from .user_model import User
    from .event_enrollment_model import EventEnrollment


class Event(SQLModel, table=True):
    __tablename__ = "event"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    start_date: datetime = Field(index=True)
    end_date: datetime = Field(index=True)
    capacity: int | None = Field(
        default=None, description="Max participants, None = unlimited"
    )
    is_active: bool = Field(default=True, index=True)
    image_url: Optional[str] = None
    created_by: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_by: int = Field(foreign_key="user.id")
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )

    # Performance indexes
    __table_args__ = (
        Index("idx_event_active_dates", "is_active", "start_date", "end_date"),
        Index("idx_event_search_title", "title"),
        Index("idx_event_created_by_date", "created_by", "created_at"),
    )

    # Relationships
    creator: "User" = Relationship(
        back_populates="created_events",
        sa_relationship_kwargs={"foreign_keys": "[Event.created_by]"},
    )
    updater: "User" = Relationship(
        back_populates="updated_events",
        sa_relationship_kwargs={"foreign_keys": "[Event.updated_by]"},
    )
    enrollments: list["EventEnrollment"] = Relationship(back_populates="event")
