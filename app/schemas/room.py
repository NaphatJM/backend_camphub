from typing import Optional
from sqlmodel import SQLModel
from .location import LocationRead


class RoomBase(SQLModel):
    name: str
    description: Optional[str] = None
    location_id: int  # FK ไป Location


class RoomCreate(RoomBase):
    pass


class RoomUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location_id: Optional[int] = None


class RoomRead(RoomBase):
    id: int
    location: Optional[LocationRead] = None
