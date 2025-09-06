from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, String


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(
        sa_column=Column(String, unique=True, index=True, nullable=False)
    )
    email: str = Field(
        sa_column=Column(String, unique=True, index=True, nullable=False)
    )
    hashed_password: str
    first_name: str
    last_name: str
    birth_date: date
    faculty_id: Optional[int] = Field(default=None, foreign_key="faculty.id")
    year_of_study: Optional[int] = None
    role_id: int = Field(default=2, foreign_key="role.id")  # 1: Professor, 2: Student
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column=Column(onupdate=datetime.now)
    )
    created_at: datetime = Field(default_factory=datetime.now)
