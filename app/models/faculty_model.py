from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user_model import User


class Faculty(SQLModel, table=True):
    __tablename__ = "faculty"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

    # Relationships
    users: list["User"] = Relationship(back_populates="faculty")
