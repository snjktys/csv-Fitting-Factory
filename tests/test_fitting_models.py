# 本代码由 AI 辅助生成，已人工验证。
"""数学模型模块测试。"""

import numpy as np
import pytest

from src.exceptions import ParameterValidationError
from src.fitting_models import (
    exponential_model,
    get_model_spec,
    logistic_model,
    make_polynomial_model,
    sine_model,
)


def test_polynomial_uses_ascending_coefficients() -> None:
    """a0、a1、a2 应分别代表常数、一次和二次项。"""

    model = make_polynomial_model(2)
    result = model(np.array([0.0, 1.0, 2.0]), 1.0, 2.0, 3.0)
    assert np.allclose(result, [1.0, 6.0, 17.0])


def test_polynomial_rejects_invalid_degree() -> None:
    with pytest.raises(ParameterValidationError):
        make_polynomial_model(0)


def test_exponential_formula() -> None:
    x = np.array([0.0, 1.0])
    assert np.allclose(exponential_model(x, 2.0, 0.5, 1.0), 2 * np.exp(0.5 * x) + 1)


def test_sine_formula() -> None:
    x = np.array([0.0, 0.25])
    result = sine_model(x, 2.0, 1.0, 0.0, 3.0)
    assert np.allclose(result, [3.0, 5.0])


def test_logistic_midpoint() -> None:
    result = logistic_model(np.array([5.0]), 10.0, 2.0, 5.0, 1.0)
    assert np.allclose(result, [6.0])


def test_model_spec_contains_expected_parameters() -> None:
    spec = get_model_spec("logistic")
    assert spec.parameter_names == ("L", "k", "x0", "c")
    assert spec.parameter_descriptions == (
        "上下平台差值",
        "增长/下降速率（正值上升，负值下降）",
        "曲线中点的 x 值",
        "下平台基线",
    )


def test_polynomial_spec_explains_each_coefficient() -> None:
    spec = get_model_spec("polynomial", degree=2)
    assert spec.formula == "y = a0 + a1*x^1 + a2*x^2"
    assert spec.parameter_names == ("a0", "a1", "a2")
    assert spec.parameter_descriptions == (
        "常数项（x⁰ 的系数）",
        "x^1 项的系数",
        "x^2 项的系数",
    )
