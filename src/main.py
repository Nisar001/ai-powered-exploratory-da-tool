"""
Main FastAPI Application

Production-grade FastAPI application with all routes, middleware,
and exception handlers configured.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.exception_handlers import (
    eda_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from src.api.middleware import CORSCustomMiddleware, RequestLoggingMiddleware
from src.api.routes import analysis, health, upload
from src.core.api_key_validator import validate_llm_apis
from src.core.config import settings
from src.core.exceptions import EDABaseException
from src.core.logging import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info(f"Starting {settings.app.app_name} v{settings.app.app_version}")
    logger.info(f"Environment: {settings.app.app_env}")
    logger.info(f"Debug mode: {settings.app.debug}")

    # Ensure directories exist
    settings.file_upload.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.file_upload.results_dir.mkdir(parents=True, exist_ok=True)
    settings.file_upload.temp_dir.mkdir(parents=True, exist_ok=True)

    # Validate LLM API keys
    await validate_llm_apis()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application")
    # Cleanup code here if needed


# Create FastAPI application
app = FastAPI(
    title=settings.api.api_title,
    description=settings.api.api_description,
    version=settings.app.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.api.api_v1_prefix}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
if settings.security.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CORSCustomMiddleware)

# Register exception handlers
app.add_exception_handler(EDABaseException, eda_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router, prefix="")
app.include_router(
    upload.router,
    prefix=settings.api.api_v1_prefix,
)
app.include_router(
    analysis.router,
    prefix=settings.api.api_v1_prefix,
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint redirect to API info"""
    return {
        "name": settings.app.app_name,
        "version": settings.app.app_version,
        "environment": settings.app.app_env,
        "docs_url": "/docs",
        "api_v1": settings.api.api_v1_prefix,
    }


# Development server runner
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        workers=1 if settings.server.reload else settings.server.workers,
        log_level=settings.app.log_level.lower(),
    )
