from typing import Optional
from sqlmodel import SQLModel, Field


class CourseTeacherLink(SQLModel, table=True):
    __tablename__ = "course_teacher_link"

    course_id: Optional[int] = Field(
        default=None, foreign_key="course.id", primary_key=True
    )
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
