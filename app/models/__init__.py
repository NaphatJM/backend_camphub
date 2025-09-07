from typing import AsyncIterator
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.config import get_settings

from .user_model import User
from .faculty_model import Faculty
from .role_model import Role
from .course_model import Course
from .enrollment_model import Enrollment
from .course_teacher_link import CourseTeacherLink

settings = get_settings()

# ✅ ใช้ async engine
async_engine = create_async_engine(
    settings.SQLDB_URL,
    echo=False,
    future=True,
)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSession(async_engine) as session:
        yield session


__all__ = [
    "User",
    "Faculty",
    "Role",
    "init_db",
    "get_session",
    "async_engine",
]
