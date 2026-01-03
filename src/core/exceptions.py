"""
Custom Exception Classes

Centralized exception hierarchy for the EDA platform.
All exceptions are structured and carry meaningful context.
"""

from typing import Any, Dict, Optional


class EDABaseException(Exception):
    """Base exception for all EDA platform errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": {
                "message": self.message,
                "code": self.error_code,
                "details": self.details,
            }
        }


# File Upload Exceptions
class FileUploadException(EDABaseException):
    """Base exception for file upload errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            status_code=400,
            details=details,
        )


class FileSizeExceedException(FileUploadException):
    """Exception raised when file size exceeds limit"""

    def __init__(self, size_mb: float, max_size_mb: float):
        super().__init__(
            message=f"File size {size_mb:.2f}MB exceeds maximum allowed size {max_size_mb}MB",
            details={"size_mb": size_mb, "max_size_mb": max_size_mb},
        )


class InvalidFileTypeException(FileUploadException):
    """Exception raised when file type is not allowed"""

    def __init__(self, file_type: str, allowed_types: list):
        super().__init__(
            message=f"File type '{file_type}' not allowed. Allowed types: {', '.join(allowed_types)}",
            details={"file_type": file_type, "allowed_types": allowed_types},
        )


class FileValidationException(FileUploadException):
    """Exception raised when file validation fails"""

    pass


# Data Processing Exceptions
class DataProcessingException(EDABaseException):
    """Base exception for data processing errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATA_PROCESSING_ERROR",
            status_code=422,
            details=details,
        )


class DataValidationException(DataProcessingException):
    """Exception raised when data validation fails"""

    pass


class InsufficientDataException(DataProcessingException):
    """Exception raised when dataset has insufficient data for analysis"""

    def __init__(self, rows: int, columns: int, min_rows: int = 10):
        super().__init__(
            message=f"Insufficient data for analysis. Dataset has {rows} rows and {columns} columns. Minimum {min_rows} rows required.",
            details={"rows": rows, "columns": columns, "min_rows": min_rows},
        )


class DataLimitExceedException(DataProcessingException):
    """Exception raised when data exceeds processing limits"""

    def __init__(self, dimension: str, actual: int, limit: int):
        super().__init__(
            message=f"Data {dimension} {actual} exceeds limit {limit}",
            details={"dimension": dimension, "actual": actual, "limit": limit},
        )


# Analysis Exceptions
class AnalysisException(EDABaseException):
    """Base exception for analysis errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ANALYSIS_ERROR",
            status_code=500,
            details=details,
        )


class StatisticalAnalysisException(AnalysisException):
    """Exception raised when statistical analysis fails"""

    pass


class VisualizationException(AnalysisException):
    """Exception raised when visualization generation fails"""

    pass


# LLM Exceptions
class LLMException(EDABaseException):
    """Base exception for LLM-related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, error_code="LLM_ERROR", status_code=503, details=details
        )


class LLMAPIException(LLMException):
    """Exception raised when LLM API call fails"""

    pass


class LLMTimeoutException(LLMException):
    """Exception raised when LLM request times out"""

    def __init__(self, timeout: int):
        super().__init__(
            message=f"LLM request timed out after {timeout} seconds",
            details={"timeout": timeout},
        )


class LLMRateLimitException(LLMException):
    """Exception raised when LLM rate limit is exceeded"""

    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(
            message="LLM rate limit exceeded",
            details={"retry_after": retry_after} if retry_after else {},
        )


# Job Exceptions
class JobException(EDABaseException):
    """Base exception for job-related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, error_code="JOB_ERROR", status_code=500, details=details
        )


class JobNotFoundException(JobException):
    """Exception raised when job is not found"""

    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job with ID '{job_id}' not found",
            details={"job_id": job_id},
        )
        self.status_code = 404


class JobTimeoutException(JobException):
    """Exception raised when job execution times out"""

    def __init__(self, job_id: str, timeout: int):
        super().__init__(
            message=f"Job '{job_id}' timed out after {timeout} seconds",
            details={"job_id": job_id, "timeout": timeout},
        )


class JobExecutionException(JobException):
    """Exception raised when job execution fails"""

    pass


# Configuration Exceptions
class ConfigurationException(EDABaseException):
    """Exception raised for configuration errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )


# Resource Exceptions
class ResourceException(EDABaseException):
    """Base exception for resource-related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_ERROR",
            status_code=500,
            details=details,
        )


class ResourceNotFoundException(ResourceException):
    """Exception raised when resource is not found"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )
        self.status_code = 404


class ResourceExhaustedException(ResourceException):
    """Exception raised when system resources are exhausted"""

    pass
