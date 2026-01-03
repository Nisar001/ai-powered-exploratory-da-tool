from pathlib import Path

import pandas as pd

from src.models.schemas import AnalysisType
from src.services.eda_orchestrator import EDAOrchestrator


def test_orchestrator_full_pipeline(tmp_path, mock_env):
    data = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "b": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        }
    )
    file_path = tmp_path / "dataset.csv"
    data.to_csv(file_path, index=False)

    orchestrator = EDAOrchestrator(job_id="job-123", file_path=file_path)
    result = orchestrator.execute_full_analysis(
        analysis_types=[AnalysisType.ALL],
        generate_insights=False,
        generate_visualizations=False,
    )

    assert result.dataset_schema.row_count == len(data)
    assert result.column_statistics
    assert result.analysis_duration_seconds >= 0

    orchestrator.cleanup()
