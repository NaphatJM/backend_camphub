from typing import Optional, Any, Dict
from fastapi import HTTPException, status


class BaseCustomException(Exception):
    """Base exception class with standardized error format"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(BaseCustomException):
    """Validation error exception"""

    def __init__(
        self, message: str, field: Optional[str] = None, value: Optional[Any] = None
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value

        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(BaseCustomException):
    """Resource not found exception"""

    def __init__(self, resource: str, resource_id: Optional[Any] = None):
        message = f"{resource} not found"
        details = {"resource": resource}
        if resource_id is not None:
            message += f" with id: {resource_id}"
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
        )


class PermissionDeniedError(BaseCustomException):
    """Permission denied exception"""

    def __init__(self, action: str, resource: Optional[str] = None):
        message = f"Permission denied for action: {action}"
        details = {"action": action}
        if resource:
            message += f" on resource: {resource}"
            details["resource"] = resource

        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PERMISSION_DENIED",
            details=details,
        )


class ConflictError(BaseCustomException):
    """Resource conflict exception"""

    def __init__(self, resource: str, message: Optional[str] = None):
        default_message = f"{resource} already exists or conflicts with existing data"

        super().__init__(
            message=message or default_message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            details={"resource": resource},
        )


class BusinessLogicError(BaseCustomException):
    """Business logic error exception"""

    def __init__(self, message: str, operation: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details,
        )


class DatabaseError(BaseCustomException):
    """Database operation error exception"""

    def __init__(self, message: str, operation: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details,
        )


class ExternalServiceError(BaseCustomException):
    """External service error exception"""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service error from {service}: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "original_message": message},
        )
