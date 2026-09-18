# 本代码由 AI 辅助生成，已人工验证。
"""用有放回重采样评估拟合参数的不确定性。"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from .data_types import CleanedData, FitConfig
from .exceptions import FittingError, FittingFactoryError, ParameterValidationError
from .fitting_engine import fit_curve


def bootstrap_parameters(
    data: CleanedData,
    config: FitConfig,
    iterations: int = 1_000,
    seed: int | None = None,
) -> np.ndarray:
    """重复有放回抽取数据行，返回每次成功拟合得到的参数。"""

    if iterations < 1:
        raise ParameterValidationError("蒙特卡洛重采样次数必须大于 0。")

    rng = np.random.default_rng(seed)
    samples: list[np.ndarray] = []
    for _ in range(iterations):
        indices = rng.integers(0, data.x.size, data.x.size)
        sample = replace(
            data,
            x=data.x[indices],
            y=data.y[indices],
            sigma=None if data.sigma is None else data.sigma[indices],
        )
        try:
            samples.append(fit_curve(sample, config).parameters)
        except FittingFactoryError:
            continue

    if not samples:
        raise FittingError("蒙特卡洛重采样全部失败，请检查数据或拟合参数。")
    return np.vstack(samples)
