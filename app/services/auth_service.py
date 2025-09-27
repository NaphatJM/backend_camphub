from typing import Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from datetime import datetime, date

from app.core.exceptions import ValidationException, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user_model import User
from app.models.faculty_model import Faculty
from app.models.role_model import Role
from app.schemas.user_schema import SignUpRequest, LoginRequest, Token


class AuthService:
    """
    Authentication service handling user registration,
    login, and token management
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, payload: SignUpRequest) -> Token:
        """Register new user with validation"""
        try:
            # Validate unique constraints
            await self._validate_unique_user(payload.username, payload.email)

            # Validate faculty if provided
            if payload.faculty_id:
                await self._validate_faculty(payload.faculty_id)

            # Validate role if provided
            if payload.role_id:
                await self._validate_role(payload.role_id)

            # Create user with validated data
            user = User(
                username=payload.username,
                email=payload.email,
                first_name=payload.first_name,
                last_name=payload.last_name,
                birth_date=payload.birth_date,
                faculty_id=payload.faculty_id,
                year_of_study=payload.year_of_study,
                role_id=payload.role_id,
                hashed_password=hash_password(payload.password),
            )

            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

            # Generate access token
            token = create_access_token({"sub": user.username})
            return Token(access_token=token)

        except (ConflictError, ValidationException):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise ValidationException(f"Registration failed: {str(e)}")

    async def authenticate_user(self, credentials: LoginRequest) -> Token:
        """Authenticate user and return access token"""
        try:
            # Find user by email
            result = await self.session.execute(
                select(User).where(User.email == credentials.email)
            )
            user = result.scalar_one_or_none()

            # Verify user exists and password is correct
            if not user or not verify_password(
                credentials.password, user.hashed_password
            ):
                raise ValidationException("Invalid email or password")

            # Generate access token
            token = create_access_token({"sub": user.username})
            return Token(access_token=token)

        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Authentication failed: {str(e)}")

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username with relations (for auth middleware)"""
        try:
            result = await self.session.execute(
                select(User)
                .options(
                    joinedload(User.role),
                    joinedload(User.faculty),
                )
                .where(User.username == username)
            )
            return result.scalar_one_or_none()

        except Exception:
            return None

    async def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> Dict[str, str]:
        """Change user password with current password verification"""
        try:
            user = await self.session.get(User, user_id)
            if not user:
                raise NotFoundError("User not found")

            # Verify current password
            if not verify_password(current_password, user.hashed_password):
                raise ValidationException("Current password is incorrect")

            # Update password
            user.hashed_password = hash_password(new_password)
            user.updated_at = datetime.now()

            await self.session.commit()

            return {"message": "Password changed successfully"}

        except (NotFoundError, ValidationException):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise ValidationException(f"Password change failed: {str(e)}")

    async def reset_password(self, email: str, new_password: str) -> Dict[str, str]:
        """Reset password (admin function)"""
        try:
            result = await self.session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if not user:
                raise NotFoundError("User with this email not found")

            # Update password
            user.hashed_password = hash_password(new_password)
            user.updated_at = datetime.now()

            await self.session.commit()

            return {"message": "Password reset successfully"}

        except NotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise ValidationException(f"Password reset failed: {str(e)}")

    # Private validation methods
    async def _validate_unique_user(self, username: str, email: str):
        """Validate that username and email are unique"""

        # Check username uniqueness
        username_result = await self.session.execute(
            select(User).where(User.username == username)
        )
        if username_result.scalar_one_or_none():
            raise ConflictError("Username already exists")

        # Check email uniqueness
        email_result = await self.session.execute(
            select(User).where(User.email == email)
        )
        if email_result.scalar_one_or_none():
            raise ConflictError("Email already exists")

    async def _validate_faculty(self, faculty_id: int):
        """Validate that faculty exists"""
        faculty_result = await self.session.execute(
            select(Faculty).where(Faculty.id == faculty_id)
        )
        if not faculty_result.scalar_one_or_none():
            raise ValidationException("Invalid faculty selected")

    async def _validate_role(self, role_id: int):
        """Validate that role exists"""
        role_result = await self.session.execute(select(Role).where(Role.id == role_id))
        if not role_result.scalar_one_or_none():
            raise ValidationException("Invalid role selected")

    # Account management
    async def deactivate_user(self, user_id: int) -> Dict[str, str]:
        """Deactivate user account (soft delete)"""
        try:
            user = await self.session.get(User, user_id)
            if not user:
                raise NotFoundError("User not found")

            # Add is_active field if needed, or use updated_at to mark
            user.updated_at = datetime.now()
            # user.is_active = False  # If you add this field to the model

            await self.session.commit()

            return {"message": "User account deactivated"}

        except NotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise ValidationException(f"Account deactivation failed: {str(e)}")

    async def verify_token_user(self, username: str) -> Optional[User]:
        """Verify user exists for token validation (used by auth middleware)"""
        return await self.get_user_by_username(username)
