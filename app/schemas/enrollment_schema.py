from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel
from app.schemas.course_schedule_schema import CourseScheduleReadWithRoom


# Base fields ของ Enrollment
class EnrollmentBase(SQLModel):
    course_id: int
    user_id: int
    status: Optional[str] = "enrolled"


# สร้าง enrollment ใหม่
class EnrollmentCreate(SQLModel):
    course_id: int


# Update enrollment (เช่น เปลี่ยน status)
class EnrollmentUpdate(SQLModel):
    status: Optional[str] = None


# Response แบบ Read
class EnrollmentRead(EnrollmentBase):
    id: int
    enrollment_at: datetime


# Summary ของ course
class EnrollmentSummary(SQLModel):
    course_id: int
    course_code: str
    course_name: str
    total_enrolled: int
    enrolled_users: List[str]  # ชื่อผู้เรียน


class EnrollmentReadWithSchedule(SQLModel):
    id: int
    course_id: int
    user_id: int
    status: str
    enrollment_at: datetime
    fullname: Optional[str] = None
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    schedules: Optional[List[CourseScheduleReadWithRoom]] = []
