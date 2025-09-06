from typing import Optional
from sqlmodel import SQLModel


class RoleRead(SQLModel):
    id: int
    name: str
    description: str


class RoleCreate(SQLModel):
    name: str
    description: str


class RoleUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
