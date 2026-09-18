"""Tkinter 主窗口和用户操作流程。

本文件只负责界面与模块协调，数学公式和拟合算法位于独立模块中。
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
)

from .csv_handler import load_csv
from .data_processor import prepare_data
from .data_types import CleanedData, DatasetInfo, FitConfig, FitResult
from .exceptions import FittingFactoryError, ParameterValidationError
from .fitting_engine import fit_curve
from .fitting_models import get_model_spec
from .gui_components import LocalizedNavigationToolbar2Tk
from .initial_guess import estimate_initial_parameters
from .localization import (
    Localizer,
    model_name,
    english_parameter_descriptions,
    localized_column_labels,
    translate_message,
)
from .monte_carlo import bootstrap_parameters
from .report_generator import build_report_text, save_report, suggested_report_name
from .visualization import (
    clear_figure,
    create_figure,
    create_parameter_histograms,
    draw_fit_result,
)

class FittingFactoryApp:
    """CSV 数据曲线拟合工厂的主窗口。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.localizer = Localizer()
        self.root.title(self.localizer.text("app_title"))
        self.root.geometry("1280x800")
        self.root.minsize(1050, 680)

        # 当前数据和拟合结果是程序的核心状态。配置变化时会主动清空旧结果。
        self.dataset: DatasetInfo | None = None
        self.cleaned_data: CleanedData | None = None
        self.fit_result: FitResult | None = None
        self.parameter_entries: dict[str, ttk.Entry] = {}
        self.preview_windows: dict[tk.Toplevel, ttk.Treeview] = {}
        self._column_labels_by_name: dict[str, str] = {}
        self._row_counts: tuple[int, int] | None = None
        self._status_key = "waiting_csv"
        self._status_values: dict[str, object] = {}

        self._create_variables()
        self._configure_style()
        self._build_menu()
        self._build_layout()
        self._set_status("waiting_csv")

    def _create_variables(self) -> None:
        """创建与 Tkinter 控件绑定的状态变量。"""

        self.file_info_var = tk.StringVar(value=self.localizer.text("no_file"))
        self.x_column_var = tk.StringVar()
        self.y_column_var = tk.StringVar()
        self.error_mode_var = tk.StringVar(value=self.localizer.choice_label("error", "none"))
        self.error_source_var = tk.StringVar()
        self.model_var = tk.StringVar(value=self.localizer.choice_label("model", "polynomial"))
        self.degree_var = tk.StringVar(value="2")
        self.r_squared_var = tk.StringVar(value=self.localizer.text("r_squared_empty"))
        self.rmse_var = tk.StringVar(value=self.localizer.text("rmse_empty"))
        self.status_var = tk.StringVar()
        self.row_info_var = tk.StringVar(value=self.localizer.text("valid_removed", valid="--", removed="--"))
        self.formula_var = tk.StringVar()

    def _configure_style(self) -> None:
        """设置简洁统一的 ttk 外观。"""

        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Section.TLabelframe.Label", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("Primary.TButton", font=("Microsoft YaHei UI", 10, "bold"), padding=7)
        style.configure("Action.TButton", font=("Microsoft YaHei UI", 10, "bold"), padding=7)
        style.configure("Status.TLabel", padding=(8, 5))

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label=self.localizer.text("open_csv"), command=self.open_csv)
        file_menu.add_command(label=self.localizer.text("export_report"), command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label=self.localizer.text("exit"), command=self.root.destroy)
        menu_bar.add_cascade(label=self.localizer.text("file"), menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(label=self.localizer.text("instructions"), command=self.show_help)
        help_menu.add_command(label=self.localizer.text("about"), command=self.show_about)
        language_menu = tk.Menu(help_menu, tearoff=False)
        language_menu.add_command(
            label=self.localizer.text("chinese"), command=lambda: self.set_language("zh")
        )
        language_menu.add_command(
            label=self.localizer.text("english"), command=lambda: self.set_language("en")
        )
        help_menu.add_cascade(label=self.localizer.text("language"), menu=language_menu)
        menu_bar.add_cascade(label=self.localizer.text("help"), menu=help_menu)
        self.root.configure(menu=menu_bar)

    def _build_layout(self) -> None:
        """创建左侧控制面板、右侧图表和底部状态栏。"""

        # 先固定底部状态栏，再让主内容区 expand；否则主内容会先占满
        # 整个窗口，状态栏在小窗口下会被 pack 成 1 像素而看不见。
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Separator(status_frame).pack(fill=tk.X)
        ttk.Label(
            status_frame, textvariable=self.status_var, style="Status.TLabel"
        ).pack(side=tk.LEFT)
        ttk.Label(
            status_frame, textvariable=self.row_info_var, style="Status.TLabel"
        ).pack(side=tk.RIGHT)

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # 左侧控制区使用独立滚动画布。参数行较多时只滚动左侧内容，
        # 右侧图表和底部状态栏保持固定，不会被参数区挤出窗口。
        controls_pane = ttk.Frame(main, width=360)
        controls_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        controls_pane.grid_propagate(False)
        controls_pane.columnconfigure(0, weight=1)
        controls_pane.rowconfigure(0, weight=1)
        controls_canvas = tk.Canvas(controls_pane, highlightthickness=0, borderwidth=0)
        controls_canvas.grid(row=0, column=0, sticky="nsew")
        self.controls_canvas = controls_canvas
        controls_scrollbar = ttk.Scrollbar(
            controls_pane, orient=tk.VERTICAL, command=controls_canvas.yview
        )
        controls_scrollbar.grid(row=0, column=1, sticky="ns")
        self.controls_scrollbar = controls_scrollbar
        self._controls_scrollable = False
        controls_canvas.configure(yscrollcommand=controls_scrollbar.set)
        controls = ttk.Frame(controls_canvas)
        controls_window = controls_canvas.create_window((0, 0), window=controls, anchor="nw")

        self._controls_wheel_tag = "FittingFactoryControlsWheel"
        self.root.bind_class(
            self._controls_wheel_tag,
            "<MouseWheel>",
            self._on_controls_mousewheel,
        )
        self.root.bind_class(
            self._controls_wheel_tag,
            "<Button-4>",
            self._on_controls_mousewheel,
        )
        self.root.bind_class(
            self._controls_wheel_tag,
            "<Button-5>",
            self._on_controls_mousewheel,
        )

        def update_controls_scrollregion(_event=None) -> None:
            bbox = controls_canvas.bbox("all")
            if not bbox:
                return
            controls_canvas.configure(scrollregion=bbox)
            content_height = bbox[3] - bbox[1]
            viewport_height = controls_canvas.winfo_height()
            self._controls_scrollable = content_height > viewport_height + 1
            if self._controls_scrollable:
                if not controls_scrollbar.winfo_ismapped():
                    controls_scrollbar.grid(row=0, column=1, sticky="ns")
            else:
                # 全屏或大窗口时内容完全可见，不显示多余滚动条，也不移动 Canvas。
                controls_scrollbar.grid_remove()
                controls_canvas.yview_moveto(0)

        def resize_controls_content(event) -> None:
            controls_canvas.itemconfigure(controls_window, width=event.width)
            controls_canvas.after_idle(update_controls_scrollregion)

        controls.bind("<Configure>", update_controls_scrollregion)
        controls_canvas.bind("<Configure>", resize_controls_content)

        chart_frame = ttk.Frame(main)
        chart_frame.grid(row=0, column=1, sticky="nsew")
        chart_frame.rowconfigure(0, weight=1)
        chart_frame.columnconfigure(0, weight=1)

        self._build_file_section(controls)
        self._build_column_section(controls)
        self._build_model_section(controls)
        self._build_result_section(controls)
        self._install_controls_wheel_binding(controls_pane)

        self.figure = create_figure(self.localizer.language)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        toolbar_frame = ttk.Frame(chart_frame)
        toolbar_frame.grid(row=1, column=0, sticky="ew")
        self.toolbar_frame = toolbar_frame
        self.toolbar = LocalizedNavigationToolbar2Tk(
            self.canvas, toolbar_frame, language=self.localizer.language, pack_toolbar=False
        )
        self.toolbar.update()
        self.toolbar.pack(side=tk.LEFT)

    def _section(self, parent: ttk.Frame, key: str) -> ttk.LabelFrame:
        return self.localizer.bind(
            ttk.LabelFrame(parent, style="Section.TLabelframe", padding=10), key
        )

    def _combo_row(
        self,
        parent: ttk.LabelFrame,
        row: int,
        label_key: str,
        variable: tk.StringVar,
        values: list[str] | None = None,
    ) -> ttk.Combobox:
        label = self.localizer.bind(ttk.Label(parent), label_key)
        label.grid(row=row, column=0, sticky="w", pady=3)
        combo = ttk.Combobox(
            parent,
            textvariable=variable,
            values=values or [],
            state="disabled",
        )
        combo.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=3)
        return combo

    def _build_file_section(self, parent: ttk.Frame) -> None:
        section = self._section(parent, "section_file")
        section.pack(fill=tk.X, pady=(0, 8))
        self.localizer.bind(ttk.Button(
            section,
            command=self.open_csv,
            style="Primary.TButton",
        ), "open_csv").pack(fill=tk.X)
        ttk.Label(
            section,
            textvariable=self.file_info_var,
            wraplength=320,
            foreground="#5f6b7a",
        ).pack(fill=tk.X, pady=(8, 0))

    def _build_column_section(self, parent: ttk.Frame) -> None:
        section = self._section(parent, "section_columns")
        section.pack(fill=tk.X, pady=(0, 8))
        section.columnconfigure(1, weight=1)

        self.x_combo = self._combo_row(section, 0, "x_column", self.x_column_var)
        self.y_combo = self._combo_row(section, 1, "y_column", self.y_column_var)
        self.error_mode_combo = self._combo_row(
            section, 2, "error_mode", self.error_mode_var, self.localizer.choices("error")
        )
        self.error_source_combo = self._combo_row(
            section, 3, "error_source", self.error_source_var
        )

        self.preview_button = ttk.Button(
            section,
            command=self.show_data_preview,
            state="disabled",
        )
        self.localizer.bind(self.preview_button, "data_preview")
        self.preview_button.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        for combo in (self.x_combo, self.y_combo):
            combo.bind("<<ComboboxSelected>>", self._on_configuration_changed)
        self.error_mode_combo.bind("<<ComboboxSelected>>", self._on_error_mode_changed)
        self.error_source_combo.bind("<<ComboboxSelected>>", self._on_configuration_changed)

    def _build_model_section(self, parent: ttk.Frame) -> None:
        section = self._section(parent, "section_model")
        section.pack(fill=tk.X, pady=(0, 8))
        section.columnconfigure(1, weight=1)

        model_label = ttk.Label(section)
        self.localizer.bind(model_label, "model")
        model_label.grid(row=0, column=0, sticky="w", pady=3)
        self.model_combo = ttk.Combobox(
            section,
            textvariable=self.model_var,
            values=self.localizer.choices("model"),
            state="disabled",
        )
        self.model_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=3)
        self.model_combo.bind("<<ComboboxSelected>>", self._on_model_changed)

        degree_label = ttk.Label(section)
        self.localizer.bind(degree_label, "degree")
        degree_label.grid(row=1, column=0, sticky="w", pady=3)
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

        formula_label = ttk.Label(section)
        self.localizer.bind(formula_label, "formula")
        formula_label.grid(row=2, column=0, sticky="nw", pady=(6, 3))
        ttk.Label(
            section,
            textvariable=self.formula_var,
            wraplength=300,
            justify=tk.LEFT,
            foreground="#5f6b7a",
        ).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 3))

        parameters_label = ttk.Label(section)
        self.localizer.bind(parameters_label, "parameters")
        parameters_label.grid(row=3, column=0, sticky="nw", pady=(6, 3))
        self.parameter_frame = ttk.Frame(section)
        self.parameter_frame.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(6, 3))
        self.parameter_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(section)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure((0, 1), weight=1)
        self.guess_button = ttk.Button(
            button_frame,
            command=self.use_smart_initial_guess,
            state="disabled",
            style="Action.TButton",
        )
        self.localizer.bind(self.guess_button, "smart_initial")
        self.guess_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.fit_button = ttk.Button(
            button_frame,
            command=self.run_fitting,
            state="disabled",
            style="Action.TButton",
        )
        self.localizer.bind(self.fit_button, "start_fitting")
        self.fit_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _build_result_section(self, parent: ttk.Frame) -> None:
        section = self._section(parent, "section_result")
        section.pack(fill=tk.X)
        metrics = ttk.Frame(section)
        metrics.pack(fill=tk.X)
        ttk.Label(
            metrics, textvariable=self.r_squared_var, font=("Consolas", 10)
        ).pack(side=tk.LEFT)
        ttk.Label(metrics, textvariable=self.rmse_var, font=("Consolas", 10)).pack(side=tk.RIGHT)
        self.report_button = ttk.Button(
            section,
            command=self.export_report,
            state="disabled",
        )
        self.localizer.bind(self.report_button, "generate_report")
        self.report_button.pack(fill=tk.X, pady=(8, 0))
        self.monte_carlo_button = ttk.Button(
            section, command=self.run_monte_carlo, state="disabled"
        )
        self.localizer.bind(self.monte_carlo_button, "monte_carlo")
        self.monte_carlo_button.pack(fill=tk.X, pady=(6, 0))

    def _install_controls_wheel_binding(self, widget: tk.Misc) -> None:
        """给左侧控件添加优先级滚轮绑定，避免 Combobox 改变选项。"""

        tags = widget.bindtags()
        if self._controls_wheel_tag not in tags:
            widget.bindtags((self._controls_wheel_tag, *tags))
        for child in widget.winfo_children():
            self._install_controls_wheel_binding(child)

    def _on_controls_mousewheel(self, event) -> str:
        """统一滚动左侧控制区，并阻止控件默认的滚轮行为。"""

        if event.num == 4:
            units = -1
        elif event.num == 5:
            units = 1
        else:
            delta = getattr(event, "delta", 0)
            units = -int(delta / 120) if delta else 0
            if units == 0 and delta:
                units = -1 if delta > 0 else 1
        if units:
            if self._controls_scrollable:
                self.controls_canvas.yview_scroll(units, "units")
        # 必须返回 break，阻止 ttk.Combobox/Spinbox 继续处理同一个滚轮事件。
        return "break"

    def _model_key(self) -> str:
        return self.localizer.choice_key("model", self.model_var.get())

    def _error_key(self) -> str:
        return self.localizer.choice_key("error", self.error_mode_var.get())

    def _selected_column(self, variable: tk.StringVar) -> str:
        selected = variable.get()
        names_by_label = {label: name for name, label in self._column_labels_by_name.items()}
        return names_by_label.get(selected, selected)

    def _refresh_column_choices(
        self,
        x_column: str | None = None,
        y_column: str | None = None,
        error_column: str | None = None,
    ) -> None:
        if self.dataset is None:
            return
        self._column_labels_by_name = localized_column_labels(
            self.dataset.column_names, self.localizer.language
        )
        labels = list(self._column_labels_by_name.values())
        for combo in (self.x_combo, self.y_combo):
            combo.configure(values=labels)
        self.x_column_var.set(
            self._column_labels_by_name.get(x_column or "", labels[0])
        )
        self.y_column_var.set(
            self._column_labels_by_name.get(y_column or "", labels[1])
        )
        if self._error_key() == "column":
            self.error_source_combo.configure(values=labels, state="readonly")
            self.error_source_var.set(
                self._column_labels_by_name.get(error_column or "", labels[-1])
            )

    def set_language(self, language: str) -> None:
        """切换完整 GUI 语言，同时保留数据、参数和拟合结果。"""

        if language == self.localizer.language:
            return
        model_key = self._model_key()
        error_key = self._error_key()
        x_column = self._selected_column(self.x_column_var)
        y_column = self._selected_column(self.y_column_var)
        error_column = (
            self._selected_column(self.error_source_var)
            if error_key == "column"
            else None
        )
        self.localizer.set_language(language)
        self.root.title(self.localizer.text("app_title"))
        self.model_var.set(self.localizer.choice_label("model", model_key))
        self.error_mode_var.set(self.localizer.choice_label("error", error_key))
        self.model_combo.configure(values=self.localizer.choices("model"))
        self.error_mode_combo.configure(values=self.localizer.choices("error"))
        self._refresh_column_choices(x_column, y_column, error_column)
        self._build_menu()
        self._refresh_file_and_metrics_text()
        self._on_model_changed(preserve_values=True, invalidate=False)
        reopen_subplots = hasattr(self.toolbar, "subplot_tool")
        if reopen_subplots:
            self.toolbar.subplot_tool.figure.canvas.manager.destroy()
        self.toolbar.destroy()
        self.toolbar = LocalizedNavigationToolbar2Tk(
            self.canvas,
            self.toolbar_frame,
            language=self.localizer.language,
            pack_toolbar=False,
        )
        self.toolbar.update()
        self.toolbar.pack(side=tk.LEFT)
        if reopen_subplots:
            self.toolbar.configure_subplots()
        for window, tree in list(self.preview_windows.items()):
            if window.winfo_exists() and self.dataset is not None:
                window.title(
                    self.localizer.text("preview_title", name=self.dataset.file_name)
                )
                for column in self.dataset.column_names:
                    tree.heading(
                        column,
                        text=self._column_labels_by_name.get(column, column),
                    )
            else:
                self.preview_windows.pop(window, None)
        if self.fit_result is None or self.cleaned_data is None:
            clear_figure(self.figure, self.localizer.language)
        else:
            draw_fit_result(
                self.figure,
                self.cleaned_data,
                self.fit_result,
                self.localizer.language,
                model_name(
                    self.fit_result.model_key,
                    self._read_degree(show_message=False)
                    if self.fit_result.model_key == "polynomial"
                    else None,
                    self.localizer.language,
                ),
            )
        self.canvas.draw_idle()
        self._render_status()

    def _refresh_file_and_metrics_text(self) -> None:
        if self.dataset is None:
            self.file_info_var.set(self.localizer.text("no_file"))
        else:
            self.file_info_var.set(
                self.localizer.text(
                    "file_info",
                    name=self.dataset.file_name,
                    encoding=self.dataset.encoding,
                    rows=self.dataset.original_rows,
                    columns=len(self.dataset.column_names),
                )
            )
        valid, removed = self._row_counts or ("--", "--")
        self.row_info_var.set(
            self.localizer.text("valid_removed", valid=valid, removed=removed)
        )
        if self.fit_result is None:
            self.r_squared_var.set(self.localizer.text("r_squared_empty"))
            self.rmse_var.set(self.localizer.text("rmse_empty"))
        else:
            self.r_squared_var.set(
                self.localizer.text("r_squared_na")
                if self.fit_result.r_squared is None
                else self.localizer.text(
                    "r_squared_value", value=f"{self.fit_result.r_squared:.6g}"
                )
            )
            self.rmse_var.set(
                self.localizer.text("rmse_value", value=f"{self.fit_result.rmse:.6g}")
            )

    def open_csv(self) -> None:
        """让用户选择 CSV，并把列名加载到界面。"""

        path = filedialog.askopenfilename(
            title=self.localizer.text("select_csv"),
            filetypes=[
                (self.localizer.text("csv_files"), "*.csv"),
                (self.localizer.text("all_files"), "*.*"),
            ],
        )
        if not path:
            return
        try:
            dataset = load_csv(path)
        except FittingFactoryError as exc:
            messagebox.showerror(
                self.localizer.text("csv_read_failed"),
                translate_message(str(exc), self.localizer.language),
                parent=self.root,
            )
            return

        self.dataset = dataset
        columns = dataset.column_names
        self._refresh_column_choices(columns[0], columns[1])
        for widget in (
            self.x_combo,
            self.y_combo,
            self.error_mode_combo,
            self.model_combo,
        ):
            widget.configure(state="readonly")
        for widget in (self.preview_button, self.guess_button, self.fit_button):
            widget.configure(state="normal")
        self._refresh_file_and_metrics_text()
        self._on_error_mode_changed()
        self._on_model_changed()
        self._invalidate_result("csv_loaded")

    def _on_error_mode_changed(self, _event=None) -> None:
        """根据误差模式切换误差来源控件的类型和状态。"""

        mode = self._error_key()
        if mode == "none":
            self.error_source_var.set("")
            self.error_source_combo.configure(values=[], state="disabled")
        elif mode == "column" and self.dataset is not None:
            error_column = self._selected_column(self.error_source_var)
            labels = list(self._column_labels_by_name.values())
            self.error_source_combo.configure(values=labels, state="readonly")
            self.error_source_var.set(
                self._column_labels_by_name.get(error_column, labels[-1])
            )
        else:
            # ttk.Combobox 的 normal 状态允许用户直接输入统一误差值。
            self.error_source_combo.configure(values=[], state="normal")
            if not self.error_source_var.get():
                self.error_source_var.set("0.1")
        self._invalidate_result("error_changed")

    def _on_model_changed(
        self, _event=None, *, preserve_values: bool = False, invalidate: bool = True
    ) -> None:
        """切换模型后重新生成参数输入框。"""

        if self.dataset is None:
            return
        model_key = self._model_key()
        degree = self._read_degree(show_message=False) if model_key == "polynomial" else None
        self.degree_spinbox.configure(state="normal" if model_key == "polynomial" else "disabled")
        if model_key == "polynomial" and degree is None:
            return
        try:
            spec = get_model_spec(model_key, degree)
        except FittingFactoryError:
            return
        self.formula_var.set(spec.formula)
        existing_values = {
            name: entry.get() for name, entry in self.parameter_entries.items()
        }
        for widget in self.parameter_frame.winfo_children():
            widget.destroy()
        self.parameter_entries.clear()
        default_values = [0.0] * len(spec.parameter_names)
        if default_values:
            default_values[0] = 1.0
        parameter_defaults = zip(
            spec.parameter_names,
            spec.parameter_descriptions
            if self.localizer.language == "zh"
            else english_parameter_descriptions(model_key, degree),
            default_values,
            strict=True,
        )
        for row, (name, description, default) in enumerate(parameter_defaults):
            entry = ttk.Entry(self.parameter_frame)
            entry.insert(
                0,
                existing_values.get(name, f"{default:g}")
                if preserve_values
                else f"{default:g}",
            )
            if self.localizer.language == "zh":
                ttk.Label(
                    self.parameter_frame,
                    text=f"{name}（{description}）",
                    wraplength=190,
                    justify=tk.LEFT,
                ).grid(row=row, column=0, sticky="w", pady=2)
                entry.grid(row=row, column=1, sticky="ew", padx=(6, 0), pady=2)
            else:
                grid_row = row * 2
                ttk.Label(self.parameter_frame, text=name).grid(
                    row=grid_row, column=0, sticky="w", pady=(2, 0)
                )
                entry.grid(
                    row=grid_row,
                    column=1,
                    sticky="ew",
                    padx=(6, 0),
                    pady=(2, 0),
                )
                ttk.Label(
                    self.parameter_frame,
                    text=description,
                    wraplength=290,
                    justify=tk.LEFT,
                    foreground="#5f6b7a",
                ).grid(
                    row=grid_row + 1,
                    column=0,
                    columnspan=2,
                    sticky="w",
                    pady=(0, 3),
                )
            entry.bind("<KeyRelease>", self._on_configuration_changed)
            self.parameter_entries[name] = entry
        self._install_controls_wheel_binding(self.parameter_frame)
        if invalidate:
            self._invalidate_result("model_changed")

    def _on_configuration_changed(self, _event=None) -> None:
        self._invalidate_result("config_changed")

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
            self._row_counts = (data.valid_rows, data.removed_rows)
            self.row_info_var.set(
                self.localizer.text(
                    "valid_removed", valid=data.valid_rows, removed=data.removed_rows
                )
            )
            self._invalidate_result("guess_ready")
            if warnings:
                messagebox.showwarning(
                    self.localizer.text("guess_warning"),
                    "\n".join(translate_message(w, self.localizer.language) for w in warnings),
                    parent=self.root,
                )
        except FittingFactoryError as exc:
            messagebox.showerror(
                self.localizer.text("guess_failed"),
                translate_message(str(exc), self.localizer.language),
                parent=self.root,
            )

    def run_fitting(self) -> None:
        """执行当前配置的曲线拟合，并刷新指标和图形。"""

        try:
            data, model_key, degree = self._prepare_current_data_and_model()
            initial_parameters = self._read_parameter_values()
            if model_key == "polynomial" and degree is not None and degree >= 6:
                proceed = messagebox.askyesno(
                    self.localizer.text("high_degree"),
                    self.localizer.text("high_degree_question"),
                    parent=self.root,
                )
                if not proceed:
                    return
            self.fit_button.configure(state="disabled")
            self._set_status("fitting")
            self.root.update_idletasks()
            result = fit_curve(data, FitConfig(model_key, degree, initial_parameters))
        except FittingFactoryError as exc:
            messagebox.showerror(
                self.localizer.text("fit_failed"),
                translate_message(str(exc), self.localizer.language),
                parent=self.root,
            )
            self._set_status("fit_failed_status")
            return
        finally:
            if self.dataset is not None:
                self.fit_button.configure(state="normal")

        self.cleaned_data = data
        self.fit_result = result
        self._row_counts = (data.valid_rows, data.removed_rows)
        self._refresh_file_and_metrics_text()
        draw_fit_result(
            self.figure,
            data,
            result,
            self.localizer.language,
            model_name(model_key, degree, self.localizer.language),
        )
        self.canvas.draw_idle()
        self.report_button.configure(state="normal")
        self.monte_carlo_button.configure(state="normal")
        self._set_status("fit_success")
        if result.warnings:
            messagebox.showwarning(
                self.localizer.text("fit_warning"),
                "\n".join(
                    translate_message(warning, self.localizer.language)
                    for warning in result.warnings
                ),
                parent=self.root,
            )

    def run_monte_carlo(self) -> None:
        """对当前拟合执行 1000 次有放回重采样并显示参数直方图。"""

        # 本函数由 AI 生成，已人工验证；

        if self.cleaned_data is None or self.fit_result is None:
            return
        degree = self._read_degree() if self.fit_result.model_key == "polynomial" else None
        config = FitConfig(
            self.fit_result.model_key,
            degree,
            self.fit_result.parameters.tolist(),
        )
        self.monte_carlo_button.configure(state="disabled")
        self._set_status("monte_carlo_running")
        self.root.update_idletasks()
        try:
            samples = bootstrap_parameters(self.cleaned_data, config)
        except FittingFactoryError as exc:
            messagebox.showerror(
                self.localizer.text("monte_carlo_failed"),
                translate_message(str(exc), self.localizer.language),
                parent=self.root,
            )
            self._set_status("fit_success")
            return
        finally:
            self.monte_carlo_button.configure(state="normal")

        window = tk.Toplevel(self.root)
        window.title(self.localizer.text("monte_carlo_title"))
        figure = create_parameter_histograms(
            samples, self.fit_result.parameter_names, self.localizer.language
        )
        canvas = FigureCanvasTkAgg(figure, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        window.figure = figure
        window.canvas = canvas
        window.geometry("850x650")
        self._set_status("monte_carlo_done")

    def export_report(self) -> None:
        """把当前有效拟合结果保存为 TXT。"""

        if self.dataset is None or self.cleaned_data is None or self.fit_result is None:
            messagebox.showinfo(
                self.localizer.text("no_result"),
                self.localizer.text("fit_first"),
                parent=self.root,
            )
            return
        output_path = filedialog.asksaveasfilename(
            title=self.localizer.text("save_report"),
            defaultextension=".txt",
            initialfile=suggested_report_name(self.dataset, self.fit_result),
            filetypes=[(self.localizer.text("text_files"), "*.txt")],
        )
        if not output_path:
            return
        try:
            report_text = build_report_text(self.dataset, self.cleaned_data, self.fit_result)
            saved_path = save_report(report_text, output_path)
        except FittingFactoryError as exc:
            messagebox.showerror(
                self.localizer.text("report_save_failed"),
                translate_message(str(exc), self.localizer.language),
                parent=self.root,
            )
            return
        self._set_status("report_saved_status", path=saved_path)
        messagebox.showinfo(
            self.localizer.text("save_success"),
            self.localizer.text("report_saved", path=saved_path),
            parent=self.root,
        )

    def show_data_preview(self) -> None:
        """在新窗口中显示 CSV 前 100 行，计算仍使用全部数据。"""

        if self.dataset is None:
            return
        window = tk.Toplevel(self.root)
        window.title(self.localizer.text("preview_title", name=self.dataset.file_name))
        window.geometry("850x500")
        frame = ttk.Frame(window, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(frame, columns=self.dataset.column_names, show="headings")
        self.preview_windows[window] = tree
        window.bind(
            "<Destroy>",
            lambda event: self.preview_windows.pop(window, None)
            if event.widget is window
            else None,
        )
        vertical = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        for column in self.dataset.column_names:
            tree.heading(column, text=self._column_labels_by_name.get(column, column))
            tree.column(column, width=120, anchor=tk.CENTER)
        for values in self.dataset.dataframe.head(100).itertuples(index=False, name=None):
            tree.insert("", tk.END, values=values)

    def _prepare_current_data_and_model(self) -> tuple[CleanedData, str, int | None]:
        """读取当前 GUI 选择，并返回清洗数据和模型标识。"""

        if self.dataset is None:
            raise ParameterValidationError(self.localizer.text("need_csv"))
        model_key = self._model_key()
        degree = self._read_degree() if model_key == "polynomial" else None
        error_mode = self._error_key()
        sigma_column = (
            self._selected_column(self.error_source_var)
            if error_mode == "column"
            else None
        )
        constant_sigma = self.error_source_var.get() if error_mode == "constant" else None
        data = prepare_data(
            self.dataset.dataframe,
            self._selected_column(self.x_column_var),
            self._selected_column(self.y_column_var),
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
                raise ParameterValidationError(self.localizer.text("degree_integer"))
            return None
        if not 1 <= degree <= 10:
            if show_message:
                raise ParameterValidationError(self.localizer.text("degree_range"))
            return None
        return degree

    def _read_parameter_values(self) -> list[float]:
        values: list[float] = []
        for name, entry in self.parameter_entries.items():
            try:
                value = float(entry.get())
            except ValueError as exc:
                raise ParameterValidationError(
                    self.localizer.text("parameter_number", name=name)
                ) from exc
            if not np.isfinite(value):
                raise ParameterValidationError(
                    self.localizer.text("parameter_finite", name=name)
                )
            values.append(value)
        return values

    def _invalidate_result(self, status_key: str) -> None:
        """配置变化后清除旧结果，避免导出与当前设置不一致的报告。"""

        self.cleaned_data = None
        self.fit_result = None
        self.r_squared_var.set(self.localizer.text("r_squared_empty"))
        self.rmse_var.set(self.localizer.text("rmse_empty"))
        if hasattr(self, "report_button"):
            self.report_button.configure(state="disabled")
        if hasattr(self, "monte_carlo_button"):
            self.monte_carlo_button.configure(state="disabled")
        if hasattr(self, "figure"):
            clear_figure(self.figure, self.localizer.language)
            self.canvas.draw_idle()
        self._set_status(status_key)

    def _set_status(self, key: str, **values) -> None:
        self._status_key = key
        self._status_values = values
        self._render_status()

    def _render_status(self) -> None:
        message = self.localizer.text(self._status_key, **self._status_values)
        self.status_var.set(self.localizer.text("status", message=message))

    def show_help(self) -> None:
        messagebox.showinfo(
            self.localizer.text("instructions"),
            self.localizer.text("help_text"),
            parent=self.root,
        )

    def show_about(self) -> None:
        messagebox.showinfo(
            self.localizer.text("about"),
            self.localizer.text("about_text"),
            parent=self.root,
        )
