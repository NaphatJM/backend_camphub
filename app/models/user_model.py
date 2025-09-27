from typing import TYPE_CHECKING, Optional, List
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index
from pydantic import computed_field


from .course_teacher_link import CourseTeacherLink

if TYPE_CHECKING:
    from .faculty_model import Faculty
    from .role_model import Role
    from .course_model import Course
    from .enrollment_model import Enrollment
    from .announcement_model import Announcement
    from .event_model import Event
    from .event_enrollment_model import EventEnrollment
    from .bookmark_model import AnnouncementBookmark


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    first_name: str
    last_name: str
    birth_date: date
    faculty_id: Optional[int] = Field(
        default=None, foreign_key="faculty.id", index=True
    )
    year_of_study: Optional[int] = None
    role_id: int = Field(
        default=2, foreign_key="role.id", index=True
    )  # 1: Professor, 2: Student
    profile_image_url: str | None = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Performance indexes
    __table_args__ = (
        Index(
            "idx_user_role_faculty", "role_id", "faculty_id"
        ),  # Composite for filtering
        Index("idx_user_created_at", "created_at"),
    )

    # Relationships
    faculty: Optional["Faculty"] = Relationship(back_populates="users")
    role: "Role" = Relationship(back_populates="users")
    courses: list["Course"] = Relationship(
        back_populates="teachers", link_model=CourseTeacherLink
    )
    enrollments: list["Enrollment"] = Relationship(back_populates="user")
    announcements: list["Announcement"] = Relationship(back_populates="creator")
    created_events: list["Event"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "[Event.created_by]"},
    )
    updated_events: list["Event"] = Relationship(
        back_populates="updater",
        sa_relationship_kwargs={"foreign_keys": "[Event.updated_by]"},
    )
    event_enrollments: list["EventEnrollment"] = Relationship(back_populates="user")
    bookmarked_announcements: List["AnnouncementBookmark"] = Relationship(
        back_populates="user"
    )

    @computed_field
    def age(self) -> Optional[int]:
        if not self.birth_date:
            return None
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    @computed_field
    def fullname(self) -> str:
        return f"{self.first_name} {self.last_name}"
