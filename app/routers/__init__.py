from fastapi import APIRouter
from . import endpoints

router = APIRouter(prefix="/api")

router.include_router(endpoints.auth_route.router)
router.include_router(endpoints.user_route.router)
