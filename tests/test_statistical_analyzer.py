import pandas as pd

from src.services.statistical_analyzer import StatisticalAnalyzer
from src.models.schemas import DataType


def test_numeric_analysis_computes_basic_stats():
    analyzer = StatisticalAnalyzer()
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 100]})

    stats = analyzer.analyze_column(df, "x", DataType.NUMERIC)

    assert stats.numeric_stats is not None
    assert stats.numeric_stats.mean is not None
    assert stats.numeric_stats.outlier_count >= 1


def test_correlation_identifies_strong_relationship():
    analyzer = StatisticalAnalyzer()
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})

    corr = analyzer.analyze_correlations(df)

    assert corr is not None
    assert any(item["column1"] == "x" and item["column2"] == "y" for item in corr.strong_correlations)


def test_outlier_detection_methods():
    analyzer = StatisticalAnalyzer()
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 100]})

    iqr_outliers = analyzer.detect_outliers(df, "x", method="iqr")
    z_outliers = analyzer.detect_outliers(df, "x", method="zscore")

    assert iqr_outliers.outlier_count >= 1
    assert z_outliers.method == "zscore"
