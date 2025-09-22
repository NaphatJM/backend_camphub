from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel


class EventEnrollmentBase(SQLModel):
    event_id: int
    user_id: int
    status: Optional[str] = "enrolled"


class EventEnrollmentCreate(SQLModel):
    event_id: int


class EventEnrollmentUpdate(SQLModel):
    status: Optional[str] = None


class EventEnrollmentRead(EventEnrollmentBase):
    id: int
    enrollment_at: datetime
    fullname: Optional[str] = None
    title: Optional[str] = None


class EventEnrollmentSummary(SQLModel):
    event_id: int
    total_enrolled: int
    enrolled_users: List[str]
