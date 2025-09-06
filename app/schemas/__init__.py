from .user_schema import (
    Token,
    LoginRequest,
    SignUpRequest,
    MeRead,
    MeUpdate,
)
from .faculty_schema import (
    FacultyRead,
    FacultyCreate,
    FacultyUpdate,
)
from .role_schema import (
    RoleRead,
    RoleCreate,
    RoleUpdate,
)

__all__ = [
    # Auth & User schemas
    "Token",
    "LoginRequest",
    "SignUpRequest",
    "MeRead",
    "MeUpdate",
    # Faculty schemas
    "FacultyRead",
    "FacultyCreate",
    "FacultyUpdate",
    # Role schemas
    "RoleRead",
    "RoleCreate",
    "RoleUpdate",
]
