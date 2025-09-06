from fastapi import APIRouter
from .endpoints import auth_route, user_route

router = APIRouter(prefix="/api")

router.include_router(auth_route.router)
router.include_router(user_route.router)
