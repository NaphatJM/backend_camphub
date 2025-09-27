from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.schemas.user_schema import SignUpRequest, LoginRequest, Token
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Token, status_code=201)
async def signup(payload: SignUpRequest, session: AsyncSession = Depends(get_session)):
    """Register a new user"""
    auth_service = AuthService(session)
    return await auth_service.register_user(payload)


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    """Authenticate user and return access token"""
    auth_service = AuthService(session)
    return await auth_service.authenticate_user(payload.username, payload.password)
