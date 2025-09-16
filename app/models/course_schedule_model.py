from typing import Optional, TYPE_CHECKING
from datetime import time
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .course_model import Course


class CourseSchedule(SQLModel, table=True):
    __tablename__ = "course_schedule"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id")  # FK ไปยัง Course

    day_of_week: str = Field(max_length=20)  # เช่น "Monday", "Tuesday"
    start_time: time
    end_time: time
    room: str = Field(max_length=50)

    # Relationship กลับไปที่ Course
    course: Optional["Course"] = Relationship(back_populates="schedules")
