from fastapi import APIRouter
from .endpoints import (
    auth_route,
    user_route,
    faculty_route,
    announcement_route,
    event_route,
    courses_route,
    enrollment_route,
    course_schedule_route,
    event_enrollment_route,
    room_route,
    location_route,
)

router = APIRouter(prefix="/api")

router.include_router(auth_route.router)
router.include_router(user_route.router)
router.include_router(faculty_route.router)
router.include_router(announcement_route.router)
router.include_router(event_route.router)
router.include_router(event_enrollment_route.router)
router.include_router(courses_route.router)
router.include_router(enrollment_route.router)
router.include_router(course_schedule_route.router)
router.include_router(room_route.router)
router.include_router(location_route.router)
