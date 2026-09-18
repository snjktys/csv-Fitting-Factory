# 本代码由 AI 辅助生成，已人工验证。
"""TXT 报告模块测试。"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.data_types import CleanedData, DatasetInfo, FitResult
from src.report_generator import build_report_text, save_report


def sample_objects(tmp_path: Path) -> tuple[DatasetInfo, CleanedData, FitResult]:
    frame = pd.DataFrame({"x": [0, 1], "y": [1, 2]})
    dataset = DatasetInfo(tmp_path / "sample.csv", "sample.csv", "utf-8", 2, ["x", "y"], frame)
    data = CleanedData(
        x=np.array([0.0, 1.0]),
        y=np.array([1.0, 2.0]),
        sigma=None,
        x_column="x",
        y_column="y",
        error_mode="none",
        sigma_column=None,
        constant_sigma=None,
        valid_rows=2,
        removed_rows=0,
    )
    result = FitResult(
        model_key="polynomial",
        model_name="1 阶多项式",
        formula="y = a0 + a1*x",
        parameter_names=["a0", "a1"],
        initial_params=np.array([1.0, 1.0]),
        parameters=np.array([1.0, 1.0]),
        parameter_errors=np.array([0.1, 0.1]),
        covariance=np.eye(2),
        predicted_y=np.array([1.0, 2.0]),
        residuals=np.zeros(2),
        r_squared=1.0,
        rmse=0.0,
        warnings=[],
        smooth_x=np.array([0.0, 1.0]),
        smooth_y=np.array([1.0, 2.0]),
    )
    return dataset, data, result


def test_report_contains_required_fields(tmp_path: Path) -> None:
    text = build_report_text(*sample_objects(tmp_path))
    for required in ["文件名", "模型", "参数", "R²", "RMSE"]:
        assert required in text


def test_report_is_saved_with_txt_suffix(tmp_path: Path) -> None:
    output = save_report("测试报告", tmp_path / "report")
    assert output.suffix == ".txt"
    assert output.read_text(encoding="utf-8-sig") == "测试报告"
