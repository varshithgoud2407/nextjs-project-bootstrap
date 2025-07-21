from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenHeartException(Exception):
    """Base exception for OpenHeart app"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AIServiceException(OpenHeartException):
    """Exception for AI service errors"""
    def __init__(self, message: str = "AI service temporarily unavailable"):
        super().__init__(message, 503)

class VoiceProcessingException(OpenHeartException):
    """Exception for voice processing errors"""
    def __init__(self, message: str = "Voice processing failed"):
        super().__init__(message, 422)

class PaymentException(OpenHeartException):
    """Exception for payment processing errors"""
    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(message, 402)

class MeetingException(OpenHeartException):
    """Exception for meeting integration errors"""
    def __init__(self, message: str = "Meeting service unavailable"):
        super().__init__(message, 503)

async def openheart_exception_handler(request: Request, exc: OpenHeartException):
    """Handle custom OpenHeart exceptions"""
    logger.error(f"OpenHeart Exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": "openheart_error"}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.error(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()}
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )
