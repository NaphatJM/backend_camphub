from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index
from datetime import datetime

from .course_teacher_link import CourseTeacherLink

if TYPE_CHECKING:
    from .user_model import User
    from .enrollment_model import Enrollment
    from .course_schedule_model import CourseSchedule


class Course(SQLModel, table=True):
    __tablename__ = "course"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_code: str = Field(unique=True, index=True)
    course_name: str = Field(index=True)
    credits: int = Field(default=3, index=True)
    available_seats: int = Field(default=40)
    description: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now, index=True)

    # Performance indexes
    __table_args__ = (
        Index("idx_course_code_name", "course_code", "course_name"),
        Index("idx_course_credits_seats", "credits", "available_seats"),
    )

    # Relationships
    teachers: list["User"] = Relationship(
        back_populates="courses", link_model=CourseTeacherLink
    )
    enrollments: list["Enrollment"] = Relationship(back_populates="course")
    schedules: list["CourseSchedule"] = Relationship(back_populates="course")
