"""四种模型的智能初值估算。

智能初值只是 curve_fit 的起点，不是最终结果。用户可以在 GUI 中继续修改。
"""

from __future__ import annotations

import numpy as np

from .exceptions import DataValidationError, ParameterValidationError


def estimate_initial_parameters(
    model_key: str,
    x: np.ndarray,
    y: np.ndarray,
    degree: int | None = None,
) -> tuple[list[float], list[str]]:
    """根据模型类型返回智能初值和可能的提示信息。"""

    x_values = np.asarray(x, dtype=float)
    y_values = np.asarray(y, dtype=float)
    if x_values.size != y_values.size or x_values.size == 0:
        raise DataValidationError("X 和 Y 必须是长度相同的非空数组。")
    if not np.all(np.isfinite(x_values)) or not np.all(np.isfinite(y_values)):
        raise DataValidationError("智能初值只能使用有限数值。")

    if model_key == "polynomial":
        return _polynomial_guess(x_values, y_values, degree), []
    if model_key == "exponential":
        return _exponential_guess(x_values, y_values)
    if model_key == "sine":
        return _sine_guess(x_values, y_values)
    if model_key == "logistic":
        return _logistic_guess(x_values, y_values)
    raise ParameterValidationError(f"未知的拟合模型：{model_key}")


def _polynomial_guess(
    x: np.ndarray, y: np.ndarray, degree: int | None
) -> list[float]:
    """使用 polyfit 粗估系数，并改成 a0 到 an 的升幂顺序。"""

    if degree is None or not 1 <= degree <= 10:
        raise ParameterValidationError("多项式阶次必须在 1～10 之间。")
    try:
        descending = np.polyfit(x, y, degree)
    except (ValueError, np.linalg.LinAlgError) as exc:
        raise ParameterValidationError("多项式初值估计失败，请降低阶次。") from exc
    return descending[::-1].astype(float).tolist()


def _exponential_guess(x: np.ndarray, y: np.ndarray) -> tuple[list[float], list[str]]:
    """先估计基线，再对平移后的 Y 取对数进行直线拟合。"""

    warnings: list[str] = []
    x_range = float(np.ptp(x))
    if x_range <= 0:
        raise DataValidationError("X 数据没有范围，无法估计指数初值。")

    y_min = float(np.min(y))
    y_range = float(np.ptp(y))
    epsilon = max(y_range * 1e-3, 1e-9)
    baseline = y_min - epsilon
    shifted = y - baseline

    try:
        slope, intercept = np.polyfit(x, np.log(shifted), 1)
        amplitude = float(np.exp(intercept))
        rate = float(slope)
        if not np.all(np.isfinite([amplitude, rate, baseline])):
            raise ValueError("非有限初值")
    except (ValueError, np.linalg.LinAlgError, FloatingPointError):
        amplitude = y_range if y_range > 0 else max(abs(float(np.mean(y))), 1.0)
        rate = 1.0 / x_range
        baseline = y_min
        warnings.append("指数初值采用了安全默认值，必要时请手动调整。")

    return [amplitude, rate, baseline], warnings


def _sine_guess(x: np.ndarray, y: np.ndarray) -> tuple[list[float], list[str]]:
    """用振幅范围和 FFT 主频估计单一正弦的初值。"""

    warnings: list[str] = []
    order = np.argsort(x)
    sorted_x = x[order]
    sorted_y = y[order]
    x_range = float(np.ptp(sorted_x))
    if x_range <= 0:
        raise DataValidationError("X 数据没有范围，无法估计正弦初值。")

    offset = float(np.mean(sorted_y))
    amplitude = max(float(np.ptp(sorted_y)) / 2.0, 1e-9)
    differences = np.diff(sorted_x)
    positive_differences = differences[differences > 0]
    frequency = 1.0 / x_range

    if positive_differences.size >= 2:
        mean_step = float(np.mean(positive_differences))
        # 变异系数小于 5% 时，认为采样间隔近似均匀，可以使用普通 FFT。
        near_uniform = float(np.std(positive_differences) / mean_step) <= 0.05
        if near_uniform:
            centered_y = sorted_y - offset
            spectrum = np.abs(np.fft.rfft(centered_y))
            frequencies = np.fft.rfftfreq(sorted_y.size, d=mean_step)
            if spectrum.size > 1:
                spectrum[0] = 0.0
                dominant_index = int(np.argmax(spectrum))
                if frequencies[dominant_index] > 0:
                    frequency = float(frequencies[dominant_index])
        else:
            warnings.append("X 间隔不均匀，正弦频率使用 1/X范围 作为初值。")
    else:
        warnings.append("有效采样间隔较少，正弦频率使用安全默认值。")

    return [amplitude, frequency, 0.0, offset], warnings


def _logistic_guess(x: np.ndarray, y: np.ndarray) -> tuple[list[float], list[str]]:
    """根据上下平台、半高位置和整体趋势估计 Logistic 初值。"""

    y_min = float(np.min(y))
    y_max = float(np.max(y))
    level = y_max - y_min
    x_range = float(np.ptp(x))
    if level <= max(abs(y_max), 1.0) * 1e-9:
        raise DataValidationError("Y 数据变化太小，不适合 Logistic 拟合。")
    if x_range <= 0:
        raise DataValidationError("X 数据没有范围，无法估计 Logistic 初值。")

    half_level = y_min + level / 2.0
    midpoint = float(x[int(np.argmin(np.abs(y - half_level)))])
    correlation = float(np.corrcoef(x, y)[0, 1]) if x.size > 1 else 1.0
    direction = -1.0 if np.isfinite(correlation) and correlation < 0 else 1.0
    rate = direction * 4.0 / x_range
    return [level, rate, midpoint, y_min], []
