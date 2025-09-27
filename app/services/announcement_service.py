from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
import math

from app.core.base_service import BaseService
from app.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ValidationException,
    DatabaseError,
)
from app.core.cache import cached, cache_invalidate, CACHE_CONFIG
from app.core.permissions import PermissionChecker, PermissionEnum
from app.models.announcement_model import Announcement
from app.models.user_model import User
from app.schemas.announcement_schema import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementRead,
    AnnouncementListResponse,
)
from app.services import announcement_image_service


class AnnouncementService(
    BaseService[Announcement, AnnouncementCreate, AnnouncementUpdate, AnnouncementRead]
):
    """บริการประกาศขั้นสูงพร้อม caching และการจัดการข้อผิดพลาดครบถ้วน"""

    def __init__(self, session: AsyncSession, current_user: Optional[User] = None):
        super().__init__(Announcement, session, current_user)

    @property
    def resource_name(self) -> str:
        return "ประกาศ"

    def check_permission(self, action: str, resource_id: Optional[Any] = None) -> None:
        """ตรวจสอบสิทธิ์สำหรับการดำเนินการประกาศ"""
        if not self.current_user:
            raise PermissionDeniedError("จำเป็นต้องลงชื่อเข้าใช้", "announcement")

        if action == "create":
            if not PermissionChecker.has_permission(
                self.current_user, PermissionEnum.ANNOUNCEMENT_CREATE
            ):
                raise PermissionDeniedError("สร้างประกาศ", "announcement")

        elif action == "update":
            if resource_id:
                # ตรวจสอบว่าผู้ใช้สามารถแก้ไขประกาศใดๆ หรือของตัวเองได้
                if not PermissionChecker.can_access_resource(
                    self.current_user,
                    resource_id,
                    PermissionEnum.ANNOUNCEMENT_UPDATE_OWN,
                    PermissionEnum.ANNOUNCEMENT_UPDATE_ANY,
                ):
                    raise PermissionDeniedError("แก้ไขประกาศ", "announcement")

        elif action == "delete":
            if resource_id:
                if not PermissionChecker.can_access_resource(
                    self.current_user,
                    resource_id,
                    PermissionEnum.ANNOUNCEMENT_DELETE_OWN,
                    PermissionEnum.ANNOUNCEMENT_DELETE_ANY,
                ):
                    raise PermissionDeniedError("ลบประกาศ", "announcement")

    @cached(ttl_seconds=CACHE_CONFIG["default_ttl"], key_prefix="announcement")
    async def get_active_announcements(
        self, page: int = 1, per_page: int = 10, category: Optional[str] = None
    ) -> AnnouncementListResponse:
        """ดึงประกาศที่ใช้งานอยู่พร้อม pagination และ caching"""
        try:
            # ตรวจสอบพารามิเตอร์ pagination
            if page < 1:
                raise ValidationException("หน้าต้องมากกว่าหรือเท่ากับ 1", "page", page)
            if per_page < 1 or per_page > 100:
                raise ValidationException(
                    "จำนวนรายการต่อหน้าต้องอยู่ระหว่าง 1 ถึง 100", "per_page", per_page
                )

            # สร้าง query สำหรับประกาศที่ใช้งานอยู่
            now = datetime.now()
            stmt = select(Announcement).where(
                and_(Announcement.start_date <= now, Announcement.end_date >= now)
            )

            if category:
                stmt = stmt.where(Announcement.category == category)

            # นับจำนวนรายการทั้งหมด
            count_stmt = select(func.count(Announcement.id)).where(
                and_(Announcement.start_date <= now, Announcement.end_date >= now)
            )
            if category:
                count_stmt = count_stmt.where(Announcement.category == category)

            total_result = await self.session.execute(count_stmt)
            total = total_result.scalar()

            # คำนวณ pagination
            offset = (page - 1) * per_page
            total_pages = math.ceil(total / per_page) if total > 0 else 0

            # ดึงผลลัพธ์แบบ paginated
            stmt = (
                stmt.order_by(Announcement.created_at.desc())
                .offset(offset)
                .limit(per_page)
            )
            result = await self.session.execute(stmt)
            announcements = result.scalars().all()

            # แปลงเป็น read schemas
            items = [self._to_read_schema(ann) for ann in announcements]

            return AnnouncementListResponse(
                items=items,
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
            )

        except ValidationException:
            raise
        except Exception as e:
            raise DatabaseError(
                message="ไม่สามารถดึงข้อมูลประกาศได้",
                operation="get_active_announcements",
            ) from e

    @cache_invalidate("announcement:*")
    async def create_with_image(
        self, create_data: AnnouncementCreate, image_file: Optional[Any] = None
    ) -> AnnouncementRead:
        """สร้างประกาศพร้อมอัปโหลดรูปภาพ (ถ้ามี)"""
        self.check_permission("create")

        try:
            # จัดการอัปโหลดรูปภาพ (ถ้ามี)
            image_url = None
            if image_file:
                image_url, _ = await announcement_image_service.save_image(
                    image_file, "announcement"
                )

            # เตรียมข้อมูลประกาศ
            data_dict = create_data.model_dump()
            data_dict["image_url"] = image_url
            data_dict["created_by"] = self.current_user.id

            # สร้างประกาศ
            announcement = Announcement(**data_dict)
            self.session.add(announcement)
            await self.session.commit()
            await self.session.refresh(announcement)

            return self._to_read_schema(announcement)

        except Exception as e:
            await self.session.rollback()
            # ลบไฟล์ที่อัปโหลดแล้วหากการสร้างประกาศล้มเหลว
            if image_url:
                announcement_image_service.delete_image(image_url)

            raise DatabaseError(
                message="ไม่สามารถสร้างประกาศได้", operation="create_with_image"
            ) from e

    @cache_invalidate("announcement:*")
    async def update_with_image(
        self,
        announcement_id: int,
        update_data: AnnouncementUpdate,
        image_file: Optional[Any] = None,
        remove_image: bool = False,
    ) -> AnnouncementRead:
        """อัปเดตประกาศพร้อมจัดการรูปภาพ"""
        # ดึงประกาศที่มีอยู่
        announcement = await self.session.get(Announcement, announcement_id)
        if not announcement:
            raise NotFoundError("ประกาศ", announcement_id)

        # ตรวจสอบสิทธิ์
        self.check_permission("update", announcement.created_by)

        try:
            # จัดการรูปภาพ
            if remove_image and announcement.image_url:
                announcement_image_service.delete_image(announcement.image_url)
                announcement.image_url = None
            elif image_file:
                new_url, _ = await announcement_image_service.replace_image(
                    image_file, announcement.image_url, "announcement"
                )
                announcement.image_url = new_url

            # อัปเดตฟิลด์อื่นๆ
            data_dict = update_data.model_dump(exclude_unset=True)
            data_dict["updated_by"] = self.current_user.id

            for field, value in data_dict.items():
                if hasattr(announcement, field) and field != "image_url":
                    setattr(announcement, field, value)

            await self.session.commit()
            await self.session.refresh(announcement)

            return self._to_read_schema(announcement)

        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message="ไม่สามารถอัปเดตประกาศได้", operation="update_with_image"
            ) from e

    @cache_invalidate("announcement:*")
    async def delete_with_cleanup(self, announcement_id: int) -> Dict[str, Any]:
        """ลบประกาศพร้อมลบรูปภาพที่เกี่ยวข้อง"""
        announcement = await self.session.get(Announcement, announcement_id)
        if not announcement:
            raise NotFoundError("ประกาศ", announcement_id)

        self.check_permission("delete", announcement.created_by)

        try:
            # ลบรูปภาพที่เกี่ยวข้อง (ถ้ามี)
            if announcement.image_url:
                announcement_image_service.delete_image(announcement.image_url)

            await self.session.delete(announcement)
            await self.session.commit()

            return {"success": True, "message": "ลบประกาศสำเร็จ"}

        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message="ไม่สามารถลบประกาศได้", operation="delete_with_cleanup"
            ) from e

    @cached(ttl_seconds=CACHE_CONFIG["long_ttl"], key_prefix="announcement")
    async def get_categories(self) -> List[Dict[str, str]]:
        """ดึงหมวดหมู่ประกาศที่มีอยู่"""
        from app.models.announcement_model import AnnouncementCategory

        return [
            {"value": AnnouncementCategory.ACADEMIC, "label": "วิชาการ"},
            {"value": AnnouncementCategory.ACTIVITY, "label": "กิจกรรม"},
            {"value": AnnouncementCategory.GENERAL, "label": "ทั่วไป"},
        ]

    async def get_user_announcements(self, user_id: int) -> List[AnnouncementRead]:
        """ดึงประกาศที่สร้างโดยผู้ใช้คนใดคนหนึ่ง"""
        try:
            stmt = select(Announcement).where(Announcement.created_by == user_id)
            result = await self.session.execute(stmt)
            announcements = result.scalars().all()

            return [self._to_read_schema(ann) for ann in announcements]

        except Exception as e:
            raise DatabaseError(
                message="ไม่สามารถดึงประกาศของผู้ใช้ได้",
                operation="get_user_announcements",
            ) from e
