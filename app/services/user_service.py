from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.base_service import BaseService
from app.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ValidationException,
    ConflictError,
    DatabaseError,
)
from app.core.cache import cached, cache_invalidate, CacheManager, CACHE_CONFIG
from app.core.permissions import PermissionChecker, PermissionEnum
from app.core.security import hash_password, verify_password
from app.models.user_model import User
from app.schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserRead,
    MeUpdate,
    MeRead,
    PasswordUpdate,
)
from app.services import profile_image_service


class UserService(BaseService[User, UserCreate, UserUpdate, UserRead]):
    """Enhanced user service with comprehensive features"""

    def __init__(self, session: AsyncSession, current_user: Optional[User] = None):
        super().__init__(User, session, current_user)

    @property
    def resource_name(self) -> str:
        return "User"

    def check_permission(self, action: str, resource_id: Optional[Any] = None) -> None:
        """Check permissions for user operations"""
        if not self.current_user:
            raise PermissionDeniedError("จำเป็นต้องเข้าสู่ระบบ", "user")

        if action == "create":
            # Only admins can create users directly
            if not PermissionChecker.has_permission(
                self.current_user, PermissionEnum.USER_UPDATE_ANY
            ):
                raise PermissionDeniedError("สร้างผู้ใช้", "user")

        elif action in ["update", "delete"]:
            if resource_id:
                # User can update/delete their own profile or admin can update/delete any
                if (
                    self.current_user.id != resource_id
                    and not PermissionChecker.has_permission(
                        self.current_user, PermissionEnum.USER_UPDATE_ANY
                    )
                ):
                    raise PermissionDeniedError(f"{action} ผู้ใช้", "user")

    @cached(ttl_seconds=CACHE_CONFIG["short_ttl"], key_prefix="user")
    async def get_by_id_with_relations(self, user_id: int) -> UserRead:
        """Get user by ID with related data"""
        try:
            stmt = (
                select(User)
                .options(joinedload(User.role), joinedload(User.faculty))
                .where(User.id == user_id)
            )

            result = await self.session.execute(stmt)
            user = result.scalars().first()

            if not user:
                raise NotFoundError("User", user_id)

            return self._to_read_schema(user)

        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(
                message="ไม่สามารถดึงข้อมูลผู้ใช้พร้อมความสัมพันธ์ได้",
                operation="get_by_id_with_relations",
            ) from e

    async def get_by_username(self, username: str) -> Optional[UserRead]:
        """Get user by username"""
        try:
            stmt = select(User).where(User.username == username)
            result = await self.session.execute(stmt)
            user = result.scalars().first()

            return self._to_read_schema(user) if user else None

        except Exception as e:
            raise DatabaseError(
                message="ไม่สามารถดึงข้อมูลผู้ใช้จากชื่อผู้ใช้ได้",
                operation="get_by_username",
            ) from e

    async def get_by_email(self, email: str) -> Optional[UserRead]:
        """Get user by email"""
        try:
            stmt = select(User).where(User.email == email)
            result = await self.session.execute(stmt)
            user = result.scalars().first()

            return self._to_read_schema(user) if user else None

        except Exception as e:
            raise DatabaseError(
                message="ไม่สามารถดึงข้อมูลผู้ใช้จากอีเมลได้", operation="get_by_email"
            ) from e

    @cache_invalidate("user:*")
    async def create_user(self, create_data: UserCreate) -> UserRead:
        """Create new user with validation"""
        self.check_permission("create")

        try:
            # Check if username already exists
            existing_username = await self.get_by_username(create_data.username)
            if existing_username:
                raise ConflictError("Username", "ชื่อผู้ใช้นี้มีอยู่แล้ว")

            # Check if email already exists
            existing_email = await self.get_by_email(create_data.email)
            if existing_email:
                raise ConflictError("Email", "อีเมลนี้มีอยู่แล้ว")

            # Validate faculty exists if provided
            if create_data.faculty_id:
                from app.models.faculty_model import Faculty

                faculty_result = await self.session.execute(
                    select(Faculty).where(Faculty.id == create_data.faculty_id)
                )
                if not faculty_result.scalar_one_or_none():
                    raise ValidationException(
                        "รหัสคณะไม่ถูกต้อง", "faculty_id", create_data.faculty_id
                    )

            # Validate role exists if provided
            if create_data.role_id:
                from app.models.role_model import Role

                role_result = await self.session.execute(
                    select(Role).where(Role.id == create_data.role_id)
                )
                if not role_result.scalar_one_or_none():
                    raise ValidationException(
                        "รหัสบทบาทไม่ถูกต้อง", "role_id", create_data.role_id
                    )

            # Create user
            data_dict = create_data.model_dump()
            data_dict["hashed_password"] = hash_password(create_data.password)
            data_dict.pop("password", None)

            user = User(**data_dict)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

            return await self.get_by_id_with_relations(user.id)

        except (ConflictError, ValidationException):
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message="ไม่สามารถสร้างผู้ใช้ได้", operation="create_user"
            ) from e

    @cache_invalidate("user:*")
    async def update_profile(self, user_id: int, update_data: MeUpdate) -> MeRead:
        """Update user profile"""
        self.check_permission("update", user_id)

        try:
            user = await self.session.get(User, user_id)
            if not user:
                raise NotFoundError("User", user_id)

            # Validate faculty if being updated
            if update_data.faculty_id is not None:
                from app.models.faculty_model import Faculty

                faculty_result = await self.session.execute(
                    select(Faculty).where(Faculty.id == update_data.faculty_id)
                )
                if not faculty_result.scalar_one_or_none():
                    raise ValidationException(
                        "รหัสคณะไม่ถูกต้อง", "faculty_id", update_data.faculty_id
                    )

            # Update fields
            data_dict = update_data.model_dump(exclude_unset=True)
            for field, value in data_dict.items():
                if hasattr(user, field):
                    setattr(user, field, value)

            await self.session.commit()
            await self.session.refresh(user)

            # Return with relations
            return await self.get_by_id_with_relations(user_id)

        except (NotFoundError, ValidationException):
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message="ไม่สามารถอัปเดตโปรไฟล์ผู้ใช้ได้", operation="update_profile"
            ) from e

    @cache_invalidate("user:*")
    async def update_password(
        self, user_id: int, password_data: PasswordUpdate
    ) -> Dict[str, Any]:
        """Update user password with validation"""
        # Only user themselves or admin can change password
        if self.current_user.id != user_id and not PermissionChecker.has_permission(
            self.current_user, PermissionEnum.USER_UPDATE_ANY
        ):
            raise PermissionDeniedError("อัปเดตรหัสผ่าน", "user")

        try:
            user = await self.session.get(User, user_id)
            if not user:
                raise NotFoundError("User", user_id)

            # Verify current password if not admin
            if self.current_user.id == user_id and not verify_password(
                password_data.current_password, user.hashed_password
            ):
                raise ValidationException("รหัสผ่านปัจจุบันไม่ถูกต้อง", "current_password")

            # Update password
            user.hashed_password = hash_password(password_data.new_password)
            await self.session.commit()

            return {"success": True, "message": "อัปเดตรหัสผ่านเรียบร้อยแล้ว"}

        except (NotFoundError, ValidationException):
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message="ไม่สามารถอัปเดตรหัสผ่านได้", operation="update_password"
            ) from e

    @cache_invalidate("user:*")
    async def upload_profile_image(
        self, user_id: int, image_file: Any
    ) -> Dict[str, Any]:
        """Upload and update profile image"""
        if self.current_user.id != user_id and not PermissionChecker.has_permission(
            self.current_user, PermissionEnum.USER_UPDATE_ANY
        ):
            raise PermissionDeniedError("อัปโหลดรูปโปรไฟล์", "user")

        try:
            user = await self.session.get(User, user_id)
            if not user:
                raise NotFoundError("User", user_id)

            # Upload new image
            image_url, _ = await profile_image_service.replace_image(
                image_file, user.profile_image_url, "profile"
            )

            user.profile_image_url = image_url
            await self.session.commit()
            await self.session.refresh(user)

            return {
                "success": True,
                "message": "อัปเดตรูปโปรไฟล์เรียบร้อยแล้ว",
                "image_url": image_url,
            }

        except NotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message="ไม่สามารถอัปโหลดรูปโปรไฟล์ได้",
                operation="upload_profile_image",
            ) from e

    @cache_invalidate("user:*")
    async def remove_profile_image(self, user_id: int) -> Dict[str, Any]:
        """Remove user profile image"""
        if self.current_user.id != user_id and not PermissionChecker.has_permission(
            self.current_user, PermissionEnum.USER_UPDATE_ANY
        ):
            raise PermissionDeniedError("ลบรูปโปรไฟล์", "user")

        try:
            user = await self.session.get(User, user_id)
            if not user:
                raise NotFoundError("User", user_id)

            if user.profile_image_url:
                profile_image_service.delete_image(user.profile_image_url)
                user.profile_image_url = None
                await self.session.commit()

            return {"success": True, "message": "ลบรูปโปรไฟล์เรียบร้อยแล้ว"}

        except NotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message="ไม่สามารถลบรูปโปรไฟล์ได้",
                operation="remove_profile_image",
            ) from e

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics and activity"""
        try:
            # This could include various stats like:
            # - Number of announcements created
            # - Number of events created/enrolled
            # - Number of courses enrolled
            # - Recent activity, etc.

            stats = {
                "user_id": user_id,
                "stats": {
                    "announcements_created": 0,
                    "events_created": 0,
                    "events_enrolled": 0,
                    "courses_enrolled": 0,
                },
            }

            # TODO: Implement actual stats calculation
            return stats

        except Exception as e:
            raise DatabaseError(
                message="ไม่สามารถดึงสถิติผู้ใช้ได้", operation="get_user_stats"
            ) from e
