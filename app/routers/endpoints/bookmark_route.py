from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.core.db import get_session
from app.models import User, Announcement, AnnouncementBookmark
from app.core.deps import get_current_user
from app.schemas.announcement_schema import BookmarkResponse, BookmarkListResponse

router = APIRouter(prefix="/annc/bookmarks", tags=["bookmarks"])


@router.get("/", response_model=BookmarkListResponse)
async def get_user_bookmarks(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """ดู bookmark ทั้งหมดของผู้ใช้ปัจจุบัน"""

    # นับจำนวน bookmark ทั้งหมด
    total_result = await session.exec(
        select(func.count(AnnouncementBookmark.id)).where(
            AnnouncementBookmark.user_id == current_user.id
        )
    )
    total = total_result.scalar() or 0

    # คำนวณ offset
    offset = (page - 1) * per_page

    # ดึงข้อมูล bookmarks พร้อม announcement
    bookmarks_result = await session.exec(
        select(AnnouncementBookmark)
        .options(selectinload(AnnouncementBookmark.announcement))
        .where(AnnouncementBookmark.user_id == current_user.id)
        .order_by(AnnouncementBookmark.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    bookmarks = bookmarks_result.scalars().all()

    # แปลงเป็น response models (handle announcement None ได้ตรง ๆ)
    bookmark_responses = [
        BookmarkResponse.model_validate(
            {
                "id": bookmark.id,
                "user_id": bookmark.user_id,
                "announcement_id": bookmark.announcement_id,
                "created_at": bookmark.created_at,
                "announcement": bookmark.announcement,
            }
        )
        for bookmark in bookmarks
    ]

    # คำนวณจำนวนหน้าทั้งหมด
    total_pages = (total + per_page - 1) // per_page if total else 1

    return BookmarkListResponse(
        bookmarks=bookmark_responses,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.post("/{announcement_id}", response_model=BookmarkResponse)
async def add_bookmark(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """สร้าง bookmark สำหรับ announcement"""

    # ตรวจสอบว่า announcement มีอยู่จริง
    announcement = await session.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="ไม่พบข่าวประกาศ")

    new_bookmark = AnnouncementBookmark(
        user_id=current_user.id,
        announcement_id=announcement_id,
    )

    try:
        session.add(new_bookmark)
        await session.commit()
        # refresh พร้อม preload relationship announcement
        await session.refresh(new_bookmark, attribute_names=["announcement"])

        return BookmarkResponse.model_validate(
            {
                "id": new_bookmark.id,
                "user_id": new_bookmark.user_id,
                "announcement_id": new_bookmark.announcement_id,
                "created_at": new_bookmark.created_at,
                "announcement": new_bookmark.announcement,
            }
        )

    except IntegrityError as e:
        await session.rollback()
        if "unique_user_announcement_bookmark" in str(e):
            raise HTTPException(status_code=409, detail="คุณได้ bookmark ข่าวประกาศนี้แล้ว")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดในการบันทึกข้อมูล")


@router.delete("/{announcement_id}")
async def remove_bookmark(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """ลบ bookmark สำหรับ announcement"""

    # ค้นหา bookmark ที่ต้องการลบ
    bookmark_result = await session.exec(
        select(AnnouncementBookmark).where(
            and_(
                AnnouncementBookmark.user_id == current_user.id,
                AnnouncementBookmark.announcement_id == announcement_id,
            )
        )
    )
    bookmark = bookmark_result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(status_code=404, detail="ไม่พบ bookmark นี้")
    if (
        bookmark.user_id != current_user.id
        and getattr(current_user, "role_id", None) != 1
    ):
        raise HTTPException(status_code=403, detail="คุณไม่มีสิทธิ์ลบ bookmark นี้")

    await session.delete(bookmark)
    await session.commit()

    return {"message": "ลบ bookmark เรียบร้อยแล้ว"}


@router.get("/{announcement_id}/status")
async def check_bookmark_status(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """ตรวจสอบสถานะ bookmark ของ announcement"""

    bookmark_result = await session.exec(
        select(AnnouncementBookmark).where(
            and_(
                AnnouncementBookmark.user_id == current_user.id,
                AnnouncementBookmark.announcement_id == announcement_id,
            )
        )
    )
    bookmark = bookmark_result.scalar_one_or_none()

    return {
        "is_bookmarked": bookmark is not None,
        "bookmark_id": bookmark.id if bookmark else None,
        "created_at": bookmark.created_at if bookmark else None,
    }
