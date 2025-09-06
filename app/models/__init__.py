from typing import Iterator
from sqlmodel import SQLModel, Session, create_engine
from app.core.config import get_settings

from .user_model import User
from .faculty_model import Faculty
from .role_model import Role

settings = get_settings()

connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.SQLDB_URL,
    echo=False,
    connect_args=connect_args,
)


def init_db():
    """Initialize database and create all tables"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """Get database session"""
    with Session(engine) as session:
        yield session


__all__ = [
    "User",
    "Faculty",
    "Role",
    "init_db",
    "get_session",
    "engine",
]
