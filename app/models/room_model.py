from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index

if TYPE_CHECKING:
    from .location_model import Location
    from .course_schedule_model import CourseSchedule


class Room(SQLModel, table=True):
    __tablename__ = "rooms"

    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="locations.id", nullable=False, index=True)
    name: str = Field(max_length=50, nullable=False, index=True)  # เช่น A101
    description: Optional[str] = None

    # Performance indexes
    __table_args__ = (Index("idx_room_location_name", "location_id", "name"),)

    # Relationships
    location: Optional["Location"] = Relationship(back_populates="rooms")
    schedules: List["CourseSchedule"] = Relationship(back_populates="room")
