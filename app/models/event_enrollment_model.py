from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from .event_model import Event
    from .user_model import User


class EventEnrollment(SQLModel, table=True):
    __tablename__ = "event_enrollment"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    user_id: int = Field(foreign_key="user.id")
    status: str = Field(default="enrolled")  # e.g., enrolled, canceled
    enrollment_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    event: "Event" = Relationship(back_populates="enrollments")
    user: "User" = Relationship(back_populates="event_enrollments")
