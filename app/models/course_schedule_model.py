from typing import Optional, TYPE_CHECKING
from datetime import time
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index

if TYPE_CHECKING:
    from .course_model import Course
    from .room_model import Room


class CourseSchedule(SQLModel, table=True):
    __tablename__ = "course_schedule"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", nullable=False, index=True)
    room_id: int = Field(foreign_key="rooms.id", nullable=False, index=True)

    day_of_week: str = Field(max_length=20, nullable=False, index=True)
    start_time: time = Field(index=True)
    end_time: time = Field(index=True)

    # Performance indexes
    __table_args__ = (
        Index("idx_course_schedule_day_time", "day_of_week", "start_time", "end_time"),
        Index("idx_course_schedule_room_time", "room_id", "day_of_week", "start_time"),
        Index("idx_course_schedule_course", "course_id"),
    )

    # Relationships
    course: Optional["Course"] = Relationship(back_populates="schedules")
    room: Optional["Room"] = Relationship(back_populates="schedules")
