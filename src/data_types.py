# 本代码由 AI 辅助生成，已人工验证。
"""模块之间传递的数据对象。

使用 dataclass 可以让每个字段的含义清晰可见，避免使用难以理解的长元组。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(slots=True)
class DatasetInfo:
    """保存 CSV 文件本身的信息和原始表格。"""

    file_path: Path
    file_name: str
    encoding: str
    original_rows: int
    column_names: list[str]
    dataframe: pd.DataFrame = field(repr=False)


@dataclass(slots=True)
class CleanedData:
    """保存转换、清洗并按 X 排序后的拟合数据。"""

    x: np.ndarray
    y: np.ndarray
    sigma: np.ndarray | None
    x_column: str
    y_column: str
    error_mode: str
    sigma_column: str | None
    constant_sigma: float | None
    valid_rows: int
    removed_rows: int


@dataclass(slots=True)
class FitConfig:
    """保存一次拟合使用的模型和参数配置。"""

    model_key: str
    polynomial_degree: int | None
    initial_params: list[float]
    max_function_evaluations: int = 20_000


@dataclass(slots=True)
class FitResult:
    """保存一次成功拟合产生的全部结果。"""

    model_key: str
    model_name: str
    formula: str
    parameter_names: list[str]
    initial_params: np.ndarray
    parameters: np.ndarray
    parameter_errors: np.ndarray
    covariance: np.ndarray
    predicted_y: np.ndarray
    residuals: np.ndarray
    r_squared: float | None
    rmse: float
    warnings: list[str]
    smooth_x: np.ndarray
    smooth_y: np.ndarray
