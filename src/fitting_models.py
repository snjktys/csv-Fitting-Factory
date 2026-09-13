"""四种曲线拟合模型及其元数据。

所有公式都集中在本文件中，GUI 不直接编写数学公式，便于测试和答辩说明。
本模块由 AI 辅助生成，已通过后续自动化测试，仍需学生本人理解与复核。
"""

# 本模块由 AI 生成，已通过自动化测试和运行检查，需学生本人最终验证。

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .exceptions import ParameterValidationError

ModelFunction = Callable[..., np.ndarray]


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """描述一个模型的显示信息、公式、参数名称和函数。"""

    key: str
    display_name: str
    formula: str
    parameter_names: tuple[str, ...]
    function: ModelFunction
    parameter_descriptions: tuple[str, ...] = ()


def make_polynomial_model(degree: int) -> ModelFunction:
    """创建指定阶次的多项式模型函数。

    参数顺序采用 a0、a1、...、an，即从常数项到最高次项。
    """

    if not 1 <= degree <= 10:
        raise ParameterValidationError("多项式阶次必须在 1～10 之间。")

    def polynomial(x: np.ndarray, *coefficients: float) -> np.ndarray:
        """按照升幂顺序计算多项式值。"""

        if len(coefficients) != degree + 1:
            raise ValueError(f"{degree} 阶多项式需要 {degree + 1} 个参数。")
        result = np.zeros_like(np.asarray(x, dtype=float), dtype=float)
        for power, coefficient in enumerate(coefficients):
            result += coefficient * np.power(x, power)
        return result

    return polynomial


def exponential_model(
    x: np.ndarray, a: float, b: float, c: float
) -> np.ndarray:
    """计算指数模型 y = a * exp(b*x) + c。

    这里不静默裁剪 b*x；如果参数导致溢出，由拟合引擎捕获并提示用户。
    """

    with np.errstate(over="raise", invalid="raise"):
        return a * np.exp(b * np.asarray(x, dtype=float)) + c


def sine_model(
    x: np.ndarray, amplitude: float, frequency: float, phase: float, offset: float
) -> np.ndarray:
    """计算正弦模型 y = A*sin(2*pi*f*x + phi) + c。"""

    x_values = np.asarray(x, dtype=float)
    return amplitude * np.sin(2.0 * np.pi * frequency * x_values + phase) + offset


def logistic_model(
    x: np.ndarray, level: float, rate: float, midpoint: float, baseline: float
) -> np.ndarray:
    """计算四参数 Logistic 模型。

    使用分段写法计算 sigmoid，避免 exp 在很大的正负参数下溢出。
    """

    z = rate * (np.asarray(x, dtype=float) - midpoint)
    sigmoid = np.empty_like(z, dtype=float)
    positive = z >= 0
    sigmoid[positive] = 1.0 / (1.0 + np.exp(-z[positive]))
    exp_z = np.exp(z[~positive])
    sigmoid[~positive] = exp_z / (1.0 + exp_z)
    return baseline + level * sigmoid


_FIXED_MODEL_SPECS = {
    "exponential": ModelSpec(
        key="exponential",
        display_name="指数模型",
        formula="y = a * exp(b*x) + c",
        parameter_names=("a", "b", "c"),
        function=exponential_model,
        parameter_descriptions=(
            "倍率（x=0 时相对基线的偏移）",
            "增长或衰减速率",
            "纵向偏移（基线）",
        ),
    ),
    "sine": ModelSpec(
        key="sine",
        display_name="正弦模型",
        formula="y = A * sin(2*pi*f*x + phi) + c",
        parameter_names=("A", "f", "phi", "c"),
        function=sine_model,
        parameter_descriptions=(
            "振幅",
            "频率（每个 x 单位的周期数）",
            "相位（弧度）",
            "纵向偏移",
        ),
    ),
    "logistic": ModelSpec(
        key="logistic",
        display_name="Logistic 模型",
        formula="y = c + L / (1 + exp(-k*(x-x0)))",
        parameter_names=("L", "k", "x0", "c"),
        function=logistic_model,
        parameter_descriptions=(
            "上下平台差值",
            "增长/下降速率（正值上升，负值下降）",
            "曲线中点的 x 值",
            "下平台基线",
        ),
    ),
}


def get_model_spec(model_key: str, degree: int | None = None) -> ModelSpec:
    """根据内部标识返回模型说明；多项式需要额外提供阶次。"""

    if model_key == "polynomial":
        if degree is None:
            raise ParameterValidationError("选择多项式模型时必须设置阶次。")
        function = make_polynomial_model(degree)
        parameter_names = tuple(f"a{i}" for i in range(degree + 1))
        terms = ["a0"] + [f"a{i}*x^{i}" for i in range(1, degree + 1)]
        parameter_descriptions = ("常数项（x⁰ 的系数）",) + tuple(
            f"x^{i} 项的系数" for i in range(1, degree + 1)
        )
        return ModelSpec(
            key=model_key,
            display_name=f"{degree} 阶多项式",
            formula="y = " + " + ".join(terms),
            parameter_names=parameter_names,
            function=function,
            parameter_descriptions=parameter_descriptions,
        )

    try:
        return _FIXED_MODEL_SPECS[model_key]
    except KeyError as exc:
        raise ParameterValidationError(f"未知的拟合模型：{model_key}") from exc


def model_parameter_count(model_key: str, degree: int | None = None) -> int:
    """返回模型需要的参数数量。"""

    return len(get_model_spec(model_key, degree).parameter_names)
