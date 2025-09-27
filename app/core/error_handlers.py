from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from datetime import datetime
import traceback

from .exceptions import BaseCustomException

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format"""

    @staticmethod
    def format_error(
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Format error response in standardized way"""
        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "status_code": status_code,
                "timestamp": datetime.now().isoformat(),
                "path": path,
                "details": details or {},
            },
        }


async def custom_exception_handler(
    request: Request, exc: BaseCustomException
) -> JSONResponse:
    """Handler for custom exceptions"""
    logger.warning(
        f"Custom exception {exc.error_code}: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.format_error(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=str(request.url.path),
        ),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handler for HTTP exceptions"""
    logger.warning(
        f"HTTP exception {exc.status_code}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.format_error(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=str(exc.detail),
            path=str(request.url.path),
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handler for request validation exceptions"""
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "errors": exc.errors(),
            "path": str(request.url.path),
        },
    )

    # Format validation errors for better readability
    validation_errors = []
    for error in exc.errors():
        field = (
            ".".join(str(loc) for loc in error["loc"][1:])
            if len(error["loc"]) > 1
            else str(error["loc"][0])
        )
        validation_errors.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"],
                "value": error.get("input", "N/A"),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse.format_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"validation_errors": validation_errors},
            path=str(request.url.path),
        ),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for general unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
            "path": str(request.url.path),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.format_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            path=str(request.url.path),
        ),
    )
