from fastapi import APIRouter
from .endpoints import (
    auth_route,
    user_route,
    faculty_route,
    course_schedule_route,
    announcement_route,
    event_route,
)

router = APIRouter(prefix="/api")

router.include_router(auth_route.router)
router.include_router(user_route.router)
router.include_router(faculty_route.router)
router.include_router(course_schedule_route.router)
router.include_router(announcement_route.router)
router.include_router(event_route.router)
