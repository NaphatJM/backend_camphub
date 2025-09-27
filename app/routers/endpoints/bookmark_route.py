from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.db import get_session
from app.models import User
from app.core.deps import get_current_user
from app.schemas.announcement_schema import BookmarkResponse, BookmarkListResponse
from app.services.bookmark_service import BookmarkService

router = APIRouter(prefix="/annc", tags=["bookmarks"])


@router.post("/{announcement_id}/bookmark", response_model=BookmarkResponse)
async def create_bookmark(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a bookmark for an announcement"""
    service = BookmarkService(session, current_user)
    return await service.create_bookmark(announcement_id)


@router.delete("/{announcement_id}/bookmark")
async def delete_bookmark(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a bookmark for an announcement"""
    service = BookmarkService(session, current_user)
    return await service.delete_bookmark(announcement_id)


@router.get("/bookmarks", response_model=BookmarkListResponse)
async def get_user_bookmarks(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all bookmarks for current user with pagination"""
    service = BookmarkService(session, current_user)
    return await service.get_user_bookmarks(page, per_page)


@router.get("/{announcement_id}/bookmark-status")
async def check_bookmark_status(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Check bookmark status for an announcement"""
    service = BookmarkService(session, current_user)
    return await service.check_bookmark_status(announcement_id)
