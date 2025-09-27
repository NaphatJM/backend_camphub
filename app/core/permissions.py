from enum import Enum
from typing import List, Optional, Dict, Any
from functools import wraps
from fastapi import Depends, HTTPException, status

from app.models.user_model import User
from app.core.deps import get_current_user
from app.core.exceptions import PermissionDeniedError


class RoleEnum(int, Enum):
    """User role enumeration"""

    ADMIN = 1
    TEACHER = 2
    STAFF = 3
    STUDENT = 4


class PermissionEnum(str, Enum):
    """Permission enumeration"""

    # User permissions
    USER_READ = "user:read"
    USER_UPDATE_SELF = "user:update_self"
    USER_UPDATE_ANY = "user:update_any"
    USER_DELETE_ANY = "user:delete_any"

    # Announcement permissions
    ANNOUNCEMENT_READ = "announcement:read"
    ANNOUNCEMENT_CREATE = "announcement:create"
    ANNOUNCEMENT_UPDATE_OWN = "announcement:update_own"
    ANNOUNCEMENT_UPDATE_ANY = "announcement:update_any"
    ANNOUNCEMENT_DELETE_OWN = "announcement:delete_own"
    ANNOUNCEMENT_DELETE_ANY = "announcement:delete_any"

    # Event permissions
    EVENT_READ = "event:read"
    EVENT_CREATE = "event:create"
    EVENT_UPDATE_OWN = "event:update_own"
    EVENT_UPDATE_ANY = "event:update_any"
    EVENT_DELETE_OWN = "event:delete_own"
    EVENT_DELETE_ANY = "event:delete_any"
    EVENT_ENROLL = "event:enroll"

    # Course permissions
    COURSE_READ = "course:read"
    COURSE_CREATE = "course:create"
    COURSE_UPDATE_OWN = "course:update_own"
    COURSE_UPDATE_ANY = "course:update_any"
    COURSE_DELETE_OWN = "course:delete_own"
    COURSE_DELETE_ANY = "course:delete_any"
    COURSE_ENROLL = "course:enroll"

    # Location & Room permissions
    LOCATION_READ = "location:read"
    LOCATION_MANAGE = "location:manage"
    ROOM_READ = "room:read"
    ROOM_MANAGE = "room:manage"

    # Faculty permissions
    FACULTY_READ = "faculty:read"
    FACULTY_MANAGE = "faculty:manage"


# Role-based permission mapping
ROLE_PERMISSIONS: Dict[RoleEnum, List[PermissionEnum]] = {
    RoleEnum.ADMIN: [
        # Full access to everything
        PermissionEnum.USER_READ,
        PermissionEnum.USER_UPDATE_SELF,
        PermissionEnum.USER_UPDATE_ANY,
        PermissionEnum.USER_DELETE_ANY,
        PermissionEnum.ANNOUNCEMENT_READ,
        PermissionEnum.ANNOUNCEMENT_CREATE,
        PermissionEnum.ANNOUNCEMENT_UPDATE_OWN,
        PermissionEnum.ANNOUNCEMENT_UPDATE_ANY,
        PermissionEnum.ANNOUNCEMENT_DELETE_OWN,
        PermissionEnum.ANNOUNCEMENT_DELETE_ANY,
        PermissionEnum.EVENT_READ,
        PermissionEnum.EVENT_CREATE,
        PermissionEnum.EVENT_UPDATE_OWN,
        PermissionEnum.EVENT_UPDATE_ANY,
        PermissionEnum.EVENT_DELETE_OWN,
        PermissionEnum.EVENT_DELETE_ANY,
        PermissionEnum.EVENT_ENROLL,
        PermissionEnum.COURSE_READ,
        PermissionEnum.COURSE_CREATE,
        PermissionEnum.COURSE_UPDATE_OWN,
        PermissionEnum.COURSE_UPDATE_ANY,
        PermissionEnum.COURSE_DELETE_OWN,
        PermissionEnum.COURSE_DELETE_ANY,
        PermissionEnum.COURSE_ENROLL,
        PermissionEnum.LOCATION_READ,
        PermissionEnum.LOCATION_MANAGE,
        PermissionEnum.ROOM_READ,
        PermissionEnum.ROOM_MANAGE,
        PermissionEnum.FACULTY_READ,
        PermissionEnum.FACULTY_MANAGE,
    ],
    RoleEnum.TEACHER: [
        # Teacher permissions - can manage own content
        PermissionEnum.USER_READ,
        PermissionEnum.USER_UPDATE_SELF,
        PermissionEnum.ANNOUNCEMENT_READ,
        PermissionEnum.ANNOUNCEMENT_CREATE,
        PermissionEnum.ANNOUNCEMENT_UPDATE_OWN,
        PermissionEnum.ANNOUNCEMENT_DELETE_OWN,
        PermissionEnum.EVENT_READ,
        PermissionEnum.EVENT_CREATE,
        PermissionEnum.EVENT_UPDATE_OWN,
        PermissionEnum.EVENT_DELETE_OWN,
        PermissionEnum.EVENT_ENROLL,
        PermissionEnum.COURSE_READ,
        PermissionEnum.COURSE_CREATE,
        PermissionEnum.COURSE_UPDATE_OWN,
        PermissionEnum.COURSE_DELETE_OWN,
        PermissionEnum.COURSE_ENROLL,
        PermissionEnum.LOCATION_READ,
        PermissionEnum.ROOM_READ,
        PermissionEnum.FACULTY_READ,
    ],
    RoleEnum.STAFF: [
        # Staff permissions - similar to admin but more restricted
        PermissionEnum.USER_READ,
        PermissionEnum.USER_UPDATE_SELF,
        PermissionEnum.ANNOUNCEMENT_READ,
        PermissionEnum.ANNOUNCEMENT_CREATE,
        PermissionEnum.ANNOUNCEMENT_UPDATE_ANY,
        PermissionEnum.ANNOUNCEMENT_DELETE_ANY,
        PermissionEnum.EVENT_READ,
        PermissionEnum.EVENT_CREATE,
        PermissionEnum.EVENT_UPDATE_ANY,
        PermissionEnum.EVENT_DELETE_ANY,
        PermissionEnum.EVENT_ENROLL,
        PermissionEnum.COURSE_READ,
        PermissionEnum.LOCATION_READ,
        PermissionEnum.LOCATION_MANAGE,
        PermissionEnum.ROOM_READ,
        PermissionEnum.ROOM_MANAGE,
        PermissionEnum.FACULTY_READ,
    ],
    RoleEnum.STUDENT: [
        # Student permissions - read-only and enrollment
        PermissionEnum.USER_READ,
        PermissionEnum.USER_UPDATE_SELF,
        PermissionEnum.ANNOUNCEMENT_READ,
        PermissionEnum.EVENT_READ,
        PermissionEnum.EVENT_ENROLL,
        PermissionEnum.COURSE_READ,
        PermissionEnum.COURSE_ENROLL,
        PermissionEnum.LOCATION_READ,
        PermissionEnum.ROOM_READ,
        PermissionEnum.FACULTY_READ,
    ],
}


