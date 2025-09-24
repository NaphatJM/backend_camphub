from typing import Optional, Literal
from datetime import time
from sqlmodel import SQLModel

DayOfWeek = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]


class CourseScheduleBase(SQLModel):
    course_id: int
    day_of_week: DayOfWeek  # ใช้ Literal แทน str
    start_time: time
    end_time: time
    room: str


class CourseScheduleCreate(CourseScheduleBase):
    pass


class CourseScheduleUpdate(SQLModel):
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room: Optional[str] = None


class CourseScheduleRead(CourseScheduleBase):
    id: int
