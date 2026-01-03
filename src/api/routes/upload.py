"""
File Upload API Routes

Handles secure file upload with validation
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from src.core.config import settings
from src.core.exceptions import (
    FileSizeExceedException,
    FileUploadException,
    InvalidFileTypeException,
)
from src.core.logging import get_logger
from src.core.redis_client import redis_client
from src.models.schemas import FileUploadResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/upload", tags=["File Upload"])


@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload CSV file for analysis",
    description="Upload a CSV file to be analyzed. File is validated and stored securely.",
)
async def upload_file(
    file: UploadFile = File(..., description="CSV file to upload"),
    description: Optional[str] = Form(None, description="Optional file description"),
) -> FileUploadResponse:
    """
    Upload a CSV file for EDA analysis

    Args:
        file: CSV file to upload
        description: Optional description of the file

    Returns:
        FileUploadResponse with file metadata

    Raises:
        HTTPException: If upload validation fails
    """
    logger.info(f"Processing file upload: {file.filename}")

    try:
        # Validate file type
        if not file.filename:
            raise FileUploadException("Filename is required")

        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = settings.file_upload.allowed_extensions

        if file_ext not in allowed_extensions:
            raise InvalidFileTypeException(file_ext, allowed_extensions)

        # Generate unique file ID
        file_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{file_id}_{timestamp}{file_ext}"

        # Determine upload path
        upload_path = settings.file_upload.upload_dir / safe_filename

        # Read file content and check size
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)

        if size_mb > settings.file_upload.max_upload_size_mb:
            raise FileSizeExceedException(
                size_mb, settings.file_upload.max_upload_size_mb
            )

        # Save file
        with open(upload_path, "wb") as f:
            f.write(content)

        # Store file metadata in Redis
        file_metadata = {
            "file_id": file_id,
            "original_filename": file.filename,
            "stored_filename": safe_filename,
            "file_path": str(upload_path),
            "size_bytes": len(content),
            "size_mb": round(size_mb, 2),
            "description": description or "",
            "upload_timestamp": datetime.utcnow().isoformat(),
            "content_type": file.content_type or "text/csv",
        }

        redis_key = f"eda:file:{file_id}"
        redis_client.set_hash(redis_key, file_metadata)
        redis_client.expire(redis_key, 604800)  # 7 days

        logger.info(
            f"File uploaded successfully: {file_id} ({size_mb:.2f}MB)"
        )

        return FileUploadResponse(
            success=True,
            message="File uploaded successfully",
            file_id=file_id,
            filename=file.filename,
            size_bytes=len(content),
            upload_timestamp=datetime.utcnow(),
        )

    except (FileUploadException, FileSizeExceedException, InvalidFileTypeException) as e:
        logger.warning(f"File upload validation failed: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        logger.error(f"File upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"message": f"File upload failed: {str(e)}"}},
        )


@router.get(
    "/{file_id}",
    summary="Get file metadata",
    description="Retrieve metadata for an uploaded file",
)
async def get_file_metadata(file_id: str):
    """
    Get metadata for an uploaded file

    Args:
        file_id: File identifier

    Returns:
        File metadata

    Raises:
        HTTPException: If file not found
    """
    logger.debug(f"Retrieving metadata for file: {file_id}")

    try:
        redis_key = f"eda:file:{file_id}"
        metadata = redis_client.get_hash(redis_key)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": f"File {file_id} not found"}},
            )

        return {
            "success": True,
            "file_metadata": metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve file metadata: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"message": f"Failed to retrieve metadata: {str(e)}"}},
        )


@router.delete(
    "/{file_id}",
    summary="Delete uploaded file",
    description="Delete an uploaded file and its metadata",
)
async def delete_file(file_id: str):
    """
    Delete an uploaded file

    Args:
        file_id: File identifier

    Returns:
        Success response

    Raises:
        HTTPException: If file not found or deletion fails
    """
    logger.info(f"Deleting file: {file_id}")

    try:
        redis_key = f"eda:file:{file_id}"
        metadata = redis_client.get_hash(redis_key)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"message": f"File {file_id} not found"}},
            )

        # Delete physical file
        file_path = Path(metadata["file_path"])
        if file_path.exists():
            file_path.unlink()

        # Delete metadata from Redis
        redis_client.delete(redis_key)

        logger.info(f"File deleted successfully: {file_id}")

        return {
            "success": True,
            "message": f"File {file_id} deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"message": f"File deletion failed: {str(e)}"}},
        )
