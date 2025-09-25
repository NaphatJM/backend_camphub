from typing import Optional
from sqlmodel import SQLModel


class LocationBase(SQLModel):
    name: str
    code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(SQLModel):
    name: Optional[str] = None
    code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None


class LocationRead(LocationBase):
    id: int
