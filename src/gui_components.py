"""GUI 中使用的 Matplotlib 中文工具栏组件。"""

from __future__ import annotations

import matplotlib as mpl
from matplotlib import widgets
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.figure import Figure


class ChineseSubplotTool(widgets.SubplotTool):
    """显示中文标签且保留英文内部参数键的子图配置工具。"""

    _parameter_names = ("left", "bottom", "right", "top", "wspace", "hspace")
    _parameter_labels = ("左边距", "下边距", "右边距", "上边距", "水平间距", "垂直间距")

    def __init__(self, targetfig: Figure, toolfig: Figure) -> None:
        super().__init__(targetfig, toolfig)
        toolfig.suptitle("拖动滑块调整子图布局")
        for slider, label in zip(self._sliders, self._parameter_labels, strict=True):
            slider.label.set_text(label)
        self.buttonreset.label.set_text("重置")

    def _on_slider_changed(self, _) -> None:
        self.targetfig.subplots_adjust(
            **dict(zip(self._parameter_names, (s.val for s in self._sliders), strict=True))
        )
        if self.drawon:
            self.targetfig.canvas.draw()


class ChineseNavigationToolbar2Tk(NavigationToolbar2Tk):
    """使用中文工具提示的 Matplotlib 导航工具栏。"""

    toolitems = (
        ("Home", "恢复初始视图", "home", "home"),
        ("Back", "返回上一个视图", "back", "back"),
        ("Forward", "前进到下一个视图", "forward", "forward"),
        (None, None, None, None),
        ("Pan", "平移：左键拖动，右键缩放；\nX/Y 固定坐标轴，Ctrl 固定纵横比", "move", "pan"),
        ("Zoom", "矩形缩放：拖动矩形区域；\nX/Y 固定坐标轴", "zoom_to_rect", "zoom"),
        ("Subplots", "配置子图", "subplots", "configure_subplots"),
        (None, None, None, None),
        ("Save", "保存图像", "filesave", "save_figure"),
    )

    def configure_subplots(self, *args):
        if hasattr(self, "subplot_tool"):
            self.subplot_tool.figure.canvas.manager.show()
            return self.subplot_tool
        with mpl.rc_context({"toolbar": "none"}):
            manager = type(self.canvas).new_manager(Figure(figsize=(6, 3)), -1)
        manager.set_window_title("子图布局配置")
        tool_fig = manager.canvas.figure
        tool_fig.subplots_adjust(top=0.9)
        self.subplot_tool = ChineseSubplotTool(self.canvas.figure, tool_fig)
        connection_id = self.canvas.mpl_connect(
            "close_event", lambda _event: manager.destroy()
        )

        def on_tool_fig_close(_event) -> None:
            self.canvas.mpl_disconnect(connection_id)
            del self.subplot_tool

        tool_fig.canvas.mpl_connect("close_event", on_tool_fig_close)
        manager.show()
        return self.subplot_tool
