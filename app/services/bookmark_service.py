from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.core.base_service import BaseService
from app.core.exceptions import (
    NotFoundError,
    ConflictError,
    DatabaseError,
    PermissionDeniedError,
    ValidationException,
)
from app.core.cache import cached, cache_invalidate, CACHE_CONFIG
from app.models.bookmark_model import AnnouncementBookmark
from app.models.announcement_model import Announcement
from app.models.user_model import User
from app.schemas.announcement_schema import BookmarkResponse, BookmarkListResponse


class BookmarkService(BaseService[AnnouncementBookmark, None, None, BookmarkResponse]):
    """Bookmark service for announcement bookmarks"""

    def __init__(self, session: AsyncSession, current_user: Optional[User] = None):
        super().__init__(AnnouncementBookmark, session, current_user)

    @property
    def resource_name(self) -> str:
        return "Bookmark"

    def check_permission(self, action: str, resource_id: Optional[Any] = None) -> None:
        """Check permissions for bookmark operations"""
        if not self.current_user:
            raise PermissionDeniedError("Authentication required", "bookmark")

        # Users can only manage their own bookmarks
        # Additional permission checks can be added here if needed

    async def create_bookmark(self, announcement_id: int) -> BookmarkResponse:
        """Create a bookmark for an announcement"""
        if not self.current_user:
            raise PermissionDeniedError("Authentication required", "bookmark")

        try:
            # Check if announcement exists
            announcement = await self.session.get(Announcement, announcement_id)
            if not announcement:
                raise NotFoundError("Announcement", announcement_id)

            # Check if bookmark already exists
            existing_stmt = select(AnnouncementBookmark).where(
                and_(
                    AnnouncementBookmark.user_id == self.current_user.id,
                    AnnouncementBookmark.announcement_id == announcement_id,
                )
            )
            existing_result = await self.session.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()

            if existing:
                raise ConflictError(
                    "Bookmark", "You have already bookmarked this announcement"
                )

            # Create new bookmark
            new_bookmark = AnnouncementBookmark(
                user_id=self.current_user.id, announcement_id=announcement_id
            )

            self.session.add(new_bookmark)
            await self.session.commit()
            await self.session.refresh(new_bookmark)

            # Get bookmark with announcement data
            bookmark_with_ann_stmt = (
                select(AnnouncementBookmark)
                .options(selectinload(AnnouncementBookmark.announcement))
                .where(AnnouncementBookmark.id == new_bookmark.id)
            )

            result = await self.session.execute(bookmark_with_ann_stmt)
            bookmark = result.scalar_one()

            return BookmarkResponse(
                id=bookmark.id,
                user_id=bookmark.user_id,
                announcement_id=bookmark.announcement_id,
                created_at=bookmark.created_at,
                announcement=bookmark.announcement,
            )

        except (NotFoundError, ConflictError):
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message="Failed to create bookmark", operation="create_bookmark"
            ) from e

    async def delete_bookmark(self, announcement_id: int) -> Dict[str, Any]:
        """Delete a bookmark for an announcement"""
        if not self.current_user:
            raise PermissionDeniedError("Authentication required", "bookmark")

        try:
            # Find the bookmark to delete
            bookmark_stmt = select(AnnouncementBookmark).where(
                and_(
                    AnnouncementBookmark.user_id == self.current_user.id,
                    AnnouncementBookmark.announcement_id == announcement_id,
                )
            )
            bookmark_result = await self.session.execute(bookmark_stmt)
            bookmark = bookmark_result.scalar_one_or_none()

            if not bookmark:
                raise NotFoundError("Bookmark")

            await self.session.delete(bookmark)
            await self.session.commit()

            return {"success": True, "message": "Bookmark deleted successfully"}

        except NotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message="Failed to delete bookmark", operation="delete_bookmark"
            ) from e

    @cached(ttl_seconds=CACHE_CONFIG["short_ttl"], key_prefix="bookmark")
    async def get_user_bookmarks(
        self, page: int = 1, per_page: int = 10
    ) -> BookmarkListResponse:
        """Get paginated bookmarks for current user"""
        if not self.current_user:
            raise PermissionDeniedError("Authentication required", "bookmark")

        try:
            # Validate pagination parameters
            if page < 1:
                raise ValidationException("Page must be >= 1", "page", page)
            if per_page < 1 or per_page > 100:
                raise ValidationException(
                    "Per page must be between 1 and 100", "per_page", per_page
                )

            # Count total bookmarks
            count_stmt = select(func.count(AnnouncementBookmark.id)).where(
                AnnouncementBookmark.user_id == self.current_user.id
            )
            total_result = await self.session.execute(count_stmt)
            total = total_result.scalar()

            # Calculate pagination
            offset = (page - 1) * per_page
            total_pages = (total + per_page - 1) // per_page if total > 0 else 1

            # Get bookmarks with announcements
            bookmarks_stmt = (
                select(AnnouncementBookmark)
                .options(selectinload(AnnouncementBookmark.announcement))
                .where(AnnouncementBookmark.user_id == self.current_user.id)
                .order_by(AnnouncementBookmark.created_at.desc())
                .offset(offset)
                .limit(per_page)
            )

            bookmarks_result = await self.session.execute(bookmarks_stmt)
            bookmarks = bookmarks_result.scalars().all()

            # Convert to response format
            bookmark_responses = [
                BookmarkResponse(
                    id=bookmark.id,
                    user_id=bookmark.user_id,
                    announcement_id=bookmark.announcement_id,
                    created_at=bookmark.created_at,
                    announcement=bookmark.announcement,
                )
                for bookmark in bookmarks
            ]

            return BookmarkListResponse(
                bookmarks=bookmark_responses,
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
            )

        except ValidationException:
            raise
        except Exception as e:
            raise DatabaseError(
                message="Failed to retrieve user bookmarks",
                operation="get_user_bookmarks",
            ) from e

    async def check_bookmark_status(self, announcement_id: int) -> Dict[str, Any]:
        """Check if user has bookmarked an announcement"""
        if not self.current_user:
            raise PermissionDeniedError("Authentication required", "bookmark")

        try:
            bookmark_stmt = select(AnnouncementBookmark).where(
                and_(
                    AnnouncementBookmark.user_id == self.current_user.id,
                    AnnouncementBookmark.announcement_id == announcement_id,
                )
            )
            bookmark_result = await self.session.execute(bookmark_stmt)
            bookmark = bookmark_result.scalar_one_or_none()

            return {
                "is_bookmarked": bookmark is not None,
                "bookmark_id": bookmark.id if bookmark else None,
                "created_at": bookmark.created_at if bookmark else None,
            }

        except Exception as e:
            raise DatabaseError(
                message="Failed to check bookmark status",
                operation="check_bookmark_status",
            ) from e

    async def get_bookmarked_announcements_count(
        self, user_id: Optional[int] = None
    ) -> int:
        """Get count of bookmarked announcements for a user"""
        target_user_id = user_id or (
            self.current_user.id if self.current_user else None
        )

        if not target_user_id:
            raise PermissionDeniedError("Authentication required", "bookmark")

        try:
            count_stmt = select(func.count(AnnouncementBookmark.id)).where(
                AnnouncementBookmark.user_id == target_user_id
            )
            result = await self.session.execute(count_stmt)
            return result.scalar()

        except Exception as e:
            raise DatabaseError(
                message="Failed to get bookmarks count",
                operation="get_bookmarked_announcements_count",
            ) from e
