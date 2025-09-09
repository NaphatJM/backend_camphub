from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from app.models.course_teacher_link import CourseTeacherLink

if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.enrollment_model import Enrollment


class Course(SQLModel, table=True):
    __tablename__ = "course"

    id: Optional[int] = Field(default=None, primary_key=True)
    course_code: str = Field(unique=True, index=True)
    course_name: str = Field(index=True)
    credits: int = Field(default=3)
    available_seats: int = Field(default=40)
    description: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    teachers: list["User"] = Relationship(
        back_populates="courses", link_model=CourseTeacherLink
    )
    enrollments: list["Enrollment"] = Relationship(back_populates="course")
