"""GUI 模块基础导入测试，不实际打开窗口。"""

from src.app import ERROR_DISPLAY_TO_KEY, MODEL_DISPLAY_TO_KEY, FittingFactoryApp


def test_gui_declares_required_models_and_error_modes() -> None:
    assert set(MODEL_DISPLAY_TO_KEY.values()) == {
        "polynomial",
        "exponential",
        "sine",
        "logistic",
    }
    assert set(ERROR_DISPLAY_TO_KEY.values()) == {"none", "column", "constant"}
    assert FittingFactoryApp.__name__ == "FittingFactoryApp"
