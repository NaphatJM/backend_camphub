from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime


if TYPE_CHECKING:
    from .user_model import User


class Event(SQLModel, table=True):
    __tablename__ = "event"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    image_url: Optional[str] = None
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_by: int = Field(foreign_key="user.id")
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )

    # Relationships
    creator: "User" = Relationship(
        back_populates="created_events",
        sa_relationship_kwargs={"foreign_keys": "[Event.created_by]"},
    )
    updater: "User" = Relationship(
        back_populates="updated_events",
        sa_relationship_kwargs={"foreign_keys": "[Event.updated_by]"},
    )
