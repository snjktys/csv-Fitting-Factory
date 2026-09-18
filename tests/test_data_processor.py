# 本代码由 AI 辅助生成，已人工验证。
"""数据清洗与模型数据量校验测试。"""

import numpy as np
import pandas as pd
import pytest

from src.data_processor import prepare_data, validate_data_for_model
from src.exceptions import DataValidationError


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "横坐标": [2, 0, 1, "错误", 3],
            "纵坐标": [5, 1, 3, 8, np.inf],
            "误差": [0.2, 0.1, 0.1, 0.2, -1],
        }
    )


def test_prepare_data_cleans_and_sorts() -> None:
    result = prepare_data(sample_frame(), "横坐标", "纵坐标", "column", "误差")
    assert np.allclose(result.x, [0, 1, 2])
    assert np.allclose(result.y, [1, 3, 5])
    assert result.removed_rows == 2


def test_constant_error_creates_sigma_array() -> None:
    frame = pd.DataFrame({"x": [0, 1, 2], "y": [1, 2, 3]})
    result = prepare_data(frame, "x", "y", "constant", constant_sigma=0.5)
    assert np.allclose(result.sigma, [0.5, 0.5, 0.5])


def test_rejects_non_positive_constant_error() -> None:
    frame = pd.DataFrame({"x": [0, 1], "y": [1, 2]})
    with pytest.raises(DataValidationError):
        prepare_data(frame, "x", "y", "constant", constant_sigma=0)


def test_model_validation_uses_documented_point_rules() -> None:
    frame = pd.DataFrame({"x": [0, 1, 2, 3], "y": [1, 2, 3, 4]})
    data = prepare_data(frame, "x", "y")
    validate_data_for_model(data, parameter_count=3)


def test_model_validation_rejects_equal_point_and_parameter_count() -> None:
    frame = pd.DataFrame({"x": [0, 1, 2], "y": [1, 2, 3]})
    data = prepare_data(frame, "x", "y")
    with pytest.raises(DataValidationError):
        validate_data_for_model(data, parameter_count=3)
