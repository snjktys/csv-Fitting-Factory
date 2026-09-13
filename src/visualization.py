"""Matplotlib 拟合图和残差图绘制。

本模块由 AI 辅助生成，已通过后续自动化测试，仍需学生本人理解与复核。
"""

# 本模块由 AI 生成，已通过自动化测试和运行检查，需学生本人最终验证。

from __future__ import annotations

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


def create_figure() -> Figure:
    """创建包含拟合图和残差图的 Figure。"""

    configure_chinese_font()
    figure = Figure(figsize=(8.5, 7.0), dpi=100)
    _reset_figure(figure)
    return figure


def draw_fit_result(figure: Figure, data: CleanedData, result: FitResult) -> None:
    """清空 Figure，并绘制原始数据、误差棒、拟合曲线和残差。"""

    figure.clear()
    fit_axis = figure.add_subplot(211)
    residual_axis = figure.add_subplot(212)

    if data.sigma is None:
        fit_axis.scatter(data.x, data.y, color="#2f73c5", label="原始数据", zorder=3)
    else:
        fit_axis.errorbar(
            data.x,
            data.y,
            yerr=data.sigma,
            fmt="o",
            color="#2f73c5",
            ecolor="#5f91d0",
            capsize=3,
            label="原始数据 / 误差棒",
            zorder=3,
        )
    fit_axis.plot(
        result.smooth_x,
        result.smooth_y,
        color="#d94b4b",
        linewidth=2.2,
        label=result.model_name,
    )
    fit_axis.set_title(f"拟合结果 - {result.model_name}")
    fit_axis.set_xlabel(data.x_column)
    fit_axis.set_ylabel(data.y_column)
    fit_axis.grid(alpha=0.25)
    fit_axis.legend()

    residual_axis.scatter(data.x, result.residuals, color="#8659b5", s=28)
    residual_axis.axhline(0.0, color="#333333", linestyle="--", linewidth=1.2)
    residual_axis.set_title("残差图")
    residual_axis.set_xlabel(data.x_column)
    residual_axis.set_ylabel("残差")
    residual_axis.grid(alpha=0.25)
    figure.tight_layout(pad=2.0)


def clear_figure(figure: Figure) -> None:
    """恢复没有拟合结果时的空图提示。"""

    _reset_figure(figure)


def _reset_figure(figure: Figure) -> None:
    """清空图形并恢复两个空状态子图。"""

    figure.clear()
    top_axis = figure.add_subplot(211)
    bottom_axis = figure.add_subplot(212)
    _draw_empty_axes(top_axis, bottom_axis)
    figure.tight_layout(pad=2.0)


def _draw_empty_axes(top_axis, bottom_axis) -> None:
    """在空图中提供下一步操作提示。"""

    top_axis.set_title("拟合结果图")
    top_axis.text(
        0.5,
        0.5,
        "请先导入 CSV 并执行拟合",
        ha="center",
        va="center",
        transform=top_axis.transAxes,
    )
    top_axis.set_xticks([])
    top_axis.set_yticks([])
    bottom_axis.set_title("残差图")
    bottom_axis.text(
        0.5,
        0.5,
        "拟合成功后显示残差",
        ha="center",
        va="center",
        transform=bottom_axis.transAxes,
    )
    bottom_axis.set_xticks([])
    bottom_axis.set_yticks([])
