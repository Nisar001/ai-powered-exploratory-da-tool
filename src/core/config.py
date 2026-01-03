"""
Configuration Management Module

This module provides centralized, type-safe configuration management
using Pydantic Settings. All configuration is environment-driven and validated.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application-level configuration"""

    app_name: str = Field(default="AI-Powered EDA Platform")
    app_version: str = Field(default="1.0.0")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class ServerSettings(BaseSettings):
    """Server configuration"""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1)
    reload: bool = Field(default=False)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class APISettings(BaseSettings):
    """API configuration"""

    api_v1_prefix: str = Field(default="/api/v1")
    api_title: str = Field(default="AI-Powered EDA API")
    api_description: str = Field(
        default="Production-grade Exploratory Data Analysis Platform"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class SecuritySettings(BaseSettings):
    """Security configuration"""

    secret_key: str = Field(default="change-me-in-production")
    allowed_origins: str = Field(default="*")
    cors_enabled: bool = Field(default=True)
    api_key_enabled: bool = Field(default=False)
    api_key: str = Field(default="")

    @field_validator("allowed_origins")
    @classmethod
    def parse_origins(cls, v: str) -> List[str]:
        """Parse comma-separated origins"""
        if v == "*":
            return ["*"]
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class FileUploadSettings(BaseSettings):
    """File upload configuration"""

    max_upload_size_mb: int = Field(default=100, ge=1, le=1000)
    allowed_extensions: str = Field(default=".csv")
    upload_dir: Path = Field(default=Path("data/uploads"))
    results_dir: Path = Field(default=Path("data/results"))
    temp_dir: Path = Field(default=Path("data/temp"))

    @field_validator("allowed_extensions")
    @classmethod
    def parse_extensions(cls, v: str) -> List[str]:
        """Parse comma-separated extensions"""
        return [ext.strip() for ext in v.split(",") if ext.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class DataProcessingSettings(BaseSettings):
    """Data processing configuration"""

    max_rows: int = Field(default=1_000_000, ge=1)
    max_columns: int = Field(default=1000, ge=1)
    chunk_size: int = Field(default=10_000, ge=100)
    numeric_precision: int = Field(default=4, ge=1, le=10)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class StatisticalAnalysisSettings(BaseSettings):
    """Statistical analysis configuration"""

    outlier_method: Literal["iqr", "zscore", "isolation_forest"] = Field(default="iqr")
    outlier_threshold: float = Field(default=1.5, ge=0.1)
    correlation_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    missing_value_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    skewness_threshold: float = Field(default=1.0, ge=0.0)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class VisualizationSettings(BaseSettings):
    """Visualization configuration"""

    plot_dpi: int = Field(default=100, ge=50, le=300)
    plot_format: Literal["png", "jpg", "svg", "pdf"] = Field(default="png")
    max_plots: int = Field(default=20, ge=1, le=100)
    figure_size_width: int = Field(default=10, ge=5, le=20)
    figure_size_height: int = Field(default=6, ge=4, le=15)
    color_palette: str = Field(default="Set2")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class LLMSettings(BaseSettings):
    """LLM configuration"""

    llm_provider: Literal["google", "anthropic", "azure"] = Field(default="google")
    google_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    llm_model: str = Field(default="models/gemini-2.5-flash")
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=2000, ge=100, le=4096)
    llm_timeout: int = Field(default=60, ge=10)
    llm_max_retries: int = Field(default=3, ge=1, le=10)
    llm_retry_delay: int = Field(default=2, ge=1)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class RedisSettings(BaseSettings):
    """Redis configuration"""

    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_db: int = Field(default=0, ge=0, le=15)
    redis_password: str = Field(default="")
    redis_decode_responses: bool = Field(default=True)
    redis_max_connections: int = Field(default=50, ge=1)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class CelerySettings(BaseSettings):
    """Celery configuration"""

    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/0")
    celery_task_track_started: bool = Field(default=True)
    celery_task_time_limit: int = Field(default=3600, ge=60)
    celery_task_soft_time_limit: int = Field(default=3000, ge=60)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class DatabaseSettings(BaseSettings):
    """Database configuration"""

    database_url: str = Field(default="sqlite+aiosqlite:///./data/eda_platform.db")
    db_echo: bool = Field(default=False)
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=1)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class MonitoringSettings(BaseSettings):
    """Monitoring and logging configuration"""

    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=9090, ge=1, le=65535)
    sentry_dsn: str = Field(default="")
    log_file_path: Path = Field(default=Path("logs/app.log"))
    log_rotation: str = Field(default="100 MB")
    log_retention: str = Field(default="30 days")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class PerformanceSettings(BaseSettings):
    """Performance and concurrency configuration"""

    background_tasks_enabled: bool = Field(default=True)
    max_concurrent_jobs: int = Field(default=10, ge=1, le=100)
    job_timeout: int = Field(default=3600, ge=60)
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=3600, ge=60)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class ReportSettings(BaseSettings):
    """Report generation configuration"""

    report_format: Literal["json", "html", "pdf"] = Field(default="json")
    enable_html_report: bool = Field(default=True)
    enable_pdf_report: bool = Field(default=False)
    include_raw_data: bool = Field(default=False)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class Settings:
    """
    Unified settings container providing access to all configuration domains.
    This is the main interface for accessing application configuration.
    """

    def __init__(self):
        self.app = AppSettings()
        self.server = ServerSettings()
        self.api = APISettings()
        self.security = SecuritySettings()
        self.file_upload = FileUploadSettings()
        self.data_processing = DataProcessingSettings()
        self.statistical_analysis = StatisticalAnalysisSettings()
        self.visualization = VisualizationSettings()
        self.llm = LLMSettings()
        self.redis = RedisSettings()
        self.celery = CelerySettings()
        self.database = DatabaseSettings()
        self.monitoring = MonitoringSettings()
        self.performance = PerformanceSettings()
        self.report = ReportSettings()

        # Create necessary directories
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist"""
        directories = [
            self.file_upload.upload_dir,
            self.file_upload.results_dir,
            self.file_upload.temp_dir,
            self.monitoring.log_file_path.parent,
            Path("reports"),
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.app.app_env == "production"

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.app.app_env == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    This ensures we only load configuration once during application lifetime.
    """
    return Settings()


# Global settings instance
settings = get_settings()
