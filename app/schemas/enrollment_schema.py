from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel
from .user_schema import UserSimple
from .course_schema import CourseSimple


class EnrollmentBase(SQLModel):
    course_id: int
    user_id: int


class EnrollmentCreate(SQLModel):
    course_id: int


class EnrollmentRead(EnrollmentBase):
    id: int
    enrollment_at: datetime
    user: Optional[UserSimple] = None
    course: Optional[CourseSimple] = None


class EnrollmentStatus(SQLModel):
    is_enrolled: bool
    enrollment_id: Optional[int] = None
    enrollment_at: Optional[datetime] = None
    message: str


class EnrollmentListResponse(SQLModel):
    enrollments: List[EnrollmentRead]
    total: int
    page: int
    per_page: int
    total_pages: int


class StudentEnrollmentResponse(SQLModel):
    enrolled_courses: List[CourseSimple]
    total_credits: int


class CourseEnrollmentResponse(SQLModel):
    enrolled_students: List[UserSimple]
    total_students: int
    available_seats: int
