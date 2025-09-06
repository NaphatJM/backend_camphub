from typing import Optional
from sqlmodel import SQLModel


class FacultyRead(SQLModel):
    id: int
    name: str


class FacultyCreate(SQLModel):
    name: str


class FacultyUpdate(SQLModel):
    name: Optional[str] = None
