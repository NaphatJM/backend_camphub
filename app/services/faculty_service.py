from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.base_service import BaseService
from app.core.exceptions import NotFoundError, ValidationException
from app.core.cache import cache_result
from app.models.faculty_model import Faculty
from app.models.user_model import User
from app.schemas.faculty_schema import FacultyRead, FacultyCreate, FacultyUpdate


class FacultyService(BaseService[Faculty, FacultyCreate, FacultyUpdate]):
    """
    Faculty management service with CRUD operations
    and caching for performance
    """

    def __init__(self, session: AsyncSession, current_user: Optional[User] = None):
        super().__init__(Faculty, session, current_user)

    @cache_result(ttl=1800)  # Cache for 30 minutes
    async def get_all_faculties(self) -> List[FacultyRead]:
        """Get all faculties (cached for performance)"""
        try:
            result = await self.session.execute(select(Faculty).order_by(Faculty.name))
            faculties = result.scalars().all()

            return [FacultyRead.from_orm(faculty) for faculty in faculties]

        except Exception as e:
            raise ValidationException(f"Failed to retrieve faculties: {str(e)}")

    async def get_faculty_by_id(self, faculty_id: int) -> FacultyRead:
        """Get faculty by ID"""
        try:
            faculty = await self.session.get(Faculty, faculty_id)
            if not faculty:
                raise NotFoundError("Faculty not found")

            return FacultyRead.from_orm(faculty)

        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationException(f"Failed to retrieve faculty: {str(e)}")

    async def create_faculty(self, data: FacultyCreate) -> FacultyRead:
        """Create new faculty (admin only)"""
        if not self.current_user or self.current_user.role_id != 3:  # Admin only
            raise ValidationException("Only administrators can create faculties")

        try:
            # Check if faculty name already exists
            existing = await self.session.execute(
                select(Faculty).where(Faculty.name == data.name)
            )
            if existing.scalar_one_or_none():
                raise ValidationException("Faculty name already exists")

            faculty = Faculty(**data.model_dump())
            self.session.add(faculty)
            await self.session.commit()
            await self.session.refresh(faculty)

            return FacultyRead.from_orm(faculty)

        except ValidationException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise ValidationException(f"Failed to create faculty: {str(e)}")

    async def update_faculty(self, faculty_id: int, data: FacultyUpdate) -> FacultyRead:
        """Update faculty (admin only)"""
        if not self.current_user or self.current_user.role_id != 3:  # Admin only
            raise ValidationException("Only administrators can update faculties")

        try:
            faculty = await self.session.get(Faculty, faculty_id)
            if not faculty:
                raise NotFoundError("Faculty not found")

            # Check name uniqueness if name is being updated
            if data.name and data.name != faculty.name:
                existing = await self.session.execute(
                    select(Faculty).where(Faculty.name == data.name)
                )
                if existing.scalar_one_or_none():
                    raise ValidationException("Faculty name already exists")

            # Apply updates
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(faculty, field, value)

            await self.session.commit()
            await self.session.refresh(faculty)

            return FacultyRead.from_orm(faculty)

        except (NotFoundError, ValidationException):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise ValidationException(f"Failed to update faculty: {str(e)}")

    async def delete_faculty(self, faculty_id: int) -> dict:
        """Delete faculty (admin only) - with user check"""
        if not self.current_user or self.current_user.role_id != 3:  # Admin only
            raise ValidationException("Only administrators can delete faculties")

        try:
            faculty = await self.session.get(Faculty, faculty_id)
            if not faculty:
                raise NotFoundError("Faculty not found")

            # Check if faculty has associated users
            users_result = await self.session.execute(
                select(User).where(User.faculty_id == faculty_id).limit(1)
            )
            if users_result.scalar_one_or_none():
                raise ValidationException(
                    "Cannot delete faculty with associated users. "
                    "Please reassign users to other faculties first."
                )

            await self.session.delete(faculty)
            await self.session.commit()

            return {"message": "Faculty deleted successfully"}

        except (NotFoundError, ValidationException):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise ValidationException(f"Failed to delete faculty: {str(e)}")

    async def get_faculty_statistics(self, faculty_id: int) -> dict:
        """Get faculty statistics (user count, etc.)"""
        try:
            faculty = await self.session.get(Faculty, faculty_id)
            if not faculty:
                raise NotFoundError("Faculty not found")

            # Count users by role
            from sqlalchemy import func

            result = await self.session.execute(
                select(User.role_id, func.count(User.id).label("count"))
                .where(User.faculty_id == faculty_id)
                .group_by(User.role_id)
            )

            role_counts = {row.role_id: row.count for row in result}

            # Total users
            total_users = sum(role_counts.values())

            return {
                "faculty_id": faculty_id,
                "faculty_name": faculty.name,
                "total_users": total_users,
                "students_count": role_counts.get(2, 0),  # Role ID 2 = Student
                "teachers_count": role_counts.get(1, 0),  # Role ID 1 = Teacher
                "admins_count": role_counts.get(3, 0),  # Role ID 3 = Admin
            }

        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationException(f"Failed to get faculty statistics: {str(e)}")

    @cache_result(ttl=3600)  # Cache for 1 hour
    async def get_faculties_with_stats(self) -> List[dict]:
        """Get all faculties with user statistics"""
        try:
            faculties = await self.get_all_faculties()

            result = []
            for faculty in faculties:
                stats = await self.get_faculty_statistics(faculty.id)
                result.append({**faculty.model_dump(), "statistics": stats})

            return result

        except Exception as e:
            raise ValidationException(
                f"Failed to get faculties with statistics: {str(e)}"
            )
