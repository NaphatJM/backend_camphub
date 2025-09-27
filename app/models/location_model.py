from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index

if TYPE_CHECKING:
    from .room_model import Room


class Location(SQLModel, table=True):
    __tablename__ = "locations"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, nullable=False, index=True)  # ชื่ออาคาร
    code: str = Field(
        max_length=50, nullable=False, unique=True, index=True
    )  # รหัส เช่น ENG1
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

    # Performance indexes
    __table_args__ = (
        Index("idx_location_name_code", "name", "code"),
        Index("idx_location_coordinates", "latitude", "longitude"),
    )

    # Relationships
    rooms: List["Room"] = Relationship(back_populates="location")
