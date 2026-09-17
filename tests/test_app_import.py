"""GUI 模块基础导入测试，不实际打开窗口。"""

from pathlib import Path
import tkinter as tk

from src.app import FittingFactoryApp
from src.csv_handler import load_csv
from src.gui_components import LocalizedSubplotTool, SUBPLOT_TEXTS, TOOLBAR_ITEMS
from src.localization import (
    ERROR_LABELS,
    MODEL_LABELS,
    Localizer,
    localized_column_labels,
)


def test_gui_declares_required_models_and_error_modes() -> None:
    assert set(MODEL_LABELS["zh"]) == {
        "polynomial",
        "exponential",
        "sine",
        "logistic",
    }
    assert set(ERROR_LABELS["zh"]) == {"none", "column", "constant"}
    assert FittingFactoryApp.__name__ == "FittingFactoryApp"


def test_matplotlib_toolbar_and_subplot_labels_are_bilingual() -> None:
    for language in ("zh", "en"):
        assert len([item for item in TOOLBAR_ITEMS[language] if item[0]]) == 7
        assert len(SUBPLOT_TEXTS[language]["labels"]) == 6
    assert LocalizedSubplotTool.parameter_names == (
        "left",
        "bottom",
        "right",
        "top",
        "wspace",
        "hspace",
    )
    assert SUBPLOT_TEXTS["zh"]["labels"] == (
        "左边距",
        "下边距",
        "右边距",
        "上边距",
        "水平间距",
        "垂直间距",
    )


def test_gui_choice_labels_have_stable_bilingual_keys() -> None:
    assert MODEL_LABELS["zh"].keys() == MODEL_LABELS["en"].keys()
    assert ERROR_LABELS["zh"].keys() == ERROR_LABELS["en"].keys()
    assert Localizer.choice_key("model", "Polynomial") == "polynomial"
    assert Localizer.choice_key("error", "无误差") == "none"


def test_gui_can_switch_language_both_ways() -> None:
    root = tk.Tk()
    root.withdraw()
    try:
        app = FittingFactoryApp(root)
        assert app.localizer.language == "zh"
        assert app.model_var.get() == "多项式"
        app.set_language("en")
        assert root.title() == "CSV Curve Fitting Factory"
        assert app.model_var.get() == "Polynomial"
        assert app.guess_button.cget("text") == "Smart Initial Guess"
        assert app.toolbar.language == "en"
        app.set_language("zh")
        assert root.title() == "CSV 数据曲线拟合工厂"
        assert app.model_var.get() == "多项式"
        assert app.toolbar.language == "zh"
    finally:
        root.destroy()


def test_english_parameter_descriptions_do_not_squeeze_entries() -> None:
    root = tk.Tk()
    root.geometry("1050x680")
    try:
        app = FittingFactoryApp(root)
        app.dataset = load_csv(Path("data/polynomial_sample.csv"))
        app.model_combo.configure(state="readonly")
        app.degree_var.set("10")
        app.set_language("en")
        root.update_idletasks()

        entries = list(app.parameter_entries.values())
        assert len(entries) == 11
        assert min(entry.winfo_width() for entry in entries) >= 100
        assert all(int(entry.grid_info()["row"]) % 2 == 0 for entry in entries)

        app.parameter_entries["a0"].delete(0, tk.END)
        app.parameter_entries["a0"].insert(0, "123.456")
        app.set_language("zh")
        assert app.parameter_entries["a0"].get() == "123.456"
    finally:
        root.destroy()


def test_csv_column_labels_switch_language_without_changing_source_names() -> None:
    root = tk.Tk()
    root.withdraw()
    try:
        app = FittingFactoryApp(root)
        app.dataset = load_csv(Path("tests/test_data/random_logistic_unsorted.csv"))
        columns = app.dataset.column_names
        app._refresh_column_choices(columns[0], columns[1])
        app.error_mode_var.set(app.localizer.choice_label("error", "column"))
        app._on_error_mode_changed()

        app.set_language("en")
        assert app.x_combo.cget("values") == ("Input", "Output", "Error")
        assert app.x_column_var.get() == "Input"
        assert app.y_column_var.get() == "Output"
        assert app.error_source_var.get() == "Error"
        assert app._selected_column(app.x_column_var) == "输入量"
        assert app._selected_column(app.error_source_var) == "误差"

        app.set_language("zh")
        assert app.x_column_var.get() == "输入量"
        assert app.y_column_var.get() == "输出量"
        assert app.error_source_var.get() == "误差"
    finally:
        root.destroy()


def test_unknown_or_ambiguous_csv_column_names_are_not_translated() -> None:
    assert localized_column_labels(["自定义列"], "en") == {"自定义列": "自定义列"}
    assert localized_column_labels(["输入量", "Input"], "en") == {
        "输入量": "输入量",
        "Input": "Input",
    }
