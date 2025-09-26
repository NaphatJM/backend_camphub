from typing import Optional, Literal
from datetime import time
from sqlmodel import SQLModel
from .room import RoomRead
from .course_schema import CourseSimple

DayOfWeek = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]


class CourseScheduleBase(SQLModel):
    course_id: int
    room_id: int
    day_of_week: DayOfWeek
    start_time: time
    end_time: time


class CourseScheduleCreate(CourseScheduleBase):
    pass


class CourseScheduleUpdate(SQLModel):
    course_id: Optional[int] = None
    room_id: Optional[int] = None
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class CourseScheduleRead(CourseScheduleBase):
    id: int


class CourseScheduleReadWithRoom(CourseScheduleRead):
    room: Optional[RoomRead] = None
    course: Optional[CourseSimple] = None
