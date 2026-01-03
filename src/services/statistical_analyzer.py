"""
Statistical Analysis Engine

Comprehensive statistical analysis including descriptive statistics,
correlation analysis, outlier detection, and distribution analysis.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest

from src.core.config import settings
from src.core.exceptions import StatisticalAnalysisException
from src.core.logging import get_logger
from src.models.schemas import (
    CategoricalStatistics,
    ColumnStatistics,
    CorrelationAnalysis,
    DataType,
    DistributionAnalysis,
    NumericStatistics,
    OutlierAnalysis,
)

logger = get_logger(__name__)


class StatisticalAnalyzer:
    """
    Performs comprehensive statistical analysis on datasets
    """

    def __init__(self):
        self.outlier_method = settings.statistical_analysis.outlier_method
        self.outlier_threshold = settings.statistical_analysis.outlier_threshold
        self.correlation_threshold = settings.statistical_analysis.correlation_threshold
        self.numeric_precision = settings.data_processing.numeric_precision

    def analyze_column(
        self, df: pd.DataFrame, column: str, data_type: DataType
    ) -> ColumnStatistics:
        """
        Perform complete statistical analysis on a single column

        Args:
            df: DataFrame containing the column
            column: Column name to analyze
            data_type: Detected data type of the column

        Returns:
            ColumnStatistics with complete analysis
        """
        logger.debug(f"Analyzing column: {column} (type: {data_type})")

        try:
            numeric_stats = None
            categorical_stats = None

            if data_type == DataType.NUMERIC:
                numeric_stats = self._analyze_numeric_column(df[column])
            elif data_type in [DataType.CATEGORICAL, DataType.TEXT, DataType.BOOLEAN]:
                categorical_stats = self._analyze_categorical_column(df[column])

            return ColumnStatistics(
                column_name=column,
                data_type=data_type,
                numeric_stats=numeric_stats,
                categorical_stats=categorical_stats,
            )

        except Exception as e:
            logger.error(f"Failed to analyze column {column}: {str(e)}", exc_info=True)
            raise StatisticalAnalysisException(
                f"Failed to analyze column {column}: {str(e)}"
            )

    def _analyze_numeric_column(self, series: pd.Series) -> NumericStatistics:
        """
        Calculate comprehensive statistics for numeric column

        Args:
            series: Numeric Series to analyze

        Returns:
            NumericStatistics with all calculated metrics
        """
        # Remove null values for calculations
        clean_series = series.dropna()

        if len(clean_series) == 0:
            return NumericStatistics()

        try:
            # Basic statistics
            mean_val = float(clean_series.mean())
            median_val = float(clean_series.median())
            mode_result = clean_series.mode()
            mode_val = float(mode_result[0]) if len(mode_result) > 0 else None

            # Dispersion measures
            std_val = float(clean_series.std())
            var_val = float(clean_series.var())
            min_val = float(clean_series.min())
            max_val = float(clean_series.max())

            # Quartiles
            q1_val = float(clean_series.quantile(0.25))
            q3_val = float(clean_series.quantile(0.75))
            iqr_val = q3_val - q1_val

            # Shape measures
            skew_val = float(clean_series.skew())
            kurt_val = float(clean_series.kurtosis())

            # Outlier count using IQR method
            lower_bound = q1_val - (self.outlier_threshold * iqr_val)
            upper_bound = q3_val + (self.outlier_threshold * iqr_val)
            outlier_count = int(
                ((clean_series < lower_bound) | (clean_series > upper_bound)).sum()
            )

            return NumericStatistics(
                mean=round(mean_val, self.numeric_precision),
                median=round(median_val, self.numeric_precision),
                mode=round(mode_val, self.numeric_precision) if mode_val else None,
                std_dev=round(std_val, self.numeric_precision),
                variance=round(var_val, self.numeric_precision),
                min=round(min_val, self.numeric_precision),
                max=round(max_val, self.numeric_precision),
                q1=round(q1_val, self.numeric_precision),
                q3=round(q3_val, self.numeric_precision),
                iqr=round(iqr_val, self.numeric_precision),
                skewness=round(skew_val, self.numeric_precision),
                kurtosis=round(kurt_val, self.numeric_precision),
                outlier_count=outlier_count,
            )

        except Exception as e:
            logger.warning(f"Failed to calculate some numeric statistics: {str(e)}")
            return NumericStatistics()

    def _analyze_categorical_column(
        self, series: pd.Series
    ) -> CategoricalStatistics:
        """
        Calculate statistics for categorical column

        Args:
            series: Categorical Series to analyze

        Returns:
            CategoricalStatistics with frequency information
        """
        clean_series = series.dropna()

        if len(clean_series) == 0:
            return CategoricalStatistics(
                unique_count=0, frequency_distribution={}
            )

        try:
            # Frequency distribution
            value_counts = clean_series.value_counts()

            # Get top categories (limit to avoid huge distributions)
            top_n = min(20, len(value_counts))
            frequency_dist = {
                str(k): int(v) for k, v in value_counts.head(top_n).items()
            }

            # Most frequent
            most_frequent = str(value_counts.index[0]) if len(value_counts) > 0 else None
            frequency = int(value_counts.iloc[0]) if len(value_counts) > 0 else None

            return CategoricalStatistics(
                unique_count=int(series.nunique()),
                most_frequent=most_frequent,
                frequency=frequency,
                frequency_distribution=frequency_dist,
            )

        except Exception as e:
            logger.warning(
                f"Failed to calculate categorical statistics: {str(e)}"
            )
            return CategoricalStatistics(
                unique_count=int(series.nunique()), frequency_distribution={}
            )

    def analyze_correlations(
        self, df: pd.DataFrame, method: str = "pearson"
    ) -> Optional[CorrelationAnalysis]:
        """
        Perform correlation analysis on numeric columns

        Args:
            df: DataFrame to analyze
            method: Correlation method ('pearson', 'spearman', 'kendall')

        Returns:
            CorrelationAnalysis or None if insufficient numeric data
        """
        logger.info(f"Analyzing correlations using {method} method")

        try:
            # Select only numeric columns
            numeric_df = df.select_dtypes(include=[np.number])

            if numeric_df.shape[1] < 2:
                logger.warning(
                    "Insufficient numeric columns for correlation analysis"
                )
                return None

            # Calculate correlation matrix
            corr_matrix = numeric_df.corr(method=method)

            # Convert to dict format
            corr_dict = {
                col: {
                    inner_col: round(float(val), self.numeric_precision)
                    for inner_col, val in corr_matrix[col].items()
                }
                for col in corr_matrix.columns
            }

            # Find strong correlations
            strong_correlations = []
            columns = corr_matrix.columns

            for i, col1 in enumerate(columns):
                for j, col2 in enumerate(columns):
                    if i < j:  # Avoid duplicates and self-correlation
                        corr_value = corr_matrix.loc[col1, col2]

                        if abs(corr_value) >= self.correlation_threshold:
                            strong_correlations.append(
                                {
                                    "column1": col1,
                                    "column2": col2,
                                    "correlation": round(
                                        float(corr_value), self.numeric_precision
                                    ),
                                    "strength": self._classify_correlation_strength(
                                        abs(corr_value)
                                    ),
                                    "direction": "positive"
                                    if corr_value > 0
                                    else "negative",
                                }
                            )

            # Sort by absolute correlation value
            strong_correlations.sort(
                key=lambda x: abs(x["correlation"]), reverse=True
            )

            logger.info(
                f"Found {len(strong_correlations)} strong correlations"
            )

            return CorrelationAnalysis(
                method=method,
                correlation_matrix=corr_dict,
                strong_correlations=strong_correlations,
            )

        except Exception as e:
            logger.error(f"Correlation analysis failed: {str(e)}", exc_info=True)
            raise StatisticalAnalysisException(
                f"Correlation analysis failed: {str(e)}"
            )

    def _classify_correlation_strength(self, abs_corr: float) -> str:
        """Classify correlation strength"""
        if abs_corr >= 0.9:
            return "very_strong"
        elif abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        elif abs_corr >= 0.3:
            return "weak"
        else:
            return "very_weak"

    def detect_outliers(
        self, df: pd.DataFrame, column: str, method: Optional[str] = None
    ) -> OutlierAnalysis:
        """
        Detect outliers in a numeric column

        Args:
            df: DataFrame containing the column
            column: Column name to analyze
            method: Detection method ('iqr', 'zscore', 'isolation_forest')

        Returns:
            OutlierAnalysis with detection results
        """
        method = method or self.outlier_method
        logger.debug(f"Detecting outliers in {column} using {method} method")

        try:
            series = df[column].dropna()

            if len(series) == 0:
                return OutlierAnalysis(
                    column_name=column,
                    method=method,
                    outlier_count=0,
                    outlier_percentage=0.0,
                    outlier_indices=[],
                )

            if method == "iqr":
                outlier_mask = self._detect_outliers_iqr(series)
            elif method == "zscore":
                outlier_mask = self._detect_outliers_zscore(series)
            elif method == "isolation_forest":
                outlier_mask = self._detect_outliers_isolation_forest(
                    series.values.reshape(-1, 1)
                )
            else:
                raise ValueError(f"Unknown outlier detection method: {method}")

            outlier_indices = series.index[outlier_mask].tolist()
            outlier_count = len(outlier_indices)
            outlier_percentage = (outlier_count / len(series)) * 100

            return OutlierAnalysis(
                column_name=column,
                method=method,
                outlier_count=outlier_count,
                outlier_percentage=round(outlier_percentage, 2),
                outlier_indices=outlier_indices[:100],  # Limit to first 100
            )

        except Exception as e:
            logger.warning(f"Outlier detection failed for {column}: {str(e)}")
            return OutlierAnalysis(
                column_name=column,
                method=method,
                outlier_count=0,
                outlier_percentage=0.0,
                outlier_indices=[],
            )

    def _detect_outliers_iqr(self, series: pd.Series) -> np.ndarray:
        """Detect outliers using IQR method"""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - (self.outlier_threshold * iqr)
        upper_bound = q3 + (self.outlier_threshold * iqr)

        return (series < lower_bound) | (series > upper_bound)

    def _detect_outliers_zscore(
        self, series: pd.Series, threshold: float = 3.0
    ) -> np.ndarray:
        """Detect outliers using Z-score method"""
        z_scores = np.abs(stats.zscore(series))
        return z_scores > threshold

    def _detect_outliers_isolation_forest(
        self, data: np.ndarray, contamination: float = 0.1
    ) -> np.ndarray:
        """Detect outliers using Isolation Forest"""
        clf = IsolationForest(contamination=contamination, random_state=42)
        predictions = clf.fit_predict(data)
        return predictions == -1

    def analyze_distribution(
        self, df: pd.DataFrame, column: str
    ) -> DistributionAnalysis:
        """
        Analyze distribution characteristics of a numeric column

        Args:
            df: DataFrame containing the column
            column: Column name to analyze

        Returns:
            DistributionAnalysis with normality test results
        """
        logger.debug(f"Analyzing distribution for {column}")

        try:
            series = df[column].dropna()

            if len(series) < 20:
                logger.warning(
                    f"Insufficient data for distribution analysis: {len(series)} samples"
                )
                return DistributionAnalysis(
                    column_name=column,
                    distribution_type="unknown",
                    is_normal=False,
                )

            # Perform Shapiro-Wilk test for normality (for samples < 5000)
            if len(series) <= 5000:
                statistic, p_value = stats.shapiro(series)
                is_normal = p_value > 0.05
            else:
                # Use Kolmogorov-Smirnov test for larger samples
                statistic, p_value = stats.kstest(
                    series, "norm", args=(series.mean(), series.std())
                )
                is_normal = p_value > 0.05

            # Classify distribution type based on skewness
            skewness = series.skew()
            if abs(skewness) < 0.5:
                distribution_type = "symmetric"
            elif skewness > 0:
                distribution_type = "right_skewed"
            else:
                distribution_type = "left_skewed"

            return DistributionAnalysis(
                column_name=column,
                distribution_type=distribution_type,
                is_normal=is_normal,
                normality_test_statistic=round(float(statistic), self.numeric_precision),
                normality_p_value=round(float(p_value), self.numeric_precision),
            )

        except Exception as e:
            logger.warning(f"Distribution analysis failed for {column}: {str(e)}")
            return DistributionAnalysis(
                column_name=column,
                distribution_type="unknown",
                is_normal=False,
            )

    def get_data_quality_score(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Calculate overall data quality score

        Args:
            df: DataFrame to assess

        Returns:
            Dictionary with quality metrics
        """
        logger.info("Calculating data quality score")

        try:
            # Missing data score
            missing_percentage = (df.isnull().sum().sum() / df.size) * 100

            # Duplicate rows
            duplicate_rows = df.duplicated().sum()
            duplicate_percentage = (duplicate_rows / len(df)) * 100

            # Constant columns (zero variance)
            numeric_df = df.select_dtypes(include=[np.number])
            constant_columns = (numeric_df.nunique() == 1).sum()

            # Overall quality score (0-100)
            quality_score = 100
            quality_score -= min(missing_percentage, 30)  # Max -30 for missing data
            quality_score -= min(duplicate_percentage, 20)  # Max -20 for duplicates
            quality_score -= min(
                constant_columns * 5, 20
            )  # -5 per constant column, max -20

            quality_score = max(0, quality_score)

            return {
                "overall_score": round(quality_score, 2),
                "missing_data_percentage": round(missing_percentage, 2),
                "duplicate_rows": int(duplicate_rows),
                "duplicate_percentage": round(duplicate_percentage, 2),
                "constant_columns": int(constant_columns),
                "assessment": self._classify_quality_score(quality_score),
            }

        except Exception as e:
            logger.error(f"Data quality assessment failed: {str(e)}", exc_info=True)
            return {
                "overall_score": 0,
                "assessment": "unknown",
                "error": str(e),
            }

    def _classify_quality_score(self, score: float) -> str:
        """Classify data quality based on score"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "very_poor"
