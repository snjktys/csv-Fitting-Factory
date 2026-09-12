"""GUI 模块基础导入测试，不实际打开窗口。"""

from src.app import (
    ERROR_DISPLAY_TO_KEY,
    MODEL_DISPLAY_TO_KEY,
    ChineseNavigationToolbar2Tk,
    ChineseSubplotTool,
    FittingFactoryApp,
)


def test_gui_declares_required_models_and_error_modes() -> None:
    assert set(MODEL_DISPLAY_TO_KEY.values()) == {
        "polynomial",
        "exponential",
        "sine",
        "logistic",
    }
    assert set(ERROR_DISPLAY_TO_KEY.values()) == {"none", "column", "constant"}
    assert FittingFactoryApp.__name__ == "FittingFactoryApp"


def test_matplotlib_toolbar_and_subplot_labels_are_chinese() -> None:
    items = [item for item in ChineseNavigationToolbar2Tk.toolitems if item[0]]
    assert len(items) == 7
    assert all(any("\u4e00" <= char <= "\u9fff" for char in item[1]) for item in items)
    assert ChineseSubplotTool._parameter_names == (
        "left",
        "bottom",
        "right",
        "top",
        "wspace",
        "hspace",
    )
    assert ChineseSubplotTool._parameter_labels == (
        "左边距",
        "下边距",
        "右边距",
        "上边距",
        "水平间距",
        "垂直间距",
    )
