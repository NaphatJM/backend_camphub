from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel


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
    # สามารถใส่ nested object ของ user และ course ได้ถ้าต้องการ
    fullname: Optional[str] = None
    course_name: Optional[str] = None


# Summary ของ course
class EnrollmentSummary(SQLModel):
    course_id: int
    total_enrolled: int
    enrolled_users: List[str]  # ชื่อผู้เรียน
