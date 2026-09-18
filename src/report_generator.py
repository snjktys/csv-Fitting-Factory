# 本代码由 AI 辅助生成，已人工验证。
"""TXT 拟合报告生成和保存。

"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np

from .data_types import CleanedData, DatasetInfo, FitResult
from .exceptions import ReportError


def build_report_text(
    dataset: DatasetInfo, data: CleanedData, result: FitResult
) -> str:
    """根据当前数据和拟合结果生成可直接保存的中文报告文本。"""

    error_source = _error_source_text(data)
    r_squared = "N/A（Y 数据没有变化）" if result.r_squared is None else f"{result.r_squared:.8g}"
    parameter_lines: list[str] = []
    for name, value, error in zip(
        result.parameter_names, result.parameters, result.parameter_errors, strict=True
    ):
        error_text = "N/A" if not np.isfinite(error) else f"{error:.8g}"
        parameter_lines.append(f"{name} = {value:.8g}，标准误差 = {error_text}")

    warning_lines = result.warnings or ["无"]
    return "\n".join(
        [
            "CSV 数据曲线拟合报告",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "一、数据文件",
            f"文件名：{dataset.file_name}",
            f"文件路径：{dataset.file_path}",
            f"文件编码：{dataset.encoding}",
            f"X 列：{data.x_column}",
            f"Y 列：{data.y_column}",
            f"误差模式：{_error_mode_text(data.error_mode)}",
            f"误差来源：{error_source}",
            f"原始行数：{dataset.original_rows}",
            f"有效行数：{data.valid_rows}",
            f"删除行数：{data.removed_rows}",
            "",
            "二、拟合设置",
            f"模型：{result.model_name}",
            f"公式：{result.formula}",
            "初始参数：" + ", ".join(f"{value:.8g}" for value in result.initial_params),
            "",
            "三、拟合结果",
            *parameter_lines,
            f"R²：{r_squared}",
            f"RMSE：{result.rmse:.8g}",
            "",
            "四、警告与说明",
            *[f"- {message}" for message in warning_lines],
            "",
        ]
    )


def save_report(report_text: str, output_path: str | Path) -> Path:
    """使用 UTF-8-SIG 编码保存报告，方便 Windows 记事本打开中文。"""

    path = Path(output_path)
    if path.suffix.lower() != ".txt":
        path = path.with_suffix(".txt")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report_text, encoding="utf-8-sig")
    except OSError as exc:
        raise ReportError(f"报告保存失败，请更换保存位置：{exc}") from exc
    return path.resolve()


def suggested_report_name(dataset: DatasetInfo, result: FitResult) -> str:
    """生成保存对话框使用的默认报告文件名。"""

    safe_model_name = result.model_name.replace(" ", "_")
    return f"{dataset.file_path.stem}_{safe_model_name}_拟合报告.txt"


def _error_mode_text(error_mode: str) -> str:
    """把内部误差模式转换为报告中的中文名称。"""

    return {"none": "无误差", "column": "CSV 误差列", "constant": "统一误差值"}.get(error_mode, error_mode)


def _error_source_text(data: CleanedData) -> str:
    """说明报告所用误差数据的具体来源。"""

    if data.error_mode == "column":
        return data.sigma_column or "未指定"
    if data.error_mode == "constant":
        return f"统一误差 {data.constant_sigma:.8g}" if data.constant_sigma is not None else "未指定"
    return "无"
