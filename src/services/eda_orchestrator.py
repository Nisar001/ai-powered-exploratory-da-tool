"""
EDA Orchestrator

Main orchestrator that coordinates the entire EDA pipeline:
data loading, statistical analysis, visualization, and insight generation.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.core.config import settings
from src.core.exceptions import AnalysisException
from src.core.logging import get_logger
from src.models.schemas import (
    AnalysisResult,
    AnalysisType,
    ColumnStatistics,
    DataType,
)
from src.services.data_loader import DataLoader
from src.services.llm_service import LLMService
from src.services.statistical_analyzer import StatisticalAnalyzer
from src.services.visualization_engine import VisualizationEngine

logger = get_logger(__name__)


class EDAOrchestrator:
    """
    Orchestrates the complete EDA workflow from data loading to insight generation
    """

    def __init__(self, job_id: str, file_path: Path):
        self.job_id = job_id
        self.file_path = file_path

        # Initialize service components
        self.data_loader = DataLoader()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.visualization_engine = VisualizationEngine()
        self.llm_service = LLMService()

        self.df: Optional[pd.DataFrame] = None
        self.start_time: Optional[float] = None

    def execute_full_analysis(
        self,
        analysis_types: List[AnalysisType] = [AnalysisType.ALL],
        generate_insights: bool = True,
        generate_visualizations: bool = True,
    ) -> AnalysisResult:
        """
        Execute complete EDA analysis pipeline

        Args:
            analysis_types: Types of analysis to perform
            generate_insights: Whether to generate AI insights
            generate_visualizations: Whether to generate visualizations

        Returns:
            Complete AnalysisResult

        Raises:
            AnalysisException: If analysis fails
        """
        self.start_time = time.time()
        logger.info(f"Starting EDA analysis for job {self.job_id}")

        try:
            # Step 1: Load and validate data
            logger.info("Step 1/5: Loading and validating data")
            self.df = self.data_loader.load_csv(self.file_path)
            self.df = self.data_loader.optimize_datatypes(self.df)

            # Step 2: Infer schema
            logger.info("Step 2/5: Inferring dataset schema")
            dataset_schema = self.data_loader.infer_schema(self.df)

            # Step 3: Perform statistical analysis
            logger.info("Step 3/5: Performing statistical analysis")
            column_statistics = self._analyze_columns(dataset_schema)

            correlation_analysis = None
            outlier_analysis = []
            distribution_analysis = []

            # Determine which analyses to run
            run_all = AnalysisType.ALL in analysis_types

            if run_all or AnalysisType.CORRELATION in analysis_types:
                correlation_analysis = self.statistical_analyzer.analyze_correlations(
                    self.df
                )

            if run_all or AnalysisType.OUTLIER in analysis_types:
                outlier_analysis = self._analyze_outliers(column_statistics)

            if run_all or AnalysisType.DISTRIBUTION in analysis_types:
                distribution_analysis = self._analyze_distributions(column_statistics)

            # Step 4: Generate visualizations
            visualizations = []
            if generate_visualizations:
                logger.info("Step 4/5: Generating visualizations")
                column_types = {
                    col.column_name: col.data_type
                    for col in column_statistics
                }
                visualizations = self.visualization_engine.generate_all_visualizations(
                    self.df, column_types, self.job_id
                )
            else:
                logger.info("Step 4/5: Skipping visualization generation")

            # Step 5: Generate AI insights
            ai_insights = None
            if generate_insights:
                logger.info("Step 5/5: Generating AI insights")
                analysis_dict = self._prepare_analysis_dict(
                    dataset_schema,
                    column_statistics,
                    correlation_analysis,
                    outlier_analysis,
                    distribution_analysis,
                )
                try:
                    ai_insights = self.llm_service.generate_insights(analysis_dict)
                except Exception as e:
                    logger.warning(
                        f"Failed to generate AI insights: {str(e)}. Continuing without insights."
                    )
            else:
                logger.info("Step 5/5: Skipping AI insight generation")

            # Calculate analysis duration
            duration = time.time() - self.start_time

            # Create final result
            result = AnalysisResult(
                job_id=self.job_id,
                file_id=str(self.file_path.stem),
                dataset_schema=dataset_schema,
                column_statistics=column_statistics,
                correlation_analysis=correlation_analysis,
                outlier_analysis=outlier_analysis,
                distribution_analysis=distribution_analysis,
                visualizations=visualizations,
                ai_insights=ai_insights,
                analysis_duration_seconds=round(duration, 2),
                completed_at=datetime.utcnow(),
            )

            logger.info(
                f"Analysis completed successfully in {duration:.2f} seconds"
            )

            return result

        except Exception as e:
            logger.error(
                f"Analysis failed for job {self.job_id}: {str(e)}", exc_info=True
            )
            raise AnalysisException(f"Analysis failed: {str(e)}")

    def _analyze_columns(
        self, dataset_schema
    ) -> List[ColumnStatistics]:
        """
        Analyze all columns in the dataset

        Args:
            dataset_schema: Dataset schema with column information

        Returns:
            List of ColumnStatistics
        """
        column_stats = []

        for col_schema in dataset_schema.columns:
            try:
                col_stat = self.statistical_analyzer.analyze_column(
                    self.df, col_schema.name, col_schema.data_type
                )
                column_stats.append(col_stat)
            except Exception as e:
                logger.warning(
                    f"Failed to analyze column {col_schema.name}: {str(e)}"
                )

        return column_stats

    def _analyze_outliers(
        self, column_statistics: List[ColumnStatistics]
    ) -> List:
        """
        Detect outliers in numeric columns

        Args:
            column_statistics: List of column statistics

        Returns:
            List of OutlierAnalysis results
        """
        outlier_results = []

        numeric_columns = [
            col_stat.column_name
            for col_stat in column_statistics
            if col_stat.data_type == DataType.NUMERIC
        ]

        for column in numeric_columns[:20]:  # Limit to first 20 numeric columns
            try:
                outlier_analysis = self.statistical_analyzer.detect_outliers(
                    self.df, column
                )
                if outlier_analysis.outlier_count > 0:
                    outlier_results.append(outlier_analysis)
            except Exception as e:
                logger.warning(
                    f"Failed to detect outliers in {column}: {str(e)}"
                )

        return outlier_results

    def _analyze_distributions(
        self, column_statistics: List[ColumnStatistics]
    ) -> List:
        """
        Analyze distributions of numeric columns

        Args:
            column_statistics: List of column statistics

        Returns:
            List of DistributionAnalysis results
        """
        distribution_results = []

        numeric_columns = [
            col_stat.column_name
            for col_stat in column_statistics
            if col_stat.data_type == DataType.NUMERIC
        ]

        for column in numeric_columns[:20]:  # Limit to first 20 numeric columns
            try:
                dist_analysis = self.statistical_analyzer.analyze_distribution(
                    self.df, column
                )
                distribution_results.append(dist_analysis)
            except Exception as e:
                logger.warning(
                    f"Failed to analyze distribution for {column}: {str(e)}"
                )

        return distribution_results

    def _prepare_analysis_dict(
        self,
        dataset_schema,
        column_statistics: List[ColumnStatistics],
        correlation_analysis,
        outlier_analysis: List,
        distribution_analysis: List,
    ) -> Dict[str, Any]:
        """
        Prepare analysis results as dictionary for LLM

        Args:
            dataset_schema: Dataset schema
            column_statistics: Column statistics
            correlation_analysis: Correlation analysis results
            outlier_analysis: Outlier detection results
            distribution_analysis: Distribution analysis results

        Returns:
            Dictionary with all analysis results
        """
        return {
            "dataset_schema": dataset_schema.model_dump(),
            "column_statistics": [stat.model_dump() for stat in column_statistics],
            "correlation_analysis": (
                correlation_analysis.model_dump() if correlation_analysis else None
            ),
            "outlier_analysis": [
                outlier.model_dump() for outlier in outlier_analysis
            ],
            "distribution_analysis": [
                dist.model_dump() for dist in distribution_analysis
            ],
        }

    def cleanup(self) -> None:
        """Clean up resources after analysis"""
        try:
            # Clear DataFrame from memory
            if self.df is not None:
                del self.df
                self.df = None

            logger.debug(f"Cleaned up resources for job {self.job_id}")

        except Exception as e:
            logger.warning(f"Cleanup failed: {str(e)}")
