"""程序启动入口。

运行方式：在项目根目录执行 `python -m src.main`。
"""

import tkinter as tk

from .app import FittingFactoryApp


def main() -> None:
    """创建 Tkinter 根窗口并进入消息循环。"""

    root = tk.Tk()
    FittingFactoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
