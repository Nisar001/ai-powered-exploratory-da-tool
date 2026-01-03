from pathlib import Path

import pandas as pd
import pytest

from src.core.exceptions import FileValidationException, InsufficientDataException
from src.services.data_loader import DataLoader


def test_load_and_infer_schema(tmp_path, mock_env):
    data = pd.DataFrame(
        {
            "sales": [100, 200, 150, 175, 190, 210, 205, 199, 188, 177, 165, 155],
            "region": ["north", "south", "east", "west", "north", "south", "east", "west", "north", "south", "east", "west"],
            "is_active": [True, False, True, True, False, True, True, True, False, True, False, True],
        }
    )
    file_path = tmp_path / "sample.csv"
    data.to_csv(file_path, index=False)

    loader = DataLoader()
    df = loader.load_csv(file_path)
    schema = loader.infer_schema(df)

    assert df.shape == data.shape
    assert schema.row_count == len(data)
    assert schema.column_count == len(data.columns)
    assert any(col.name == "sales" and col.data_type.value == "numeric" for col in schema.columns)
    assert any(col.name == "region" and col.data_type.value == "categorical" for col in schema.columns)


def test_load_csv_missing_file_raises():
    loader = DataLoader()
    with pytest.raises(FileValidationException):
        loader.load_csv(Path("nonexistent.csv"))


def test_validate_dataframe_min_rows(tmp_path, mock_env):
    data = pd.DataFrame({"a": [1, 2]})
    file_path = tmp_path / "tiny.csv"
    data.to_csv(file_path, index=False)

    loader = DataLoader()
    with pytest.raises(FileValidationException):
        loader.load_csv(file_path)
