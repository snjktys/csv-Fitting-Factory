# 本代码由 AI 辅助生成，已人工验证。
"""智能初值模块测试。"""

import numpy as np

from src.initial_guess import estimate_initial_parameters


def test_polynomial_guess_returns_ascending_coefficients() -> None:
    x = np.linspace(-2, 2, 20)
    y = 1 + 2 * x + 3 * x**2
    values, warnings = estimate_initial_parameters("polynomial", x, y, degree=2)
    assert np.allclose(values, [1, 2, 3], atol=1e-8)
    assert warnings == []


def test_sine_guess_finds_main_frequency() -> None:
    x = np.linspace(0, 4, 201)
    y = 2 * np.sin(2 * np.pi * 1.5 * x + 0.3) + 1
    values, _ = estimate_initial_parameters("sine", x, y)
    assert abs(values[1] - 1.5) < 0.05
    assert abs(values[0] - 2.0) < 0.1


def test_logistic_guess_returns_four_finite_values() -> None:
    x = np.linspace(-5, 5, 100)
    y = 1 + 10 / (1 + np.exp(-1.2 * (x - 0.5)))
    values, warnings = estimate_initial_parameters("logistic", x, y)
    assert len(values) == 4
    assert np.all(np.isfinite(values))
    assert warnings == []
