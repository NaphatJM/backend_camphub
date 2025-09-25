from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .room_model import Room


class Location(SQLModel, table=True):
    __tablename__ = "locations"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, nullable=False)  # ชื่ออาคาร
    code: str = Field(max_length=50, nullable=False, unique=True)  # รหัส เช่น ENG1
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

    # Relationships
    rooms: List["Room"] = Relationship(back_populates="location")
