"""Custom exceptions for AI Study Architect application"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception for all API exceptions"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


# Authentication Exceptions
class AuthenticationError(BaseAPIException):
    """Base class for authentication errors"""
    def __init__(self, detail: str = "Authentication failed", error_code: str = "AUTH_ERROR"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
            error_code=error_code
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when username/password is incorrect"""
    def __init__(self):
        super().__init__(
            detail="Incorrect username/email or password",
            error_code="INVALID_CREDENTIALS"
        )


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired"""
    def __init__(self):
        super().__init__(
            detail="Token has expired",
            error_code="TOKEN_EXPIRED"
        )


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid"""
    def __init__(self):
        super().__init__(
            detail="Invalid token",
            error_code="INVALID_TOKEN"
        )


class UnauthorizedError(BaseAPIException):
    """Raised when user is not authorized to perform an action"""
    def __init__(self, detail: str = "Unauthorized", error_code: str = "UNAUTHORIZED"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code
        )


# User Management Exceptions
class UserAlreadyExistsError(BaseAPIException):
    """Raised when trying to create a user that already exists"""
    def __init__(self, field: str = "email"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with this {field} already exists",
            error_code="USER_ALREADY_EXISTS"
        )


class UserNotFoundError(BaseAPIException):
    """Raised when user is not found"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            error_code="USER_NOT_FOUND"
        )


class InactiveUserError(BaseAPIException):
    """Raised when inactive user tries to perform actions"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
            error_code="INACTIVE_USER"
        )


# Content Management Exceptions
class ContentNotFoundError(BaseAPIException):
    """Raised when content is not found"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
            error_code="CONTENT_NOT_FOUND"
        )


class ContentAlreadyExistsError(BaseAPIException):
    """Raised when duplicate content is uploaded"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="This file has already been uploaded",
            error_code="CONTENT_ALREADY_EXISTS"
        )


class InvalidFileTypeError(BaseAPIException):
    """Raised when uploaded file type is not allowed"""
    def __init__(self, mime_type: str):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type {mime_type} is not allowed",
            error_code="INVALID_FILE_TYPE"
        )


class FileTooLargeError(BaseAPIException):
    """Raised when uploaded file exceeds size limit"""
    def __init__(self, max_size: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {max_size} bytes",
            error_code="FILE_TOO_LARGE"
        )


class FileUploadError(BaseAPIException):
    """Raised when file upload fails"""
    def __init__(self, detail: str = "Failed to upload file"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="FILE_UPLOAD_ERROR"
        )


class ContentProcessingError(BaseAPIException):
    """Raised when content processing fails"""
    def __init__(self, detail: str = "Failed to process content"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="CONTENT_PROCESSING_ERROR"
        )


# AI Agent Exceptions
class AgentNotAvailableError(BaseAPIException):
    """Raised when AI agent is not available"""
    def __init__(self, agent_name: str = "Agent"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{agent_name} is currently unavailable",
            error_code="AGENT_NOT_AVAILABLE"
        )


class AgentProcessingError(BaseAPIException):
    """Raised when agent fails to process request"""
    def __init__(self, detail: str = "Failed to process request"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="AGENT_PROCESSING_ERROR"
        )



# Database Exceptions
class DatabaseError(BaseAPIException):
    """Base class for database errors"""
    def __init__(self, detail: str = "Database error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR"
        )


class DatabaseConnectionError(DatabaseError):
    """Raised when cannot connect to database"""
    def __init__(self):
        super().__init__(detail="Cannot connect to database")


# Validation Exceptions
class ValidationError(BaseAPIException):
    """Raised when input validation fails"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )


# Permission Exceptions
class PermissionDeniedError(BaseAPIException):
    """Raised when user lacks required permissions"""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED"
        )


class ResourceOwnershipError(PermissionDeniedError):
    """Raised when user tries to access resource they don't own"""
    def __init__(self, resource_type: str = "resource"):
        super().__init__(detail=f"You don't have permission to access this {resource_type}")


# Security Exceptions
class CSRFError(BaseAPIException):
    """Raised when CSRF validation fails"""
    def __init__(self, detail: str = "CSRF validation failed"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="CSRF_VALIDATION_FAILED"
        )