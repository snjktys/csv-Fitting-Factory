"""Tkinter 主窗口和用户操作流程。

本文件只负责界面与模块协调，数学公式和拟合算法位于独立模块中。
本模块由 AI 辅助生成，已通过后续自动化测试与手工冒烟测试，仍需学生本人理解。
"""

# 本模块由 AI 生成，已通过自动化测试和运行检查，需学生本人最终验证。

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .csv_handler import load_csv
from .data_processor import prepare_data
from .data_types import CleanedData, DatasetInfo, FitConfig, FitResult
from .exceptions import FittingFactoryError, ParameterValidationError
from .fitting_engine import fit_curve
from .fitting_models import get_model_spec
from .initial_guess import estimate_initial_parameters
from .report_generator import build_report_text, save_report, suggested_report_name
from .visualization import clear_figure, create_figure, draw_fit_result

MODEL_DISPLAY_TO_KEY = {
    "多项式": "polynomial",
    "指数": "exponential",
    "正弦": "sine",
    "Logistic": "logistic",
}
ERROR_DISPLAY_TO_KEY = {
    "无误差": "none",
    "CSV 误差列": "column",
    "统一误差值": "constant",
}


class FittingFactoryApp:
    """CSV 数据曲线拟合工厂的主窗口。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("CSV 数据曲线拟合工厂")
        self.root.geometry("1280x800")
        self.root.minsize(1050, 680)

        # 当前数据和拟合结果是程序的核心状态。配置变化时会主动清空旧结果。
        self.dataset: DatasetInfo | None = None
        self.cleaned_data: CleanedData | None = None
        self.fit_result: FitResult | None = None
        self.parameter_entries: dict[str, ttk.Entry] = {}

        self._create_variables()
        self._configure_style()
        self._build_menu()
        self._build_layout()
        self._set_status("等待导入 CSV 文件")

    def _create_variables(self) -> None:
        """创建与 Tkinter 控件绑定的状态变量。"""

        self.file_info_var = tk.StringVar(value="尚未选择文件")
        self.x_column_var = tk.StringVar()
        self.y_column_var = tk.StringVar()
        self.error_mode_var = tk.StringVar(value="无误差")
        self.error_source_var = tk.StringVar()
        self.model_var = tk.StringVar(value="多项式")
        self.degree_var = tk.StringVar(value="2")
        self.r_squared_var = tk.StringVar(value="R²：--")
        self.rmse_var = tk.StringVar(value="RMSE：--")
        self.status_var = tk.StringVar()
        self.row_info_var = tk.StringVar(value="有效数据：--　删除数据：--")

    def _configure_style(self) -> None:
        """设置简洁统一的 ttk 外观。"""

        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("Primary.TButton", font=("Microsoft YaHei UI", 10, "bold"), padding=7)
        style.configure("Status.TLabel", padding=(8, 5))

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="打开 CSV", command=self.open_csv)
        file_menu.add_command(label="导出 TXT 报告", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.destroy)
        menu_bar.add_cascade(label="文件", menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        menu_bar.add_cascade(label="帮助", menu=help_menu)
        self.root.configure(menu=menu_bar)

    def _build_layout(self) -> None:
        """创建左侧控制面板、右侧图表和底部状态栏。"""

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        controls = ttk.Frame(main, width=360)
        controls.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
        controls.grid_propagate(False)

        chart_frame = ttk.Frame(main)
        chart_frame.grid(row=0, column=1, sticky="nsew")
        chart_frame.rowconfigure(0, weight=1)
        chart_frame.columnconfigure(0, weight=1)

        self._build_file_section(controls)
        self._build_column_section(controls)
        self._build_model_section(controls)
        self._build_result_section(controls)

        self.figure = create_figure()
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        toolbar_frame = ttk.Frame(chart_frame)
        toolbar_frame.grid(row=1, column=0, sticky="ew")
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side=tk.LEFT)

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Separator(status_frame).pack(fill=tk.X)
        ttk.Label(
            status_frame, textvariable=self.status_var, style="Status.TLabel"
        ).pack(side=tk.LEFT)
        ttk.Label(
            status_frame, textvariable=self.row_info_var, style="Status.TLabel"
        ).pack(side=tk.RIGHT)

    def _build_file_section(self, parent: ttk.Frame) -> None:
        section = ttk.LabelFrame(parent, text="1  数据文件", style="Section.TLabelframe", padding=10)
        section.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(
            section,
            text="打开 CSV",
            command=self.open_csv,
            style="Primary.TButton",
        ).pack(fill=tk.X)
        ttk.Label(
            section,
            textvariable=self.file_info_var,
            wraplength=320,
            foreground="#5f6b7a",
        ).pack(fill=tk.X, pady=(8, 0))

    def _build_column_section(self, parent: ttk.Frame) -> None:
        section = ttk.LabelFrame(parent, text="2  数据列与误差", style="Section.TLabelframe", padding=10)
        section.pack(fill=tk.X, pady=(0, 8))
        section.columnconfigure(1, weight=1)

        ttk.Label(section, text="X 列").grid(row=0, column=0, sticky="w", pady=3)
        self.x_combo = ttk.Combobox(section, textvariable=self.x_column_var, state="disabled")
        self.x_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=3)

        ttk.Label(section, text="Y 列").grid(row=1, column=0, sticky="w", pady=3)
        self.y_combo = ttk.Combobox(section, textvariable=self.y_column_var, state="disabled")
        self.y_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=3)

        ttk.Label(section, text="误差模式").grid(row=2, column=0, sticky="w", pady=3)
        self.error_mode_combo = ttk.Combobox(
            section,
            textvariable=self.error_mode_var,
            values=list(ERROR_DISPLAY_TO_KEY),
            state="disabled",
        )
        self.error_mode_combo.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=3)

        ttk.Label(section, text="误差来源").grid(row=3, column=0, sticky="w", pady=3)
        self.error_source_combo = ttk.Combobox(
            section, textvariable=self.error_source_var, state="disabled"
        )
        self.error_source_combo.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=3)

        self.preview_button = ttk.Button(
            section,
            text="数据预览",
            command=self.show_data_preview,
            state="disabled",
        )
        self.preview_button.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        for combo in (self.x_combo, self.y_combo):
            combo.bind("<<ComboboxSelected>>", self._on_configuration_changed)
        self.error_mode_combo.bind("<<ComboboxSelected>>", self._on_error_mode_changed)
        self.error_source_combo.bind("<<ComboboxSelected>>", self._on_configuration_changed)

    def _build_model_section(self, parent: ttk.Frame) -> None:
        section = ttk.LabelFrame(
            parent,
            text="3  拟合模型与参数",
            style="Section.TLabelframe",
            padding=10,
        )
        section.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        section.columnconfigure(1, weight=1)

        ttk.Label(section, text="模型").grid(row=0, column=0, sticky="w", pady=3)
        self.model_combo = ttk.Combobox(
            section,
            textvariable=self.model_var,
            values=list(MODEL_DISPLAY_TO_KEY),
            state="disabled",
        )
        self.model_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=3)
        self.model_combo.bind("<<ComboboxSelected>>", self._on_model_changed)

        ttk.Label(section, text="阶次").grid(row=1, column=0, sticky="w", pady=3)
        self.degree_spinbox = ttk.Spinbox(
            section,
            from_=1,
            to=10,
            textvariable=self.degree_var,
            width=8,
            state="disabled",
            command=self._on_model_changed,
        )
        self.degree_spinbox.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=3)
        self.degree_spinbox.bind("<FocusOut>", self._on_model_changed)
        self.degree_spinbox.bind("<Return>", self._on_model_changed)

        ttk.Label(section, text="参数").grid(row=2, column=0, sticky="nw", pady=(6, 3))
        self.parameter_frame = ttk.Frame(section)
        self.parameter_frame.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(6, 3))
        self.parameter_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(section)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure((0, 1), weight=1)
        self.guess_button = ttk.Button(
            button_frame,
            text="智能初值",
            command=self.use_smart_initial_guess,
            state="disabled",
        )
        self.guess_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.fit_button = ttk.Button(
            button_frame,
            text="开始拟合",
            command=self.run_fitting,
            state="disabled",
            style="Primary.TButton",
        )
        self.fit_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _build_result_section(self, parent: ttk.Frame) -> None:
        section = ttk.LabelFrame(parent, text="4  拟合结果", style="Section.TLabelframe", padding=10)
        section.pack(fill=tk.X)
        metrics = ttk.Frame(section)
        metrics.pack(fill=tk.X)
        ttk.Label(
            metrics, textvariable=self.r_squared_var, font=("Consolas", 10)
        ).pack(side=tk.LEFT)
        ttk.Label(metrics, textvariable=self.rmse_var, font=("Consolas", 10)).pack(side=tk.RIGHT)
        self.report_button = ttk.Button(
            section,
            text="生成 TXT 报告",
            command=self.export_report,
            state="disabled",
        )
        self.report_button.pack(fill=tk.X, pady=(8, 0))

    def open_csv(self) -> None:
        """让用户选择 CSV，并把列名加载到界面。"""

        path = filedialog.askopenfilename(
            title="选择 CSV 文件",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            dataset = load_csv(path)
        except FittingFactoryError as exc:
            messagebox.showerror("CSV 读取失败", str(exc), parent=self.root)
            return

        self.dataset = dataset
        columns = dataset.column_names
        for combo in (self.x_combo, self.y_combo):
            combo.configure(values=columns, state="readonly")
        self.x_column_var.set(columns[0])
        self.y_column_var.set(columns[1])
        self.error_mode_combo.configure(state="readonly")
        self.model_combo.configure(state="readonly")
        self.preview_button.configure(state="normal")
        self.guess_button.configure(state="normal")
        self.fit_button.configure(state="normal")
        self.file_info_var.set(
            f"{dataset.file_name}\n编码：{dataset.encoding}　"
            f"{dataset.original_rows} 行 × {len(columns)} 列"
        )
        self._on_error_mode_changed()
        self._on_model_changed()
        self._invalidate_result("CSV 加载成功，请确认列和模型。")

    def _on_error_mode_changed(self, _event=None) -> None:
        """根据误差模式切换误差来源控件的类型和状态。"""

        mode = ERROR_DISPLAY_TO_KEY.get(self.error_mode_var.get(), "none")
        if mode == "none":
            self.error_source_var.set("")
            self.error_source_combo.configure(values=[], state="disabled")
        elif mode == "column" and self.dataset is not None:
            self.error_source_combo.configure(values=self.dataset.column_names, state="readonly")
            if self.error_source_var.get() not in self.dataset.column_names:
                self.error_source_var.set(self.dataset.column_names[-1])
        else:
            # ttk.Combobox 的 normal 状态允许用户直接输入统一误差值。
            self.error_source_combo.configure(values=[], state="normal")
            if not self.error_source_var.get():
                self.error_source_var.set("0.1")
        self._invalidate_result("误差设置已改变，需要重新拟合。")

    def _on_model_changed(self, _event=None) -> None:
        """切换模型后重新生成参数输入框。"""

        if self.dataset is None:
            return
        model_key = MODEL_DISPLAY_TO_KEY[self.model_var.get()]
        degree = self._read_degree(show_message=False) if model_key == "polynomial" else None
        self.degree_spinbox.configure(state="normal" if model_key == "polynomial" else "disabled")
        if model_key == "polynomial" and degree is None:
            return
        try:
            spec = get_model_spec(model_key, degree)
        except FittingFactoryError:
            return
        for widget in self.parameter_frame.winfo_children():
            widget.destroy()
        self.parameter_entries.clear()
        default_values = [0.0] * len(spec.parameter_names)
        if default_values:
            default_values[0] = 1.0
        parameter_defaults = zip(
            spec.parameter_names, default_values, strict=True
        )
        for row, (name, default) in enumerate(parameter_defaults):
            ttk.Label(self.parameter_frame, text=name).grid(row=row, column=0, sticky="w", pady=2)
            entry = ttk.Entry(self.parameter_frame)
            entry.insert(0, f"{default:g}")
            entry.grid(row=row, column=1, sticky="ew", padx=(6, 0), pady=2)
            entry.bind("<KeyRelease>", self._on_configuration_changed)
            self.parameter_entries[name] = entry
        self._invalidate_result("模型或参数已改变，需要重新拟合。")

    def _on_configuration_changed(self, _event=None) -> None:
        self._invalidate_result("数据列或参数已改变，需要重新拟合。")

    def use_smart_initial_guess(self) -> None:
        """清洗数据并把模型对应的智能初值填入参数框。"""

        try:
            data, model_key, degree = self._prepare_current_data_and_model()
            parameters, warnings = estimate_initial_parameters(model_key, data.x, data.y, degree)
            spec = get_model_spec(model_key, degree)
            for name, value in zip(spec.parameter_names, parameters, strict=True):
                entry = self.parameter_entries[name]
                entry.delete(0, tk.END)
                entry.insert(0, f"{value:.8g}")
            self.cleaned_data = data
            self.row_info_var.set(f"有效数据：{data.valid_rows}　删除数据：{data.removed_rows}")
            self._invalidate_result("智能初值已生成，可以开始拟合。")
            if warnings:
                messagebox.showwarning("智能初值提示", "\n".join(warnings), parent=self.root)
        except FittingFactoryError as exc:
            messagebox.showerror("智能初值失败", str(exc), parent=self.root)

    def run_fitting(self) -> None:
        """执行当前配置的曲线拟合，并刷新指标和图形。"""

        try:
            data, model_key, degree = self._prepare_current_data_and_model()
            initial_parameters = self._read_parameter_values()
            if model_key == "polynomial" and degree is not None and degree >= 6:
                proceed = messagebox.askyesno(
                    "高阶多项式提示",
                    "6～10 阶多项式可能过拟合或在边缘振荡，是否继续？",
                    parent=self.root,
                )
                if not proceed:
                    return
            self.fit_button.configure(state="disabled")
            self._set_status("正在进行曲线拟合...")
            self.root.update_idletasks()
            result = fit_curve(data, FitConfig(model_key, degree, initial_parameters))
        except FittingFactoryError as exc:
            messagebox.showerror("拟合失败", str(exc), parent=self.root)
            self._set_status("拟合失败，请检查数据和参数。")
            return
        finally:
            if self.dataset is not None:
                self.fit_button.configure(state="normal")

        self.cleaned_data = data
        self.fit_result = result
        r_squared_text = (
            "R²：N/A"
            if result.r_squared is None
            else f"R²：{result.r_squared:.6g}"
        )
        self.r_squared_var.set(r_squared_text)
        self.rmse_var.set(f"RMSE：{result.rmse:.6g}")
        self.row_info_var.set(f"有效数据：{data.valid_rows}　删除数据：{data.removed_rows}")
        draw_fit_result(self.figure, data, result)
        self.canvas.draw_idle()
        self.report_button.configure(state="normal")
        self._set_status("拟合成功，可以查看图形或生成报告。")
        if result.warnings:
            messagebox.showwarning("拟合结果提示", "\n".join(result.warnings), parent=self.root)

    def export_report(self) -> None:
        """把当前有效拟合结果保存为 TXT。"""

        if self.dataset is None or self.cleaned_data is None or self.fit_result is None:
            messagebox.showinfo("暂无结果", "请先完成一次成功拟合。", parent=self.root)
            return
        output_path = filedialog.asksaveasfilename(
            title="保存拟合报告",
            defaultextension=".txt",
            initialfile=suggested_report_name(self.dataset, self.fit_result),
            filetypes=[("文本文件", "*.txt")],
        )
        if not output_path:
            return
        try:
            report_text = build_report_text(self.dataset, self.cleaned_data, self.fit_result)
            saved_path = save_report(report_text, output_path)
        except FittingFactoryError as exc:
            messagebox.showerror("报告保存失败", str(exc), parent=self.root)
            return
        self._set_status(f"报告已保存：{saved_path}")
        messagebox.showinfo("保存成功", f"拟合报告已保存到：\n{saved_path}", parent=self.root)

    def show_data_preview(self) -> None:
        """在新窗口中显示 CSV 前 100 行，计算仍使用全部数据。"""

        if self.dataset is None:
            return
        window = tk.Toplevel(self.root)
        window.title(f"数据预览 - {self.dataset.file_name}")
        window.geometry("850x500")
        frame = ttk.Frame(window, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(frame, columns=self.dataset.column_names, show="headings")
        vertical = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        for column in self.dataset.column_names:
            tree.heading(column, text=column)
            tree.column(column, width=120, anchor=tk.CENTER)
        for values in self.dataset.dataframe.head(100).itertuples(index=False, name=None):
            tree.insert("", tk.END, values=values)

    def _prepare_current_data_and_model(self) -> tuple[CleanedData, str, int | None]:
        """读取当前 GUI 选择，并返回清洗数据和模型标识。"""

        if self.dataset is None:
            raise ParameterValidationError("请先导入 CSV 文件。")
        model_key = MODEL_DISPLAY_TO_KEY[self.model_var.get()]
        degree = self._read_degree() if model_key == "polynomial" else None
        error_mode = ERROR_DISPLAY_TO_KEY[self.error_mode_var.get()]
        sigma_column = self.error_source_var.get() if error_mode == "column" else None
        constant_sigma = self.error_source_var.get() if error_mode == "constant" else None
        data = prepare_data(
            self.dataset.dataframe,
            self.x_column_var.get(),
            self.y_column_var.get(),
            error_mode,
            sigma_column,
            constant_sigma,  # prepare_data 会负责数字转换和中文错误提示。
        )
        return data, model_key, degree

    def _read_degree(self, show_message: bool = True) -> int | None:
        try:
            degree = int(self.degree_var.get())
        except ValueError:
            if show_message:
                raise ParameterValidationError("多项式阶次必须是 1～10 的整数。")
            return None
        if not 1 <= degree <= 10:
            if show_message:
                raise ParameterValidationError("多项式阶次必须在 1～10 之间。")
            return None
        return degree

    def _read_parameter_values(self) -> list[float]:
        values: list[float] = []
        for name, entry in self.parameter_entries.items():
            try:
                value = float(entry.get())
            except ValueError as exc:
                raise ParameterValidationError(f"参数 {name} 必须是数字。") from exc
            if not np.isfinite(value):
                raise ParameterValidationError(f"参数 {name} 必须是有限数值。")
            values.append(value)
        return values

    def _invalidate_result(self, status: str) -> None:
        """配置变化后清除旧结果，避免导出与当前设置不一致的报告。"""

        self.cleaned_data = None
        self.fit_result = None
        self.r_squared_var.set("R²：--")
        self.rmse_var.set("RMSE：--")
        if hasattr(self, "report_button"):
            self.report_button.configure(state="disabled")
        if hasattr(self, "figure"):
            clear_figure(self.figure)
            self.canvas.draw_idle()
        self._set_status(status)

    def _set_status(self, message: str) -> None:
        self.status_var.set(f"状态：{message}")

    def show_help(self) -> None:
        messagebox.showinfo(
            "使用说明",
            "1. 打开带表头的 CSV 文件。\n"
            "2. 选择 X、Y 和误差模式。\n"
            "3. 选择模型，并使用智能初值或手动输入参数。\n"
            "4. 点击开始拟合，查看拟合图、残差、R² 和 RMSE。\n"
            "5. 拟合成功后生成 TXT 报告。",
            parent=self.root,
        )

    def show_about(self) -> None:
        messagebox.showinfo(
            "关于",
            "CSV 数据曲线拟合工厂\nPython 课程设计第 38 题\n支持多项式、指数、正弦和 Logistic 拟合。",
            parent=self.root,
        )
