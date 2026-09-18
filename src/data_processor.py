# 本代码由 AI 辅助生成，已人工验证。
"""拟合数据选择、转换、清洗和数量校验。

"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from .data_types import CleanedData
from .exceptions import DataValidationError

ErrorMode = Literal["none", "column", "constant"]


def prepare_data(
    dataframe: pd.DataFrame,
    x_column: str,
    y_column: str,
    error_mode: ErrorMode = "none",
    sigma_column: str | None = None,
    constant_sigma: float | None = None,
) -> CleanedData:
    """将用户选择的列转换成可用于拟合的有限浮点数组。"""

    if x_column not in dataframe.columns or y_column not in dataframe.columns:
        raise DataValidationError("选择的 X 或 Y 列不存在。")
    if x_column == y_column:
        raise DataValidationError("X 列和 Y 列不能选择同一列。")
    if error_mode not in {"none", "column", "constant"}:
        raise DataValidationError("未知的误差模式。")

    selected = pd.DataFrame(
        {
            "x": pd.to_numeric(dataframe[x_column], errors="coerce"),
            "y": pd.to_numeric(dataframe[y_column], errors="coerce"),
        }
    )

    normalized_sigma_column: str | None = None
    normalized_constant_sigma: float | None = None

    if error_mode == "column":
        if not sigma_column or sigma_column not in dataframe.columns:
            raise DataValidationError("请选择有效的 CSV 误差列。")
        selected["sigma"] = pd.to_numeric(dataframe[sigma_column], errors="coerce")
        normalized_sigma_column = sigma_column
    elif error_mode == "constant":
        try:
            normalized_constant_sigma = float(constant_sigma)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise DataValidationError("统一误差值必须是数字。") from exc
        if not np.isfinite(normalized_constant_sigma) or normalized_constant_sigma <= 0:
            raise DataValidationError("统一误差值必须是有限正数。")
        selected["sigma"] = normalized_constant_sigma

    # 无穷值对 curve_fit 没有意义，先转换为缺失值，再统一删除对应行。
    selected = selected.replace([np.inf, -np.inf], np.nan)
    if "sigma" in selected.columns:
        selected.loc[selected["sigma"] <= 0, "sigma"] = np.nan
    original_rows = len(selected)
    selected = selected.dropna().sort_values("x", kind="mergesort")

    if selected.empty:
        raise DataValidationError("清洗后没有有效数值，请更换数据列或修正 CSV。")

    sigma = (
        selected["sigma"].to_numpy(dtype=float)
        if "sigma" in selected.columns
        else None
    )
    return CleanedData(
        x=selected["x"].to_numpy(dtype=float),
        y=selected["y"].to_numpy(dtype=float),
        sigma=sigma,
        x_column=x_column,
        y_column=y_column,
        error_mode=error_mode,
        sigma_column=normalized_sigma_column,
        constant_sigma=normalized_constant_sigma,
        valid_rows=len(selected),
        removed_rows=original_rows - len(selected),
    )


def validate_data_for_model(data: CleanedData, parameter_count: int) -> None:
    """按照系统设计文档校验数据点数量。

    总点数必须大于参数数；不同 X 的数量必须不少于参数数。
    """

    if parameter_count <= 0:
        raise DataValidationError("模型参数数量必须大于 0。")
    if data.valid_rows <= parameter_count:
        raise DataValidationError(
            f"有效数据点只有 {data.valid_rows} 个，必须多于模型的 "
            f"{parameter_count} 个参数。"
        )
    unique_x_count = int(np.unique(data.x).size)
    if unique_x_count < parameter_count:
        raise DataValidationError(
            f"不同的 X 只有 {unique_x_count} 个，至少需要 {parameter_count} 个。"
        )
    if np.ptp(data.x) == 0:
        raise DataValidationError("X 数据没有变化，无法进行曲线拟合。")