class PermissionChecker:
    """Permission checking utility class"""

    @staticmethod
    def get_user_permissions(user: User) -> List[PermissionEnum]:
        """Get all permissions for a user based on their role"""
        if not user or not user.role_id:
            return []

        try:
            role = RoleEnum(user.role_id)
            return ROLE_PERMISSIONS.get(role, [])
        except ValueError:
            return []

    @staticmethod
    def has_permission(user: User, permission: PermissionEnum) -> bool:
        """Check if user has a specific permission"""
        user_permissions = PermissionChecker.get_user_permissions(user)
        return permission in user_permissions

    @staticmethod
    def has_any_permission(user: User, permissions: List[PermissionEnum]) -> bool:
        """Check if user has any of the specified permissions"""
        user_permissions = PermissionChecker.get_user_permissions(user)
        return any(perm in user_permissions for perm in permissions)

    @staticmethod
    def has_all_permissions(user: User, permissions: List[PermissionEnum]) -> bool:
        """Check if user has all of the specified permissions"""
        user_permissions = PermissionChecker.get_user_permissions(user)
        return all(perm in user_permissions for perm in permissions)

    @staticmethod
    def can_access_resource(
        user: User,
        resource_owner_id: Optional[int],
        own_permission: PermissionEnum,
        any_permission: PermissionEnum,
    ) -> bool:
        """Check if user can access a resource (either own or any)"""
        if not user:
            return False

        # Check if user can access any resource of this type
        if PermissionChecker.has_permission(user, any_permission):
            return True

        # Check if user can access their own resource and they own it
        if resource_owner_id and user.id == resource_owner_id:
            return PermissionChecker.has_permission(user, own_permission)

        return False


def require_permission(permission: PermissionEnum):
    """Decorator to require specific permission"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs or args
            current_user = None
            for key, value in kwargs.items():
                if key == "current_user" and isinstance(value, User):
                    current_user = value
                    break

            if not current_user:
                raise PermissionDeniedError("Authentication required", str(permission))

            if not PermissionChecker.has_permission(current_user, permission):
                raise PermissionDeniedError(
                    f"Required permission: {permission}",
                    f"User role: {current_user.role_id}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(*permissions: PermissionEnum):
    """Decorator to require any of the specified permissions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = None
            for key, value in kwargs.items():
                if key == "current_user" and isinstance(value, User):
                    current_user = value
                    break

            if not current_user:
                raise PermissionDeniedError("Authentication required")

            if not PermissionChecker.has_any_permission(
                current_user, list(permissions)
            ):
                raise PermissionDeniedError(
                    f"Required any permission: {', '.join(str(p) for p in permissions)}",
                    f"User role: {current_user.role_id}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles: RoleEnum):
    """Decorator to require specific role(s)"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = None
            for key, value in kwargs.items():
                if key == "current_user" and isinstance(value, User):
                    current_user = value
                    break

            if not current_user:
                raise PermissionDeniedError("Authentication required")

            if current_user.role_id not in [role.value for role in roles]:
                raise PermissionDeniedError(
                    f"Required role: {', '.join(str(r.name) for r in roles)}",
                    f"User role: {current_user.role_id}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# FastAPI dependency for permission checking
def require_permission_dependency(permission: PermissionEnum):
    """FastAPI dependency for permission checking"""

    def check_permission(current_user: User = Depends(get_current_user)):
        if not PermissionChecker.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permission: {permission}",
            )
        return current_user

    return check_permission


def require_role_dependency(*roles: RoleEnum):
    """FastAPI dependency for role checking"""

    def check_role(current_user: User = Depends(get_current_user)):
        if current_user.role_id not in [role.value for role in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(str(r.name) for r in roles)}",
            )
        return current_user

    return check_role
