from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel
from .user_schema import UserSimple


class CourseBase(SQLModel):
    course_code: str
    course_name: str
    credits: int = 3
    available_seats: int = 40
    description: str = ""


class CourseCreate(CourseBase):
    teacher_ids: Optional[List[int]] = []


class CourseUpdate(SQLModel):
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    credits: Optional[int] = None
    available_seats: Optional[int] = None
    description: Optional[str] = None
    teacher_ids: Optional[List[int]] = None


class CourseRead(CourseBase):
    id: int
    created_at: datetime
    enrolled_count: Optional[int] = 0


class CourseSimple(SQLModel):
    id: int
    course_code: str
    course_name: str
    credits: int


class CourseReadWithDetails(CourseRead):
    teachers: List[UserSimple] = []
    faculty: Optional[str] = None  # Use FacultyRead schema if needed
    is_full: bool = False


class CourseFilter(SQLModel):
    faculty_id: Optional[int] = None
    credits: Optional[int] = None
    available_only: Optional[bool] = None
    search: Optional[str] = None


class CourseListResponse(SQLModel):
    courses: List[CourseRead]
    total: int
    page: int
    per_page: int
    total_pages: int
