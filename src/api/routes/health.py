"""
Health Check and Monitoring Routes
"""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, status

from src.core.config import settings
from src.core.logging import get_logger
from src.core.redis_client import redis_client
from src.models.schemas import HealthStatus

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Health check",
    description="Check the health status of the API and its dependencies",
)
async def health_check() -> HealthStatus:
    """
    Comprehensive health check endpoint

    Returns:
        HealthStatus with service availability
    """
    services = {}
    all_healthy = True

    # Check Redis
    try:
        redis_client.client.ping()
        services["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        services["redis"] = False
        all_healthy = False

    # Check file system
    try:
        settings.file_upload.upload_dir.exists()
        services["file_system"] = True
    except Exception as e:
        logger.error(f"File system health check failed: {str(e)}")
        services["file_system"] = False
        all_healthy = False

    # Determine overall status
    overall_status = "healthy" if all_healthy else "degraded"

    return HealthStatus(
        status=overall_status,
        version=settings.app.app_version,
        timestamp=datetime.utcnow(),
        services=services,
        details={
            "environment": settings.app.app_env,
            "debug_mode": settings.app.debug,
        },
    )


@router.get(
    "/",
    summary="Root endpoint",
    description="API root with basic information",
)
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app.app_name,
        "version": settings.app.app_version,
        "environment": settings.app.app_env,
        "docs_url": "/docs",
        "health_url": "/health",
    }


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Prometheus-compatible metrics endpoint (if enabled)",
)
async def metrics():
    """
    Metrics endpoint for monitoring

    Returns:
        Basic metrics (would be enhanced with prometheus_client)
    """
    if not settings.monitoring.enable_metrics:
        return {"message": "Metrics collection is disabled"}

    # Basic metrics
    return {
        "app_info": {
            "name": settings.app.app_name,
            "version": settings.app.app_version,
            "environment": settings.app.app_env,
        },
        "timestamp": datetime.utcnow().isoformat(),
        # Additional metrics would be added here
    }
