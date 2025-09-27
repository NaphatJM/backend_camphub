from typing import TypeVar, Generic, Type, List, Optional, Any, Dict
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from pydantic import BaseModel

from app.models.user_model import User
from app.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    DatabaseError,
)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ReadSchemaType = TypeVar("ReadSchemaType", bound=BaseModel)


class BaseService(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, ReadSchemaType], ABC
):
    """Base service class with common CRUD operations"""

    def __init__(
        self,
        model: Type[ModelType],
        session: AsyncSession,
        current_user: Optional[User] = None,
    ):
        self.model = model
        self.session = session
        self.current_user = current_user

    @property
    @abstractmethod
    def resource_name(self) -> str:
        """Name of the resource for error messages"""
        pass

    def check_permission(self, action: str, resource_id: Optional[Any] = None) -> None:
        """Override this method to implement permission checking"""
        pass

    async def get_all(self, **filters) -> List[ReadSchemaType]:
        """Get all records with optional filters"""
        try:
            stmt = select(self.model)

            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if value is not None and hasattr(self.model, field):
                        stmt = stmt.where(getattr(self.model, field) == value)

            result = await self.session.execute(stmt)
            records = result.scalars().all()
            return [self._to_read_schema(record) for record in records]
        except Exception as e:
            raise DatabaseError(
                message=f"Failed to retrieve {self.resource_name} list",
                operation="get_all",
            ) from e

    async def get_by_id(self, record_id: Any) -> ReadSchemaType:
        """Get record by ID"""
        try:
            record = await self.session.get(self.model, record_id)
            if not record:
                raise NotFoundError(resource=self.resource_name, resource_id=record_id)

            return self._to_read_schema(record)
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(
                message=f"Failed to retrieve {self.resource_name}",
                operation="get_by_id",
            ) from e

    async def create(self, create_data: CreateSchemaType) -> ReadSchemaType:
        """Create new record"""
        self.check_permission("create")

        try:
            # Convert schema to dict and create model instance
            data_dict = (
                create_data.model_dump()
                if hasattr(create_data, "model_dump")
                else create_data.dict()
            )

            # Add audit fields if model supports it
            if hasattr(self.model, "created_by") and self.current_user:
                data_dict["created_by"] = self.current_user.id
            if hasattr(self.model, "updated_by") and self.current_user:
                data_dict["updated_by"] = self.current_user.id

            record = self.model(**data_dict)
            self.session.add(record)
            await self.session.commit()
            await self.session.refresh(record)

            return self._to_read_schema(record)
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message=f"Failed to create {self.resource_name}", operation="create"
            ) from e

    async def update(
        self, record_id: Any, update_data: UpdateSchemaType
    ) -> ReadSchemaType:
        """Update existing record"""
        self.check_permission("update", record_id)

        try:
            # Check if record exists
            record = await self.session.get(self.model, record_id)
            if not record:
                raise NotFoundError(resource=self.resource_name, resource_id=record_id)

            # Convert schema to dict and update fields
            data_dict = (
                update_data.model_dump(exclude_unset=True)
                if hasattr(update_data, "model_dump")
                else update_data.dict(exclude_unset=True)
            )

            # Add audit fields if model supports it
            if hasattr(self.model, "updated_by") and self.current_user:
                data_dict["updated_by"] = self.current_user.id

            for field, value in data_dict.items():
                if hasattr(record, field):
                    setattr(record, field, value)

            await self.session.commit()
            await self.session.refresh(record)

            return self._to_read_schema(record)
        except NotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message=f"Failed to update {self.resource_name}", operation="update"
            ) from e

    async def delete(self, record_id: Any) -> Dict[str, Any]:
        """Delete record by ID"""
        self.check_permission("delete", record_id)

        try:
            record = await self.session.get(self.model, record_id)
            if not record:
                raise NotFoundError(resource=self.resource_name, resource_id=record_id)

            await self.session.delete(record)
            await self.session.commit()

            return {
                "success": True,
                "message": f"{self.resource_name} deleted successfully",
            }
        except NotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(
                message=f"Failed to delete {self.resource_name}", operation="delete"
            ) from e

    async def exists(self, record_id: Any) -> bool:
        """Check if record exists"""
        try:
            record = await self.session.get(self.model, record_id)
            return record is not None
        except Exception as e:
            raise DatabaseError(
                message=f"Failed to check {self.resource_name} existence",
                operation="exists",
            ) from e

    def _to_read_schema(self, record: ModelType) -> ReadSchemaType:
        """Convert model instance to read schema. Override if needed."""
        # Default implementation tries to use from_orm
        try:
            return ReadSchemaType.from_orm(record)
        except AttributeError:
            # Fallback to model_validate if from_orm doesn't exist
            return ReadSchemaType.model_validate(record)

    def check_admin_permission(self) -> None:
        """Check if current user is admin"""
        if not self.current_user or self.current_user.role_id not in [1, 3]:
            raise PermissionDeniedError(
                action="admin operation", resource=self.resource_name
            )
