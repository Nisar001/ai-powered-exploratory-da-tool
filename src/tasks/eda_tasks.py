"""
Background Tasks

Celery tasks for async EDA processing
"""

import json
from pathlib import Path

from src.core.celery_app import celery_app
from src.core.logging import get_logger
from src.core.redis_client import redis_client
from src.models.schemas import AnalysisType, JobStatus
from src.services.eda_orchestrator import EDAOrchestrator

logger = get_logger(__name__)


@celery_app.task(bind=True, name="tasks.process_eda_analysis")
def process_eda_analysis(
    self,
    job_id: str,
    file_path: str,
    analysis_types: list = None,
    generate_insights: bool = True,
    generate_visualizations: bool = True,
):
    """
    Background task for processing EDA analysis

    Args:
        job_id: Unique job identifier
        file_path: Path to CSV file
        analysis_types: List of analysis types to perform
        generate_insights: Whether to generate AI insights
        generate_visualizations: Whether to generate visualizations

    Returns:
        Analysis result as dictionary
    """
    logger.info(f"Starting background EDA analysis for job {job_id}")

    try:
        # Update job status to PROCESSING
        _update_job_status(job_id, JobStatus.PROCESSING, progress=10)

        # Parse analysis types
        if analysis_types is None:
            analysis_types = [AnalysisType.ALL]
        else:
            analysis_types = [AnalysisType(at) for at in analysis_types]

        # Initialize orchestrator
        orchestrator = EDAOrchestrator(job_id=job_id, file_path=Path(file_path))

        # Update progress
        _update_job_status(job_id, JobStatus.PROCESSING, progress=20)

        # Execute analysis
        result = orchestrator.execute_full_analysis(
            analysis_types=analysis_types,
            generate_insights=generate_insights,
            generate_visualizations=generate_visualizations,
        )

        # Update progress
        _update_job_status(job_id, JobStatus.PROCESSING, progress=90)

        # Convert result to dict
        result_dict = result.model_dump()

        # Store result in Redis
        result_key = f"eda:result:{job_id}"
        redis_client.set(result_key, result_dict, expire=86400)  # 24 hours

        # Update job status to COMPLETED
        _update_job_status(job_id, JobStatus.COMPLETED, progress=100, result_available=True)

        # Cleanup
        orchestrator.cleanup()

        logger.info(f"EDA analysis completed successfully for job {job_id}")

        return result_dict

    except Exception as e:
        logger.error(
            f"EDA analysis failed for job {job_id}: {str(e)}", exc_info=True
        )

        # Update job status to FAILED
        _update_job_status(
            job_id, JobStatus.FAILED, progress=0, error_message=str(e)
        )

        raise


def _update_job_status(
    job_id: str,
    status: JobStatus,
    progress: float = 0.0,
    error_message: str = None,
    result_available: bool = False,
):
    """
    Update job status in Redis

    Args:
        job_id: Job identifier
        status: New job status
        progress: Progress percentage
        error_message: Error message if failed
        result_available: Whether result is available
    """
    from datetime import datetime

    job_key = f"eda:job:{job_id}"

    # Get existing job data
    job_data = redis_client.get_hash(job_key) or {}

    # Update fields
    job_data["status"] = status.value
    job_data["progress"] = progress

    if status == JobStatus.PROCESSING and "started_at" not in job_data:
        job_data["started_at"] = datetime.utcnow().isoformat()

    if status == JobStatus.COMPLETED:
        job_data["completed_at"] = datetime.utcnow().isoformat()
        job_data["result_available"] = result_available

    if status == JobStatus.FAILED:
        job_data["completed_at"] = datetime.utcnow().isoformat()
        job_data["error_message"] = error_message
        job_data["result_available"] = False

    # Store updated job data
    redis_client.set_hash(job_key, job_data)

    # Set expiration (7 days)
    redis_client.expire(job_key, 604800)

    logger.debug(f"Updated job {job_id} status to {status.value} (progress: {progress}%)")


@celery_app.task(name="tasks.cleanup_old_jobs")
def cleanup_old_jobs(days_to_keep: int = 7):
    """
    Periodic task to clean up old job data and files
    
    Args:
        days_to_keep: Number of days to retain completed jobs (default: 7)
    """
    from datetime import datetime, timedelta
    from pathlib import Path
    
    logger.info(f"Running cleanup task for jobs older than {days_to_keep} days")

    try:
        from src.core.config import settings
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Track cleanup statistics
        stats = {
            "jobs_deleted": 0,
            "results_deleted": 0,
            "files_deleted": 0,
            "errors": 0,
        }
        
        # Scan Redis for job keys
        try:
            # Note: In production, use SCAN instead of KEYS for better performance
            job_keys = redis_client.client.keys("eda:job:*")
            
            for job_key in job_keys:
                try:
                    job_data = redis_client.get_hash(job_key.decode() if isinstance(job_key, bytes) else job_key)
                    
                    if not job_data:
                        continue
                    
                    # Check if job is completed and older than cutoff
                    completed_at_str = job_data.get("completed_at")
                    if completed_at_str:
                        completed_at = datetime.fromisoformat(completed_at_str)
                        
                        if completed_at < cutoff_date:
                            job_id = job_data.get("job_id")
                            file_id = job_data.get("file_id")
                            
                            # Delete job metadata
                            redis_client.delete(job_key.decode() if isinstance(job_key, bytes) else job_key)
                            stats["jobs_deleted"] += 1
                            
                            # Delete result data
                            result_key = f"eda:result:{job_id}"
                            if redis_client.exists(result_key):
                                redis_client.delete(result_key)
                                stats["results_deleted"] += 1
                            
                            # Delete associated uploaded file
                            if file_id:
                                file_key = f"eda:file:{file_id}"
                                file_metadata = redis_client.get_hash(file_key)
                                
                                if file_metadata and "file_path" in file_metadata:
                                    file_path = Path(file_metadata["file_path"])
                                    if file_path.exists():
                                        file_path.unlink()
                                        stats["files_deleted"] += 1
                                
                                redis_client.delete(file_key)
                            
                            logger.debug(f"Cleaned up old job: {job_id}")
                
                except Exception as e:
                    logger.warning(f"Failed to cleanup job {job_key}: {str(e)}")
                    stats["errors"] += 1
                    continue
        
        except Exception as e:
            logger.error(f"Failed to scan Redis keys: {str(e)}")
            stats["errors"] += 1
        
        # Cleanup old visualization files
        try:
            results_dir = settings.file_upload.results_dir
            if results_dir.exists():
                cutoff_timestamp = cutoff_date.timestamp()
                
                for file_path in results_dir.glob("*"):
                    if file_path.is_file():
                        if file_path.stat().st_mtime < cutoff_timestamp:
                            file_path.unlink()
                            stats["files_deleted"] += 1
        
        except Exception as e:
            logger.error(f"Failed to cleanup visualization files: {str(e)}")
            stats["errors"] += 1
        
        logger.info(
            f"Cleanup task completed: {stats['jobs_deleted']} jobs, "
            f"{stats['results_deleted']} results, {stats['files_deleted']} files deleted "
            f"({stats['errors']} errors)"
        )
        
        return stats

    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}", exc_info=True)
        raise
