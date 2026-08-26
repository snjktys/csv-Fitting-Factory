"""程序启动入口。

运行方式：在项目根目录执行 `python -m src.main`。
本文件由 AI 辅助生成，已人工检查启动流程。
"""

# 本模块由 AI 生成，已通过自动化测试和运行检查，需学生本人最终验证。

import tkinter as tk

from .app import FittingFactoryApp


def main() -> None:
    """创建 Tkinter 根窗口并进入消息循环。"""

    root = tk.Tk()
    FittingFactoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
