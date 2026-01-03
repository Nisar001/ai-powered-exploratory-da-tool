"""
Pydantic Models and Schemas

This module contains all data models, request/response schemas,
and internal data structures used throughout the platform.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


# Enumerations
class JobStatus(str, Enum):
    """Job execution status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataType(str, Enum):
    """Column data types"""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class AnalysisType(str, Enum):
    """Types of analysis to perform"""

    DESCRIPTIVE = "descriptive"
    CORRELATION = "correlation"
    DISTRIBUTION = "distribution"
    OUTLIER = "outlier"
    TREND = "trend"
    ALL = "all"


# Request Models
class FileUploadRequest(BaseModel):
    """Request model for file upload metadata"""

    filename: str = Field(..., description="Name of the uploaded file")
    description: Optional[str] = Field(None, description="Optional file description")
    tags: Optional[List[str]] = Field(default=[], description="Optional tags")

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename"""
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        return v.strip()


class AnalysisRequest(BaseModel):
    """Request model for triggering analysis"""

    file_id: str = Field(..., description="ID of the uploaded file")
    analysis_types: List[AnalysisType] = Field(
        default=[AnalysisType.ALL], description="Types of analysis to perform"
    )
    generate_insights: bool = Field(
        default=True, description="Whether to generate AI insights"
    )
    generate_visualizations: bool = Field(
        default=True, description="Whether to generate visualizations"
    )
    custom_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom analysis configuration"
    )


# Response Models
class BaseResponse(BaseModel):
    """Base response model"""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class ErrorResponse(BaseModel):
    """Error response model"""

    error: Dict[str, Any] = Field(..., description="Error details")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


class FileUploadResponse(BaseResponse):
    """Response model for file upload"""

    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    filename: str = Field(..., description="Name of the uploaded file")
    size_bytes: int = Field(..., description="File size in bytes")
    upload_timestamp: datetime = Field(..., description="Upload timestamp")


class JobResponse(BaseResponse):
    """Response model for job creation"""

    job_id: str = Field(..., description="Unique identifier for the job")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    estimated_completion: Optional[datetime] = Field(
        None, description="Estimated completion time"
    )


class JobStatusResponse(BaseModel):
    """Response model for job status"""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress: float = Field(
        ..., ge=0.0, le=100.0, description="Job progress percentage"
    )
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(
        None, description="Job completion timestamp"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    result_available: bool = Field(
        ..., description="Whether results are available for retrieval"
    )


# Data Schema Models
class ColumnSchema(BaseModel):
    """Schema information for a single column"""

    name: str = Field(..., description="Column name")
    data_type: DataType = Field(..., description="Detected data type")
    missing_count: int = Field(..., description="Number of missing values")
    missing_percentage: float = Field(..., description="Percentage of missing values")
    unique_count: int = Field(..., description="Number of unique values")
    sample_values: List[Any] = Field(..., description="Sample values from the column")


class DatasetSchema(BaseModel):
    """Schema information for the entire dataset"""

    row_count: int = Field(..., description="Total number of rows")
    column_count: int = Field(..., description="Total number of columns")
    columns: List[ColumnSchema] = Field(..., description="Column schemas")
    total_missing: int = Field(..., description="Total missing values in dataset")
    memory_usage_mb: float = Field(..., description="Memory usage in megabytes")


# Statistical Analysis Models
class NumericStatistics(BaseModel):
    """Statistical measures for numeric columns"""

    mean: Optional[float] = Field(None, description="Mean value")
    median: Optional[float] = Field(None, description="Median value")
    mode: Optional[float] = Field(None, description="Mode value")
    std_dev: Optional[float] = Field(None, description="Standard deviation")
    variance: Optional[float] = Field(None, description="Variance")
    min: Optional[float] = Field(None, description="Minimum value")
    max: Optional[float] = Field(None, description="Maximum value")
    q1: Optional[float] = Field(None, description="First quartile")
    q3: Optional[float] = Field(None, description="Third quartile")
    iqr: Optional[float] = Field(None, description="Interquartile range")
    skewness: Optional[float] = Field(None, description="Skewness")
    kurtosis: Optional[float] = Field(None, description="Kurtosis")
    outlier_count: Optional[int] = Field(None, description="Number of outliers")


class CategoricalStatistics(BaseModel):
    """Statistical measures for categorical columns"""

    unique_count: int = Field(..., description="Number of unique categories")
    most_frequent: Optional[str] = Field(None, description="Most frequent category")
    frequency: Optional[int] = Field(
        None, description="Frequency of most common category"
    )
    frequency_distribution: Dict[str, int] = Field(
        ..., description="Frequency distribution"
    )


class ColumnStatistics(BaseModel):
    """Complete statistics for a column"""

    column_name: str = Field(..., description="Column name")
    data_type: DataType = Field(..., description="Data type")
    numeric_stats: Optional[NumericStatistics] = Field(
        None, description="Numeric statistics"
    )
    categorical_stats: Optional[CategoricalStatistics] = Field(
        None, description="Categorical statistics"
    )


class CorrelationAnalysis(BaseModel):
    """Correlation analysis results"""

    method: str = Field(..., description="Correlation method used")
    correlation_matrix: Dict[str, Dict[str, float]] = Field(
        ..., description="Correlation matrix"
    )
    strong_correlations: List[Dict[str, Any]] = Field(
        ..., description="List of strong correlations"
    )


class OutlierAnalysis(BaseModel):
    """Outlier detection results"""

    column_name: str = Field(..., description="Column name")
    method: str = Field(..., description="Detection method used")
    outlier_count: int = Field(..., description="Number of outliers detected")
    outlier_percentage: float = Field(..., description="Percentage of outliers")
    outlier_indices: List[int] = Field(..., description="Indices of outliers")


class DistributionAnalysis(BaseModel):
    """Distribution analysis results"""

    column_name: str = Field(..., description="Column name")
    distribution_type: str = Field(..., description="Detected distribution type")
    is_normal: bool = Field(..., description="Whether distribution is normal")
    normality_test_statistic: Optional[float] = Field(
        None, description="Normality test statistic"
    )
    normality_p_value: Optional[float] = Field(
        None, description="Normality test p-value"
    )


# Visualization Models
class Visualization(BaseModel):
    """Visualization metadata and data"""

    viz_id: str = Field(..., description="Visualization identifier")
    viz_type: str = Field(..., description="Type of visualization")
    title: str = Field(..., description="Visualization title")
    file_path: str = Field(..., description="Path to visualization file")
    columns_used: List[str] = Field(..., description="Columns used in visualization")
    description: Optional[str] = Field(None, description="Visualization description")


# AI Insights Models
class InsightItem(BaseModel):
    """Single insight item"""

    category: str = Field(..., description="Insight category")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed insight description")
    severity: str = Field(..., description="Insight severity: info, warning, critical")
    affected_columns: List[str] = Field(
        default=[], description="Columns related to this insight"
    )


class AIInsights(BaseModel):
    """AI-generated insights"""

    executive_summary: str = Field(..., description="High-level summary")
    key_findings: List[str] = Field(..., description="Key findings")
    data_quality_assessment: str = Field(..., description="Data quality assessment")
    insights: List[InsightItem] = Field(..., description="Detailed insights")
    recommendations: List[str] = Field(..., description="Recommendations")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Generation timestamp"
    )


# Complete Analysis Result
class AnalysisResult(BaseModel):
    """Complete analysis result"""

    job_id: str = Field(..., description="Job identifier")
    file_id: str = Field(..., description="File identifier")
    dataset_schema: DatasetSchema = Field(..., description="Dataset schema")
    column_statistics: List[ColumnStatistics] = Field(
        ..., description="Column-level statistics"
    )
    correlation_analysis: Optional[CorrelationAnalysis] = Field(
        None, description="Correlation analysis"
    )
    outlier_analysis: List[OutlierAnalysis] = Field(
        default=[], description="Outlier detection results"
    )
    distribution_analysis: List[DistributionAnalysis] = Field(
        default=[], description="Distribution analysis results"
    )
    visualizations: List[Visualization] = Field(
        default=[], description="Generated visualizations"
    )
    ai_insights: Optional[AIInsights] = Field(None, description="AI-generated insights")
    analysis_duration_seconds: float = Field(
        ..., description="Total analysis duration"
    )
    completed_at: datetime = Field(..., description="Completion timestamp")


class AnalysisReportResponse(BaseResponse):
    """Response model for analysis report"""

    result: AnalysisResult = Field(..., description="Analysis result")


# Health Check Models
class HealthStatus(BaseModel):
    """Health check status"""

    status: str = Field(..., description="Overall status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Health check timestamp"
    )
    services: Dict[str, bool] = Field(..., description="Service availability")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
