from typing import TYPE_CHECKING, Optional
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Relationship

from .course_teacher_link import CourseTeacherLink

if TYPE_CHECKING:
    from .faculty_model import Faculty
    from .role_model import Role
    from .course_model import Course
    from .enrollment_model import Enrollment
    from .announcement_model import Announcement


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    first_name: str
    last_name: str
    birth_date: date
    faculty_id: Optional[int] = Field(default=None, foreign_key="faculty.id")
    year_of_study: Optional[int] = None
    role_id: int = Field(default=2, foreign_key="role.id")  # 1: Professor, 2: Student

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    faculty: Optional["Faculty"] = Relationship(back_populates="users")
    role: "Role" = Relationship(back_populates="users")
    courses: list["Course"] = Relationship(
        back_populates="teachers", link_model=CourseTeacherLink
    )
    enrollments: list["Enrollment"] = Relationship(back_populates="user")
    announcements: list["Announcement"] = Relationship(back_populates="creator")
