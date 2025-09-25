from typing import Optional, TYPE_CHECKING
from datetime import time
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .course_model import Course
    from .room_model import Room


class CourseSchedule(SQLModel, table=True):
    __tablename__ = "course_schedule"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", nullable=False)
    room_id: int = Field(foreign_key="rooms.id", nullable=False)

    day_of_week: str = Field(max_length=20, nullable=False)
    start_time: time
    end_time: time

    # Relationships
    course: Optional["Course"] = Relationship(back_populates="schedules")
    room: Optional["Room"] = Relationship(back_populates="schedules")
