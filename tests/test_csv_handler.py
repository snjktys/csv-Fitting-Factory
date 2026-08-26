"""CSV 文件读取模块测试。"""

from pathlib import Path

import pytest

from src.csv_handler import load_csv
from src.exceptions import CsvReadError


def test_load_utf8_csv_with_chinese_headers(tmp_path: Path) -> None:
    file_path = tmp_path / "中文数据.csv"
    file_path.write_text("时间,温度\n0,20\n1,21\n", encoding="utf-8-sig")

    dataset = load_csv(file_path)

    assert dataset.column_names == ["时间", "温度"]
    assert dataset.original_rows == 2
    assert dataset.encoding == "utf-8-sig"


def test_rejects_single_column_csv(tmp_path: Path) -> None:
    file_path = tmp_path / "single.csv"
    file_path.write_text("x\n1\n2\n", encoding="utf-8")

    with pytest.raises(CsvReadError):
        load_csv(file_path)


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(CsvReadError):
        load_csv(tmp_path / "missing.csv")
