# 本代码由 AI 辅助生成，已人工验证。
"""curve_fit 调用、参数边界、残差和评价指标。

"""

from __future__ import annotations

import warnings as python_warnings

import numpy as np
from scipy.optimize import OptimizeWarning, curve_fit

from .data_processor import validate_data_for_model
from .data_types import CleanedData, FitConfig, FitResult
from .exceptions import FittingError, ParameterValidationError
from .fitting_models import ModelSpec, get_model_spec


def calculate_metrics(
    observed_y: np.ndarray, predicted_y: np.ndarray
) -> tuple[np.ndarray, float | None, float]:
    """计算残差、R² 和 RMSE。

    当所有 Y 完全相同时，SST 为 0，此时 R² 没有定义，返回 None。
    """

    observed = np.asarray(observed_y, dtype=float)
    predicted = np.asarray(predicted_y, dtype=float)
    residuals = observed - predicted
    squared_error_sum = float(np.sum(np.square(residuals)))
    total_sum = float(np.sum(np.square(observed - np.mean(observed))))
    r_squared = None if np.isclose(total_sum, 0.0) else 1.0 - squared_error_sum / total_sum
    rmse = float(np.sqrt(np.mean(np.square(residuals))))
    return residuals, r_squared, rmse


def fit_curve(data: CleanedData, config: FitConfig) -> FitResult:
    """按照配置完成曲线拟合并返回统一结果对象。"""

    spec = get_model_spec(config.model_key, config.polynomial_degree)
    parameter_count = len(spec.parameter_names)
    validate_data_for_model(data, parameter_count)
    initial_parameters = _validate_initial_parameters(config.initial_params, parameter_count)
    bounds = _parameter_bounds(spec, data.x)
    result_warnings: list[str] = []

    if config.model_key == "polynomial" and (config.polynomial_degree or 0) >= 6:
        result_warnings.append("高阶多项式可能过拟合或在数据边缘产生振荡。")

    try:
        with python_warnings.catch_warnings(record=True) as caught:
            python_warnings.simplefilter("always", OptimizeWarning)
            parameters, covariance = curve_fit(
                spec.function,
                data.x,
                data.y,
                p0=initial_parameters,
                sigma=data.sigma,
                absolute_sigma=data.sigma is not None,
                bounds=bounds,
                maxfev=config.max_function_evaluations,
            )
            if any(issubclass(item.category, OptimizeWarning) for item in caught):
                result_warnings.append("参数协方差无法可靠估计，请谨慎解释参数误差。")
    except (RuntimeError, ValueError, FloatingPointError, OverflowError) as exc:
        detail = str(exc).strip()
        if config.model_key == "exponential":
            message = "指数拟合失败，请使用智能初值，或缩放 X 数据后重试。"
        else:
            message = "拟合没有收敛，请使用智能初值或调整参数后重试。"
        if detail:
            message += f"（{detail}）"
        raise FittingError(message) from exc

    try:
        predicted_y = np.asarray(spec.function(data.x, *parameters), dtype=float)
        smooth_x = np.linspace(float(np.min(data.x)), float(np.max(data.x)), 500)
        smooth_y = np.asarray(spec.function(smooth_x, *parameters), dtype=float)
    except (FloatingPointError, OverflowError, ValueError) as exc:
        raise FittingError("拟合参数会导致模型计算溢出，请调整初值或数据尺度。") from exc

    if not np.all(np.isfinite(parameters)) or not np.all(np.isfinite(predicted_y)):
        raise FittingError("拟合结果包含无效数值，请调整初值或数据尺度。")

    residuals, r_squared, rmse = calculate_metrics(data.y, predicted_y)
    if covariance.shape != (parameter_count, parameter_count) or not np.all(
        np.isfinite(covariance)
    ):
        parameter_errors = np.full(parameter_count, np.nan)
        if "参数协方差无法可靠估计，请谨慎解释参数误差。" not in result_warnings:
            result_warnings.append("参数协方差无法可靠估计，请谨慎解释参数误差。")
    else:
        parameter_errors = np.sqrt(np.maximum(np.diag(covariance), 0.0))

    return FitResult(
        model_key=config.model_key,
        model_name=spec.display_name,
        formula=spec.formula,
        parameter_names=list(spec.parameter_names),
        initial_params=initial_parameters,
        parameters=np.asarray(parameters, dtype=float),
        parameter_errors=np.asarray(parameter_errors, dtype=float),
        covariance=np.asarray(covariance, dtype=float),
        predicted_y=predicted_y,
        residuals=residuals,
        r_squared=r_squared,
        rmse=rmse,
        warnings=result_warnings,
        smooth_x=smooth_x,
        smooth_y=smooth_y,
    )


def _validate_initial_parameters(values: list[float], count: int) -> np.ndarray:
    """检查参数数量，并转换为有限浮点数组。"""

    if len(values) != count:
        raise ParameterValidationError(f"当前模型需要 {count} 个初始参数。")
    try:
        parameters = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ParameterValidationError("所有初始参数都必须是数字。") from exc
    if not np.all(np.isfinite(parameters)):
        raise ParameterValidationError("所有初始参数都必须是有限数值。")
    return parameters


def _parameter_bounds(spec: ModelSpec, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """集中定义模型参数边界，避免边界散落在 GUI 中。"""

    count = len(spec.parameter_names)
    lower = np.full(count, -np.inf)
    upper = np.full(count, np.inf)

    if spec.key == "exponential":
        max_abs_x = max(float(np.max(np.abs(x))), np.finfo(float).eps)
        rate_limit = 100.0 / max_abs_x
        lower[1], upper[1] = -rate_limit, rate_limit
    elif spec.key == "sine":
        x_range = max(float(np.ptp(x)), np.finfo(float).eps)
        unique_x = np.unique(x)
        steps = np.diff(unique_x)
        positive_steps = steps[steps > 0]
        min_step = float(np.min(positive_steps)) if positive_steps.size else x_range
        upper_frequency = max(1.0 / (2.0 * min_step), 10.0 / x_range)
        lower[1], upper[1] = np.finfo(float).eps, upper_frequency
    elif spec.key == "logistic":
        lower[0] = np.finfo(float).eps

    return lower, upper
