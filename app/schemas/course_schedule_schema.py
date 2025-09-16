from typing import List
from datetime import time
from sqlmodel import SQLModel


class CourseScheduleRead(SQLModel):
    id: int
    course_id: int
    day_of_week: str
    start_time: time
    end_time: time
    room: str


class CourseReadWithSchedule(SQLModel):
    id: int
    course_code: str
    course_name: str
    credits: int
    available_seats: int
    description: str
    schedules: List[CourseScheduleRead] = []
