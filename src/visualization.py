"""Matplotlib 拟合图和残差图绘制。

"""

from __future__ import annotations

import numpy as np
from matplotlib import font_manager, rcParams
from matplotlib.figure import Figure

from .data_types import CleanedData, FitResult


def configure_chinese_font() -> str | None:
    """选择系统中可用的中文字体，避免图表中文显示成方框。

    Windows 通常提供 Microsoft YaHei 或 SimHei；如果系统没有这些字体，函数
    返回 None，Matplotlib 会继续使用默认字体。
    """

    available_names = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS"):
        if candidate in available_names:
            rcParams["font.sans-serif"] = [candidate, "DejaVu Sans"]
            rcParams["axes.unicode_minus"] = False
            return candidate
    return None


def create_figure(language: str = "zh") -> Figure:
    """创建包含拟合图和残差图的 Figure。"""

    configure_chinese_font()
    figure = Figure(figsize=(8.5, 7.0), dpi=100)
    _reset_figure(figure, language)
    return figure


def draw_fit_result(
    figure: Figure,
    data: CleanedData,
    result: FitResult,
    language: str = "zh",
    model_name: str | None = None,
) -> None:
    """清空 Figure，并绘制原始数据、误差棒、拟合曲线和残差。"""

    figure.clear()
    fit_axis = figure.add_subplot(211)
    residual_axis = figure.add_subplot(212)

    labels = {
        "zh": ("原始数据", "原始数据 / 误差棒", "拟合结果", "残差图", "残差"),
        "en": ("Raw Data", "Raw Data / Error Bars", "Fitting Result", "Residual Plot", "Residual"),
    }[language]
    display_model_name = model_name or result.model_name
    if data.sigma is None:
        fit_axis.scatter(data.x, data.y, color="#2f73c5", label=labels[0], zorder=3)
    else:
        fit_axis.errorbar(
            data.x,
            data.y,
            yerr=data.sigma,
            fmt="o",
            color="#2f73c5",
            ecolor="#5f91d0",
            capsize=3,
            label=labels[1],
            zorder=3,
        )
    fit_axis.plot(
        result.smooth_x,
        result.smooth_y,
        color="#d94b4b",
        linewidth=2.2,
        label=display_model_name,
    )
    fit_axis.set_title(f"{labels[2]} - {display_model_name}")
    fit_axis.set_xlabel(data.x_column)
    fit_axis.set_ylabel(data.y_column)
    fit_axis.grid(alpha=0.25)
    fit_axis.legend()

    residual_axis.scatter(data.x, result.residuals, color="#8659b5", s=28)
    residual_axis.axhline(0.0, color="#333333", linestyle="--", linewidth=1.2)
    residual_axis.set_title(labels[3])
    residual_axis.set_xlabel(data.x_column)
    residual_axis.set_ylabel(labels[4])
    residual_axis.grid(alpha=0.25)
    figure.tight_layout(pad=2.0)


def create_parameter_histograms(
    samples: np.ndarray, parameter_names: list[str], language: str = "zh"
) -> Figure:
    """绘制蒙特卡洛参数样本的直方图。"""

    # 本函数由 AI 生成，已人工验证；

    configure_chinese_font()
    columns = 2 if len(parameter_names) > 1 else 1
    rows = (len(parameter_names) + columns - 1) // columns
    figure = Figure(figsize=(8, max(3, rows * 2.6)), dpi=100)
    value_label, count_label, title = {
        "zh": ("参数值", "次数", f"蒙特卡洛参数分布（成功 {len(samples)} 次）"),
        "en": ("Parameter Value", "Count", f"Monte Carlo Parameter Distributions ({len(samples)} successful)"),
    }[language]
    for index, name in enumerate(parameter_names):
        axis = figure.add_subplot(rows, columns, index + 1)
        axis.hist(samples[:, index], bins=30, color="#2f73c5", edgecolor="white")
        axis.set_title(name)
        axis.set_xlabel(value_label)
        axis.set_ylabel(count_label)
        axis.grid(axis="y", alpha=0.2)
    figure.suptitle(title)
    figure.tight_layout(pad=2.0)
    return figure


def clear_figure(figure: Figure, language: str = "zh") -> None:
    """恢复没有拟合结果时的空图提示。"""

    _reset_figure(figure, language)


def _reset_figure(figure: Figure, language: str = "zh") -> None:
    """清空图形并恢复两个空状态子图。"""

    figure.clear()
    top_axis = figure.add_subplot(211)
    bottom_axis = figure.add_subplot(212)
    _draw_empty_axes(top_axis, bottom_axis, language)
    figure.tight_layout(pad=2.0)


def _draw_empty_axes(top_axis, bottom_axis, language: str = "zh") -> None:
    """在空图中提供下一步操作提示。"""

    texts = {
        "zh": ("拟合结果图", "请先导入 CSV 并执行拟合", "残差图", "拟合成功后显示残差"),
        "en": ("Fitting Result", "Open a CSV file and run fitting", "Residual Plot", "Residuals appear after a successful fit"),
    }[language]
    top_axis.set_title(texts[0])
    top_axis.text(
        0.5,
        0.5,
        texts[1],
        ha="center",
        va="center",
        transform=top_axis.transAxes,
    )
    top_axis.set_xticks([])
    top_axis.set_yticks([])
    bottom_axis.set_title(texts[2])
    bottom_axis.text(
        0.5,
        0.5,
        texts[3],
        ha="center",
        va="center",
        transform=bottom_axis.transAxes,
    )
    bottom_axis.set_xticks([])
    bottom_axis.set_yticks([])
