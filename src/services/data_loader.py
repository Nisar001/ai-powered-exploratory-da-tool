"""
Data Loader Module

Handles secure file loading, validation, and schema inference
with memory-efficient chunked processing.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from src.core.config import settings
from src.core.exceptions import (
    DataLimitExceedException,
    DataValidationException,
    FileValidationException,
    InsufficientDataException,
)
from src.core.logging import get_logger
from src.models.schemas import ColumnSchema, DatasetSchema, DataType

logger = get_logger(__name__)


class DataLoader:
    """
    Handles data loading with validation, schema inference, and memory optimization
    """

    def __init__(self):
        self.max_rows = settings.data_processing.max_rows
        self.max_columns = settings.data_processing.max_columns
        self.chunk_size = settings.data_processing.chunk_size

    def load_csv(
        self, file_path: Path, sample_size: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Load CSV file with validation and optional sampling

        Args:
            file_path: Path to CSV file
            sample_size: Optional number of rows to sample

        Returns:
            Loaded DataFrame

        Raises:
            FileValidationException: If file is invalid
            DataLimitExceedException: If data exceeds limits
        """
        logger.info(f"Loading CSV file: {file_path}")

        try:
            # Check file exists and is readable
            if not file_path.exists():
                raise FileValidationException(f"File not found: {file_path}")

            if not file_path.is_file():
                raise FileValidationException(f"Path is not a file: {file_path}")

            # Read first chunk to validate
            try:
                df_sample = pd.read_csv(file_path, nrows=1000)
            except Exception as e:
                raise FileValidationException(f"Failed to parse CSV: {str(e)}")

            # Validate dimensions
            if df_sample.shape[1] > self.max_columns:
                raise DataLimitExceedException(
                    dimension="columns",
                    actual=df_sample.shape[1],
                    limit=self.max_columns,
                )

            # Load full dataset or sample
            if sample_size:
                df = pd.read_csv(file_path, nrows=sample_size)
                logger.info(f"Loaded sample of {len(df)} rows")
            else:
                # Check file size for memory estimation
                file_size_mb = file_path.stat().st_size / (1024 * 1024)

                # For large files, use chunked reading
                if file_size_mb > 100:
                    logger.info(
                        f"Large file detected ({file_size_mb:.2f}MB), using chunked reading"
                    )
                    df = self._load_large_csv(file_path)
                else:
                    df = pd.read_csv(file_path)

            # Validate loaded data
            self._validate_dataframe(df)

            logger.info(
                f"Successfully loaded DataFrame with shape {df.shape} and memory usage {df.memory_usage(deep=True).sum() / 1024**2:.2f}MB"
            )

            return df

        except (FileValidationException, DataLimitExceedException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading CSV: {str(e)}", exc_info=True)
            raise FileValidationException(f"Failed to load CSV: {str(e)}")

    def _load_large_csv(self, file_path: Path) -> pd.DataFrame:
        """
        Load large CSV file in chunks with memory optimization

        Args:
            file_path: Path to CSV file

        Returns:
            Loaded DataFrame
        """
        chunks = []
        total_rows = 0

        try:
            for chunk in pd.read_csv(file_path, chunksize=self.chunk_size):
                total_rows += len(chunk)

                # Check row limit
                if total_rows > self.max_rows:
                    logger.warning(
                        f"Row limit reached at {total_rows}, truncating dataset"
                    )
                    chunks.append(chunk.head(self.max_rows - (total_rows - len(chunk))))
                    break

                chunks.append(chunk)

            df = pd.concat(chunks, ignore_index=True)
            return df

        except Exception as e:
            raise FileValidationException(
                f"Failed to load large CSV in chunks: {str(e)}"
            )

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """
        Validate DataFrame meets minimum requirements

        Args:
            df: DataFrame to validate

        Raises:
            InsufficientDataException: If data is insufficient
            DataValidationException: If validation fails
        """
        # Check for empty DataFrame
        if df.empty:
            raise InsufficientDataException(rows=0, columns=0)

        # Check minimum rows
        min_rows = 10
        if len(df) < min_rows:
            raise InsufficientDataException(
                rows=len(df), columns=len(df.columns), min_rows=min_rows
            )

        # Check for all-null columns
        null_columns = df.columns[df.isnull().all()].tolist()
        if null_columns:
            logger.warning(f"Columns with all null values: {null_columns}")

        # Check for duplicate column names
        if df.columns.duplicated().any():
            duplicates = df.columns[df.columns.duplicated()].tolist()
            raise DataValidationException(
                f"Duplicate column names found: {duplicates}"
            )

    def infer_schema(self, df: pd.DataFrame) -> DatasetSchema:
        """
        Infer comprehensive schema from DataFrame

        Args:
            df: DataFrame to analyze

        Returns:
            DatasetSchema with complete schema information
        """
        logger.info("Inferring dataset schema")

        column_schemas = []

        for column in df.columns:
            col_data = df[column]

            # Infer data type
            data_type = self._infer_column_type(col_data)

            # Calculate statistics
            missing_count = int(col_data.isnull().sum())
            missing_percentage = (missing_count / len(df)) * 100
            unique_count = int(col_data.nunique())

            # Get sample values (non-null)
            sample_values = (
                col_data.dropna().head(5).tolist() if not col_data.isnull().all() else []
            )

            column_schema = ColumnSchema(
                name=column,
                data_type=data_type,
                missing_count=missing_count,
                missing_percentage=round(missing_percentage, 2),
                unique_count=unique_count,
                sample_values=sample_values,
            )

            column_schemas.append(column_schema)

        # Calculate total missing values
        total_missing = int(df.isnull().sum().sum())

        # Calculate memory usage
        memory_usage_mb = df.memory_usage(deep=True).sum() / (1024**2)

        schema = DatasetSchema(
            row_count=len(df),
            column_count=len(df.columns),
            columns=column_schemas,
            total_missing=total_missing,
            memory_usage_mb=round(memory_usage_mb, 2),
        )

        logger.info(f"Schema inferred: {len(df)} rows, {len(df.columns)} columns")

        return schema

    def _infer_column_type(self, series: pd.Series) -> DataType:
        """
        Infer the semantic data type of a column

        Args:
            series: Pandas Series to analyze

        Returns:
            DataType enumeration
        """
        # Check for datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return DataType.DATETIME

        # Try to convert to datetime
        if series.dtype == object:
            try:
                pd.to_datetime(series.dropna().head(100), errors="raise")
                return DataType.DATETIME
            except:
                pass

        # Check for numeric types
        if pd.api.types.is_numeric_dtype(series):
            return DataType.NUMERIC

        # Try to convert to numeric
        if series.dtype == object:
            try:
                pd.to_numeric(series.dropna().head(100), errors="raise")
                return DataType.NUMERIC
            except:
                pass

        # Check for boolean
        if pd.api.types.is_bool_dtype(series):
            return DataType.BOOLEAN

        # Check if could be categorical
        unique_ratio = series.nunique() / len(series)
        if unique_ratio < 0.5:  # Less than 50% unique values
            return DataType.CATEGORICAL

        # Check for text content
        if series.dtype == object:
            # Check average string length
            avg_length = series.dropna().astype(str).str.len().mean()
            if avg_length > 50:  # Longer strings are likely text
                return DataType.TEXT
            else:
                return DataType.CATEGORICAL

        return DataType.UNKNOWN

    def optimize_datatypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame memory usage by downcasting numeric types

        Args:
            df: DataFrame to optimize

        Returns:
            Optimized DataFrame
        """
        logger.info("Optimizing DataFrame datatypes")

        initial_memory = df.memory_usage(deep=True).sum() / (1024**2)

        # Downcast integers
        int_columns = df.select_dtypes(include=["int"]).columns
        for col in int_columns:
            df[col] = pd.to_numeric(df[col], downcast="integer")

        # Downcast floats
        float_columns = df.select_dtypes(include=["float"]).columns
        for col in float_columns:
            df[col] = pd.to_numeric(df[col], downcast="float")

        # Convert low-cardinality object columns to category
        object_columns = df.select_dtypes(include=["object"]).columns
        for col in object_columns:
            if df[col].nunique() / len(df) < 0.5:
                df[col] = df[col].astype("category")

        final_memory = df.memory_usage(deep=True).sum() / (1024**2)

        logger.info(
            f"Memory optimized from {initial_memory:.2f}MB to {final_memory:.2f}MB "
            f"({((initial_memory - final_memory) / initial_memory * 100):.1f}% reduction)"
        )

        return df
