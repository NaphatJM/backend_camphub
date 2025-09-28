import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from sqlmodel import SQLModel
from app.main import app
from app.core.db import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

from app.models.user_model import User
from app.models.faculty_model import Faculty
from app.models.role_model import Role
from app.models.announcement_model import Announcement, AnnouncementCategory

# Load test environment variables
load_dotenv(".env.test")


@pytest_asyncio.fixture
async def engine():
    """Create test database engine."""
    # Use SQLite in-memory for faster tests
    sql_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        sql_url,
        connect_args={"check_same_thread": False},
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Create test database session."""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(session):
    """Create test client with dependency override."""

    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override

    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://localhost:8000"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def setup_base_data(session):
    student_role = Role(id=1, name="Student", description="นักศึกษา")
    teacher_role = Role(id=2, name="Teacher", description="อาจารย์")
    session.add(student_role)
    session.add(teacher_role)
    faculty = Faculty(id=1, name="คณะวิทยาศาสตร์และเทคโนโลยี")
    session.add(faculty)
    await session.commit()
    return {
        "student_role": student_role,
        "teacher_role": teacher_role,
        "faculty": faculty,
    }


@pytest_asyncio.fixture
async def authenticated_user(client, setup_base_data):
    signup_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "birth_date": "2000-01-01",
        "faculty_id": 1,
        "year_of_study": 3,
        "role_id": 2,
    }
    response = await client.post("/api/auth/signup", json=signup_data)
    token = response.json()["access_token"]
    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_data": signup_data,
    }


@pytest_asyncio.fixture
async def sample_announcement(session, authenticated_user):
    from sqlalchemy import select

    result = await session.exec(select(User).where(User.username == "testuser"))
    user = result.scalar_one()
    now = datetime.now()
    announcement = Announcement(
        title="Sample Announcement",
        description="Sample description",
        category=AnnouncementCategory.GENERAL,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=5),
        created_by=user.id,
    )
    session.add(announcement)
    await session.commit()
    await session.refresh(announcement)
    return announcement
