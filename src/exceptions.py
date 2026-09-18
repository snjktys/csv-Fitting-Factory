# 本代码由 AI 辅助生成，已人工验证。
"""项目统一使用的业务异常。

"""

class FittingFactoryError(Exception):
    """所有可直接展示给用户的业务异常基类。"""


class CsvReadError(FittingFactoryError):
    """CSV 文件无法读取或内容不符合基本要求。"""


class DataValidationError(FittingFactoryError):
    """用户选择的数据列或清洗后的数据不满足要求。"""


class ParameterValidationError(FittingFactoryError):
    """拟合模型的阶次、参数数量或参数值不正确。"""


class FittingError(FittingFactoryError):
    """曲线拟合没有收敛或模型计算出现数值问题。"""


class ReportError(FittingFactoryError):
    """拟合报告无法生成或保存。"""
