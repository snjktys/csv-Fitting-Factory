"""蒙特卡洛参数重采样测试。"""

from pathlib import Path

import numpy as np
import pytest

from src.csv_handler import load_csv
from src.data_processor import prepare_data
from src.data_types import FitConfig
from src.fitting_engine import fit_curve
from src.initial_guess import estimate_initial_parameters
from src.exceptions import ParameterValidationError
from src.monte_carlo import bootstrap_parameters
from src.visualization import create_parameter_histograms


def test_bootstrap_returns_parameter_samples() -> None:
    # 本测试函数由 AI 生成，已人工验证；
    dataset = load_csv(Path("data/polynomial_sample.csv"))
    data = prepare_data(dataset.dataframe, "x", "y", "column", "error")
    initial, _ = estimate_initial_parameters("polynomial", data.x, data.y, 2)
    result = fit_curve(data, FitConfig("polynomial", 2, initial))

    samples = bootstrap_parameters(
        data, FitConfig("polynomial", 2, result.parameters.tolist()), 20, seed=1
    )

    assert samples.shape == (20, 3)
    assert np.all(np.isfinite(samples))


def test_parameter_histograms_have_one_axis_per_parameter() -> None:
    # 本测试函数由 AI 生成，已人工验证；
    figure = create_parameter_histograms(np.ones((10, 3)), ["a0", "a1", "a2"])
    assert len(figure.axes) == 3


def test_bootstrap_rejects_invalid_iteration_count() -> None:
    # 本测试函数由 AI 生成，已人工验证；
    dataset = load_csv(Path("data/polynomial_sample.csv"))
    data = prepare_data(dataset.dataframe, "x", "y", "none")
    with pytest.raises(ParameterValidationError):
        bootstrap_parameters(data, FitConfig("polynomial", 2, [1, 1, 1]), 0)
