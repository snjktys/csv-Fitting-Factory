"""随机与异常 CSV 场景测试。

这些测试模拟用户实际可能导入的不同文件，覆盖课程设计要求中的正常、边界和异常情况。
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.csv_handler import load_csv
from src.data_processor import prepare_data, validate_data_for_model
from src.data_types import FitConfig
from src.exceptions import CsvReadError, DataValidationError, FittingError
from src.fitting_engine import fit_curve
from src.initial_guess import estimate_initial_parameters


def _fit_frame(
    frame: pd.DataFrame,
    model_key: str,
    degree: int | None = None,
    error_mode: str = "none",
    sigma_column: str | None = None,
    constant_sigma: float | None = None,
):
    """将 DataFrame 走过与 GUI 相同的读取后核心流程。"""

    data = prepare_data(
        frame,
        frame.columns[0],
        frame.columns[1],
        error_mode,
        sigma_column,
        constant_sigma,
    )
    initial, warnings = estimate_initial_parameters(model_key, data.x, data.y, degree)
    result = fit_curve(data, FitConfig(model_key, degree, initial))
    return data, result, warnings


@pytest.mark.parametrize("seed", [3, 17, 42, 101, 2026])
def test_random_polynomial_data_with_outliers_and_missing_rows(seed: int) -> None:
    """随机生成带轻微噪声和少量异常行的多项式数据。"""

    rng = np.random.default_rng(seed)
    x = np.linspace(-5, 5, 40)
    y = 1.5 - 0.8 * x + 0.35 * x**2 + rng.normal(0, 0.12, x.size)
    frame = pd.DataFrame({"自变量": x, "因变量": y, "测量误差": 0.12})
    # Pandas 3 不允许把字符串直接写入已确定为 float64 的列，先转成 object。
    frame["因变量"] = frame["因变量"].astype(object)
    frame.loc[2, "因变量"] = "缺失"
    frame.loc[7, "自变量"] = np.inf
    frame.loc[13, "因变量"] = np.nan

    data, result, _ = _fit_frame(frame, "polynomial", 2, "column", "测量误差")

    assert data.valid_rows == 37
    assert data.removed_rows == 3
    assert result.r_squared is not None and result.r_squared > 0.97
    assert np.all(np.isfinite(result.parameters))


@pytest.mark.parametrize("seed", [5, 23, 88])
def test_random_exponential_data_without_error_column(seed: int) -> None:
    """随机生成不同噪声水平的指数数据，验证无误差模式。"""

    rng = np.random.default_rng(seed)
    x = np.linspace(0, 4.5, 35)
    y = 2.0 * np.exp(0.42 * x) + 0.8 + rng.normal(0, 0.12, x.size)
    frame = pd.DataFrame({"x": x, "y": y})

    data, result, _ = _fit_frame(frame, "exponential")

    assert data.sigma is None
    assert result.r_squared is not None and result.r_squared > 0.98


def test_random_sine_data_with_uniform_error() -> None:
    """随机相位的正弦数据验证统一误差值模式和 FFT 初值。"""

    rng = np.random.default_rng(314)
    x = np.linspace(0, 6, 241)
    y = 1.8 * np.sin(2 * np.pi * 0.75 * x + 0.45) - 0.3
    y += rng.normal(0, 0.04, x.size)
    frame = pd.DataFrame({"时间": x, "信号": y})

    data, result, _ = _fit_frame(frame, "sine", error_mode="constant", constant_sigma=0.04)

    assert data.sigma is not None and np.allclose(data.sigma, 0.04)
    assert result.r_squared is not None and result.r_squared > 0.99


def test_random_logistic_data_with_unsorted_rows_and_duplicate_x() -> None:
    """乱序且含重复 X 的 Logistic 数据应能正常排序并拟合。"""

    rng = np.random.default_rng(2718)
    x = np.linspace(-6, 6, 50)
    y = 1.2 + 8.5 / (1 + np.exp(-1.1 * (x - 0.8)))
    y += rng.normal(0, 0.05, x.size)
    frame = pd.DataFrame({"输入量": x, "输出量": y, "误差": 0.05})
    frame = pd.concat([frame, frame.iloc[[10, 20]]], ignore_index=True)
    frame = frame.sample(frac=1.0, random_state=99).reset_index(drop=True)

    data, result, _ = _fit_frame(frame, "logistic", error_mode="column", sigma_column="误差")

    assert np.all(np.diff(data.x) >= 0)
    assert data.valid_rows == 52
    assert result.r_squared is not None and result.r_squared > 0.99


def test_gb18030_chinese_csv_is_read(tmp_path: Path) -> None:
    """验证中文 Windows 常见 GB18030 编码。"""

    file_path = tmp_path / "中文编码.csv"
    file_path.write_text("横坐标,纵坐标\n0,1\n1,2\n2,3\n", encoding="gb18030")
    dataset = load_csv(file_path)
    assert dataset.encoding == "gb18030"
    assert dataset.column_names == ["横坐标", "纵坐标"]


def test_constant_y_returns_undefined_r_squared() -> None:
    frame = pd.DataFrame({"x": np.arange(8), "y": np.ones(8) * 5})
    data = prepare_data(frame, "x", "y")
    with pytest.raises(DataValidationError, match="Logistic"):
        estimate_initial_parameters("logistic", data.x, data.y)


def test_duplicate_x_is_allowed_when_unique_count_is_enough() -> None:
    frame = pd.DataFrame({"x": [0, 0, 1, 1, 2, 2, 3], "y": [1, 1, 2, 2, 3, 3, 4]})
    data = prepare_data(frame, "x", "y")
    validate_data_for_model(data, 2)


def test_insufficient_unique_x_is_rejected() -> None:
    frame = pd.DataFrame({"x": [0, 0, 0, 1], "y": [1, 1, 1, 2]})
    data = prepare_data(frame, "x", "y")
    with pytest.raises(DataValidationError, match="不同的 X"):
        validate_data_for_model(data, 3)


def test_invalid_error_values_are_removed() -> None:
    frame = pd.DataFrame({"x": [0, 1, 2, 3], "y": [1, 2, 3, 4], "e": [0.1, 0, -1, np.nan]})
    data = prepare_data(frame, "x", "y", "column", "e")
    assert data.valid_rows == 1
    assert data.removed_rows == 3


def test_unknown_encoding_and_malformed_csv_are_reported(tmp_path: Path) -> None:
    file_path = tmp_path / "malformed.csv"
    file_path.write_bytes(b"\xff\xfe\xfa\xfb")
    with pytest.raises(CsvReadError):
        load_csv(file_path)


def test_extreme_exponential_initial_value_fails_clearly() -> None:
    frame = pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0], "y": [1.0, 2.0, 4.0, 8.0]})
    data = prepare_data(frame, "x", "y")
    with pytest.raises((FittingError, DataValidationError, ValueError)):
        fit_curve(data, FitConfig("exponential", None, [1.0, 1e9, 0.0]))


def test_persisted_gb18030_file_can_be_loaded() -> None:
    """验证落盘后的 GB18030 中文测试文件，而不仅是内存字符串。"""

    path = Path(__file__).parent / "test_data" / "encoding_gb18030.csv"
    dataset = load_csv(path)
    assert dataset.encoding == "gb18030"


def test_persisted_malformed_file_is_rejected() -> None:
    """验证落盘后的非法字节文件会返回业务异常。"""

    path = Path(__file__).parent / "test_data" / "malformed_bytes.csv"
    with pytest.raises(CsvReadError):
        load_csv(path)
