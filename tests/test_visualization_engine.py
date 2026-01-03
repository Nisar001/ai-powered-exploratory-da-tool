from pathlib import Path

import pandas as pd

from src.models.schemas import DataType
from src.services.visualization_engine import VisualizationEngine


def test_generate_visualizations_creates_files(tmp_path, mock_env):
    df = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "b": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
            "category": ["x", "y", "x", "y", "x", "y", "x", "y", "x", "y"],
        }
    )
    column_types = {"a": DataType.NUMERIC, "b": DataType.NUMERIC, "category": DataType.CATEGORICAL}

    engine = VisualizationEngine(output_dir=tmp_path)
    results = engine.generate_all_visualizations(df, column_types, job_id="job-1")

    assert results
    for viz in results:
        assert (tmp_path / Path(viz.file_path).name).exists()
