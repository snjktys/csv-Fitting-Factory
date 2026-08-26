"""拟合引擎和评价指标测试。"""

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("scipy")

from src.csv_handler import load_csv
from src.data_processor import prepare_data
from src.data_types import FitConfig
from src.fitting_engine import calculate_metrics, fit_curve
from src.initial_guess import estimate_initial_parameters


@pytest.mark.parametrize(
    ("file_name", "model_key", "degree"),
    [
        ("polynomial_sample.csv", "polynomial", 2),
        ("exponential_sample.csv", "exponential", None),
        ("sine_sample.csv", "sine", None),
        ("logistic_sample.csv", "logistic", None),
    ],
)
def test_sample_data_can_be_fitted(file_name: str, model_key: str, degree: int | None) -> None:
    path = Path(__file__).parents[1] / "data" / file_name
    dataset = load_csv(path)
    x_column, y_column = dataset.column_names[:2]
    data = prepare_data(dataset.dataframe, x_column, y_column, "column", "error")
    initial, _ = estimate_initial_parameters(model_key, data.x, data.y, degree)
    result = fit_curve(data, FitConfig(model_key, degree, initial))

    assert np.all(np.isfinite(result.parameters))
    assert result.rmse >= 0
    assert result.r_squared is not None
    assert result.r_squared > 0.95


def test_metrics_return_none_r_squared_for_constant_y() -> None:
    residuals, r_squared, rmse = calculate_metrics(
        np.array([3.0, 3.0, 3.0]), np.array([3.0, 3.0, 3.0])
    )
    assert np.allclose(residuals, 0)
    assert r_squared is None
    assert rmse == 0
