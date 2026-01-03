"""
Analysis API Routes

Handles EDA analysis triggering and management
"""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from src.core.config import settings
from src.core.logging import get_logger
from src.core.redis_client import redis_client
from src.models.schemas import (
    AnalysisRequest,
    JobResponse,
    JobStatus,
    JobStatusResponse,
    AnalysisReportResponse,
)
from src.tasks.eda_tasks import process_eda_analysis

logger = get_logger(__name__)

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger EDA analysis",
    description="Start background EDA analysis for an uploaded file",
)
async def trigger_analysis(request: AnalysisRequest) -> JobResponse:
    """
    Trigger EDA analysis for an uploaded file

    Args:
        request: Analysis request with file_id and options

    Returns:
        JobResponse with job_id for tracking

    Raises:
        HTTPException: If file not found or analysis cannot be started
    """
    logger.info(f"Triggering analysis for file: {request.file_id}")

    try:
        # Verify file exists
        file_key = f"eda:file:{request.file_id}"
        file_metadata = redis_client.get_hash(file_key)

        if not file_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {"message": f"File {request.file_id} not found"}
                },
            )

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Create job metadata
        job_data = {
            "job_id": job_id,
            "file_id": request.file_id,
            "status": JobStatus.PENDING.value,
            "progress": 0.0,
            "created_at": datetime.utcnow().isoformat(),
            "analysis_types": [at.value for at in request.analysis_types],
            "generate_insights": request.generate_insights,
            "generate_visualizations": request.generate_visualizations,
            "result_available": False,
        }

        # Store job metadata in Redis
        job_key = f"eda:job:{job_id}"
        redis_client.set_hash(job_key, job_data)
        redis_client.expire(job_key, 604800)  # 7 days

        # Trigger background task
        if settings.performance.background_tasks_enabled:
            process_eda_analysis.delay(
                job_id=job_id,
                file_path=file_metadata["file_path"],
                analysis_types=[at.value for at in request.analysis_types],
                generate_insights=request.generate_insights,
                generate_visualizations=request.generate_visualizations,
            )

            logger.info(f"Background analysis task queued for job: {job_id}")
        else:
            # Synchronous execution (for testing)
            logger.warning("Background tasks disabled, running synchronously")
            process_eda_analysis(
                job_id=job_id,
                file_path=file_metadata["file_path"],
                analysis_types=[at.value for at in request.analysis_types],
                generate_insights=request.generate_insights,
                generate_visualizations=request.generate_visualizations,
            )

        return JobResponse(
            success=True,
            message="Analysis job created successfully",
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"message": f"Failed to trigger analysis: {str(e)}"}},
        )


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Check the status of an analysis job",
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of an analysis job

    Args:
        job_id: Job identifier

    Returns:
        JobStatusResponse with current status and progress

    Raises:
        HTTPException: If job not found
    """
    logger.debug(f"Checking status for job: {job_id}")

    try:
        job_key = f"eda:job:{job_id}"
        job_data = redis_client.get_hash(job_key)

        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": f"Job {job_id} not found"}},
            )

        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus(job_data["status"]),
            progress=float(job_data.get("progress", 0)),
            created_at=datetime.fromisoformat(job_data["created_at"]),
            started_at=(
                datetime.fromisoformat(job_data["started_at"])
                if "started_at" in job_data
                else None
            ),
            completed_at=(
                datetime.fromisoformat(job_data["completed_at"])
                if "completed_at" in job_data
                else None
            ),
            error_message=job_data.get("error_message"),
            result_available=job_data.get("result_available", False),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"message": f"Failed to get job status: {str(e)}"}},
        )


@router.get(
    "/result/{job_id}",
    response_model=AnalysisReportResponse,
    summary="Get analysis results",
    description="Retrieve the complete analysis results for a completed job",
)
async def get_analysis_result(job_id: str) -> AnalysisReportResponse:
    """
    Get analysis results for a completed job

    Args:
        job_id: Job identifier

    Returns:
        AnalysisReportResponse with complete results

    Raises:
        HTTPException: If job not found or not completed
    """
    logger.info(f"Retrieving results for job: {job_id}")

    try:
        # Check job status
        job_key = f"eda:job:{job_id}"
        job_data = redis_client.get_hash(job_key)

        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": f"Job {job_id} not found"}},
            )

        job_status = JobStatus(job_data["status"])

        if job_status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "message": f"Job {job_id} is not completed. Current status: {job_status.value}"
                    }
                },
            )

        # Retrieve result from Redis
        result_key = f"eda:result:{job_id}"
        result_data = redis_client.get(result_key)

        if not result_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "message": f"Results for job {job_id} not found or expired"
                    }
                },
            )

        logger.info(f"Results retrieved successfully for job: {job_id}")

        from src.models.schemas import AnalysisResult

        return AnalysisReportResponse(
            success=True,
            message="Analysis results retrieved successfully",
            result=AnalysisResult(**result_data),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve analysis results: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "message": f"Failed to retrieve analysis results: {str(e)}"
                }
            },
        )


@router.delete(
    "/{job_id}",
    summary="Cancel or delete a job",
    description="Cancel a running job or delete a completed job and its results",
)
async def delete_job(job_id: str):
    """
    Cancel or delete an analysis job

    Args:
        job_id: Job identifier

    Returns:
        Success response

    Raises:
        HTTPException: If job not found
    """
    logger.info(f"Deleting job: {job_id}")

    try:
        job_key = f"eda:job:{job_id}"
        job_data = redis_client.get_hash(job_key)

        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": f"Job {job_id} not found"}},
            )

        # Delete job metadata
        redis_client.delete(job_key)

        # Delete results if they exist
        result_key = f"eda:result:{job_id}"
        redis_client.delete(result_key)

        logger.info(f"Job deleted successfully: {job_id}")

        return {
            "success": True,
            "message": f"Job {job_id} deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"message": f"Failed to delete job: {str(e)}"}},
        )
