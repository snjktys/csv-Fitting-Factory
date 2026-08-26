"""可视化模块的无界面测试。"""

import matplotlib
import numpy as np

matplotlib.use("Agg")

from src.data_types import CleanedData, FitResult
from src.visualization import configure_chinese_font, create_figure, draw_fit_result


def test_figure_contains_two_axes_after_drawing() -> None:
    data = CleanedData(
        x=np.array([0.0, 1.0, 2.0]),
        y=np.array([1.0, 2.0, 3.0]),
        sigma=np.array([0.1, 0.1, 0.1]),
        x_column="x",
        y_column="y",
        error_mode="constant",
        sigma_column=None,
        constant_sigma=0.1,
        valid_rows=3,
        removed_rows=0,
    )
    result = FitResult(
        model_key="polynomial",
        model_name="1 阶多项式",
        formula="y=a0+a1*x",
        parameter_names=["a0", "a1"],
        initial_params=np.array([1.0, 1.0]),
        parameters=np.array([1.0, 1.0]),
        parameter_errors=np.array([0.1, 0.1]),
        covariance=np.eye(2),
        predicted_y=np.array([1.0, 2.0, 3.0]),
        residuals=np.zeros(3),
        r_squared=1.0,
        rmse=0.0,
        warnings=[],
        smooth_x=np.linspace(0, 2, 10),
        smooth_y=np.linspace(1, 3, 10),
    )
    figure = create_figure()
    draw_fit_result(figure, data, result)
    assert len(figure.axes) == 2


def test_chinese_font_configuration_does_not_fail() -> None:
    """系统有无中文字体都不应导致程序崩溃。"""

    selected = configure_chinese_font()
    assert selected is None or isinstance(selected, str)
