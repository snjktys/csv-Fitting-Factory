"""CSV 文件读取模块。

本模块只负责文件输入，不负责选择列和数学拟合。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .data_types import DatasetInfo
from .exceptions import CsvReadError

SUPPORTED_ENCODINGS = ("utf-8-sig", "gb18030")


def load_csv(file_path: str | Path) -> DatasetInfo:
    """读取 CSV，并返回文件信息和原始 DataFrame。

    中文 Windows 环境中常见 UTF-8 与 GB18030，因此按固定顺序尝试编码。
    原始文件只读，程序不会写回 CSV。
    """

    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise CsvReadError("CSV 文件不存在，请重新选择文件。")
    if path.suffix.lower() != ".csv":
        raise CsvReadError("请选择扩展名为 .csv 的文件。")

    dataframe: pd.DataFrame | None = None
    selected_encoding = ""
    last_error: Exception | None = None

    for encoding in SUPPORTED_ENCODINGS:
        try:
            dataframe = pd.read_csv(path, encoding=encoding)
            selected_encoding = encoding
            break
        except UnicodeDecodeError as exc:
            last_error = exc
        except pd.errors.EmptyDataError as exc:
            raise CsvReadError("CSV 文件为空，没有可以读取的数据。") from exc
        except pd.errors.ParserError as exc:
            raise CsvReadError("CSV 格式无法解析，请检查分隔符和每行列数。") from exc
        except PermissionError as exc:
            raise CsvReadError("没有读取该文件的权限，请关闭占用程序或更换文件。") from exc
        except OSError as exc:
            raise CsvReadError(f"读取 CSV 时发生系统错误：{exc}") from exc

    if dataframe is None:
        raise CsvReadError(
            "无法识别 CSV 编码，请将文件另存为 UTF-8 或 GB18030 后重试。"
        ) from last_error
    if dataframe.empty:
        raise CsvReadError("CSV 文件没有数据行。")
    if len(dataframe.columns) < 2:
        raise CsvReadError("CSV 至少需要两列数据，才能选择 X 和 Y。")

    # 将列名统一转换成字符串，但不修改原 CSV 的数据内容。
    dataframe.columns = [str(column) for column in dataframe.columns]
    return DatasetInfo(
        file_path=path.resolve(),
        file_name=path.name,
        encoding=selected_encoding,
        original_rows=len(dataframe),
        column_names=list(dataframe.columns),
        dataframe=dataframe,
    )
