from sqlmodel import SQLModel

# Models
from .faculty_model import Faculty
from .role_model import Role
from .course_teacher_link import CourseTeacherLink
from .user_model import User
from .course_model import Course
from .enrollment_model import Enrollment
from .course_schedule_model import CourseSchedule
from .announcement_model import Announcement
from .event_model import Event
from .event_enrollment_model import EventEnrollment
from .room_model import Room
from .location_model import Location

# __all__ สำหรับ import *
__all__ = [
    "User",
    "Faculty",
    "Role",
    "Course",
    "CourseSchedule",
    "Enrollment",
    "CourseTeacherLink",
    "Announcement",
    "Event",
    "EventEnrollment",
    "Room",
    "Location",
]
