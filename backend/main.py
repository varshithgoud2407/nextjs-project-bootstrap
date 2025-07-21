from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from config import settings
from database import engine, Base
from exceptions import (
    OpenHeartException,
    openheart_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler
)
from routes import auth, users, ai_sessions, payments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="OpenHeart AI Companion API",
    description="AI-powered emotional support companion with multilingual voice conversations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(OpenHeartException, openheart_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(ai_sessions.router, prefix="/ai", tags=["AI Sessions"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to OpenHeart AI Companion API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "database": "connected",
            "ai_service": "available" if settings.OPENAI_API_KEY else "not_configured",
            "payment_service": "available" if settings.STRIPE_API_KEY else "not_configured"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
