"""GUI 中使用的 Matplotlib 双语工具栏组件。"""

from __future__ import annotations

import matplotlib as mpl
from matplotlib import widgets
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.figure import Figure

TOOLBAR_ITEMS = {
    "zh": (
        ("Home", "恢复初始视图", "home", "home"),
        ("Back", "返回上一个视图", "back", "back"),
        ("Forward", "前进到下一个视图", "forward", "forward"),
        (None, None, None, None),
        ("Pan", "平移：左键拖动，右键缩放；\nX/Y 固定坐标轴，Ctrl 固定纵横比", "move", "pan"),
        ("Zoom", "矩形缩放：拖动矩形区域；\nX/Y 固定坐标轴", "zoom_to_rect", "zoom"),
        ("Subplots", "配置子图", "subplots", "configure_subplots"),
        (None, None, None, None),
        ("Save", "保存图像", "filesave", "save_figure"),
    ),
    "en": NavigationToolbar2Tk.toolitems,
}

SUBPLOT_TEXTS = {
    "zh": {
        "window": "子图布局配置",
        "title": "拖动滑块调整子图布局",
        "labels": ("左边距", "下边距", "右边距", "上边距", "水平间距", "垂直间距"),
        "reset": "重置",
    },
    "en": {
        "window": "Subplot Configuration",
        "title": "Drag the sliders to adjust the subplot layout",
        "labels": ("Left", "Bottom", "Right", "Top", "Horizontal Spacing", "Vertical Spacing"),
        "reset": "Reset",
    },
}


class LocalizedSubplotTool(widgets.SubplotTool):
    """显示当前语言标签且保留英文内部参数键的子图配置工具。"""

    parameter_names = ("left", "bottom", "right", "top", "wspace", "hspace")

    def __init__(self, targetfig: Figure, toolfig: Figure, language: str) -> None:
        super().__init__(targetfig, toolfig)
        texts = SUBPLOT_TEXTS[language]
        toolfig.suptitle(texts["title"])
        for slider, label in zip(self._sliders, texts["labels"], strict=True):
            slider.label.set_text(label)
        self.buttonreset.label.set_text(texts["reset"])

    def _on_slider_changed(self, _) -> None:
        self.targetfig.subplots_adjust(
            **dict(zip(self.parameter_names, (s.val for s in self._sliders), strict=True))
        )
        if self.drawon:
            self.targetfig.canvas.draw()


class LocalizedNavigationToolbar2Tk(NavigationToolbar2Tk):
    """根据当前语言显示工具提示和子图配置窗口。"""

    def __init__(self, canvas, window=None, *, language="zh", pack_toolbar=True):
        self.language = language
        self.toolitems = TOOLBAR_ITEMS[language]
        super().__init__(canvas, window, pack_toolbar=pack_toolbar)

    def configure_subplots(self, *args):
        if hasattr(self, "subplot_tool"):
            self.subplot_tool.figure.canvas.manager.show()
            return self.subplot_tool
        with mpl.rc_context({"toolbar": "none"}):
            manager = type(self.canvas).new_manager(Figure(figsize=(6, 3)), -1)
        manager.set_window_title(SUBPLOT_TEXTS[self.language]["window"])
        tool_fig = manager.canvas.figure
        tool_fig.subplots_adjust(top=0.9)
        self.subplot_tool = LocalizedSubplotTool(
            self.canvas.figure, tool_fig, self.language
        )
        connection_id = self.canvas.mpl_connect(
            "close_event", lambda _event: manager.destroy()
        )

        def on_tool_fig_close(_event) -> None:
            self.canvas.mpl_disconnect(connection_id)
            del self.subplot_tool

        tool_fig.canvas.mpl_connect("close_event", on_tool_fig_close)
        manager.show()
        return self.subplot_tool
