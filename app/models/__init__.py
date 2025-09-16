from typing import AsyncIterator
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.config import get_settings

# Models
from .faculty_model import Faculty
from .role_model import Role
from .course_teacher_link import CourseTeacherLink
from .user_model import User
from .course_model import Course
from .enrollment_model import Enrollment
from .course_schedule_model import CourseSchedule
from .announcement_model import Announcement

settings = get_settings()

# ✅ Async engine
async_engine = create_async_engine(
    settings.SQLDB_URL,
    echo=False,
    future=True,
)


# Initialize all tables
async def init_db():
    async with async_engine.begin() as conn:
        # สร้างทุก table จาก metadata ของ SQLModel
        await conn.run_sync(SQLModel.metadata.create_all)


# Async session generator
async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSession(async_engine) as session:
        yield session


# __all__ สำหรับ import แบบ *
__all__ = [
    "User",
    "Faculty",
    "Role",
    "Course",
    "CourseSchedule",
    "Enrollment",
    "CourseTeacherLink",
    "Announcement",
    "init_db",
    "get_session",
    "async_engine",
]
