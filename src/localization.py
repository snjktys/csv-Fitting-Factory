# 本代码由 AI 辅助生成，已人工验证。
"""GUI 中英文文本、选项映射和模型说明。"""

from __future__ import annotations

import re
import tkinter as tk

TEXTS = {
    "zh": {
        "app_title": "CSV 数据曲线拟合工厂",
        "file": "文件",
        "open_csv": "打开 CSV",
        "export_report": "导出 TXT 报告",
        "exit": "退出",
        "help": "帮助",
        "instructions": "使用说明",
        "about": "关于",
        "language": "界面语言",
        "chinese": "中文",
        "english": "English",
        "section_file": "1  数据文件",
        "section_columns": "2  数据列与误差",
        "section_model": "3  拟合模型与参数",
        "section_result": "4  拟合结果",
        "x_column": "X 列",
        "y_column": "Y 列",
        "error_mode": "误差模式",
        "error_source": "误差来源",
        "data_preview": "数据预览",
        "model": "模型",
        "degree": "阶次",
        "formula": "公式",
        "parameters": "参数",
        "smart_initial": "智能初值",
        "start_fitting": "开始拟合",
        "generate_report": "生成 TXT 报告",
        "monte_carlo": "蒙特卡洛分析（1000 次）",
        "no_file": "尚未选择文件",
        "valid_removed": "有效数据：{valid}　删除数据：{removed}",
        "status": "状态：{message}",
        "waiting_csv": "等待导入 CSV 文件",
        "csv_loaded": "CSV 加载成功，请确认列和模型。",
        "error_changed": "误差设置已改变，需要重新拟合。",
        "model_changed": "模型或参数已改变，需要重新拟合。",
        "config_changed": "数据列或参数已改变，需要重新拟合。",
        "guess_ready": "智能初值已生成，可以开始拟合。",
        "fitting": "正在进行曲线拟合...",
        "fit_failed_status": "拟合失败，请检查数据和参数。",
        "fit_success": "拟合成功，可以查看图形或生成报告。",
        "monte_carlo_running": "正在执行 1000 次蒙特卡洛重采样...",
        "monte_carlo_done": "蒙特卡洛分析完成。",
        "monte_carlo_failed": "蒙特卡洛分析失败",
        "monte_carlo_title": "参数分布",
        "report_saved_status": "报告已保存：{path}",
        "file_info": "{name}\n编码：{encoding}　{rows} 行 × {columns} 列",
        "r_squared_empty": "R²：--",
        "r_squared_na": "R²：N/A",
        "r_squared_value": "R²：{value}",
        "rmse_empty": "RMSE：--",
        "rmse_value": "RMSE：{value}",
        "select_csv": "选择 CSV 文件",
        "csv_files": "CSV 文件",
        "all_files": "所有文件",
        "csv_read_failed": "CSV 读取失败",
        "guess_warning": "智能初值提示",
        "guess_failed": "智能初值失败",
        "high_degree": "高阶多项式提示",
        "high_degree_question": "6～10 阶多项式可能过拟合或在边缘振荡，是否继续？",
        "fit_failed": "拟合失败",
        "fit_warning": "拟合结果提示",
        "no_result": "暂无结果",
        "fit_first": "请先完成一次成功拟合。",
        "save_report": "保存拟合报告",
        "text_files": "文本文件",
        "report_save_failed": "报告保存失败",
        "save_success": "保存成功",
        "report_saved": "拟合报告已保存到：\n{path}",
        "preview_title": "数据预览 - {name}",
        "help_text": (
            "1. 打开带表头的 CSV 文件。\n"
            "2. 选择 X、Y 和误差模式。\n"
            "3. 选择模型，并使用智能初值或手动输入参数。\n"
            "4. 点击开始拟合，查看拟合图、残差、R² 和 RMSE。\n"
            "5. 拟合成功后生成 TXT 报告。"
        ),
        "about_text": "CSV 数据曲线拟合工厂\nPython 课程设计第 38 题\n支持多项式、指数、正弦和 Logistic 拟合。",
        "need_csv": "请先导入 CSV 文件。",
        "degree_integer": "多项式阶次必须是 1～10 的整数。",
        "degree_range": "多项式阶次必须在 1～10 之间。",
        "parameter_number": "参数 {name} 必须是数字。",
        "parameter_finite": "参数 {name} 必须是有限数值。",
    },
    "en": {
        "app_title": "CSV Curve Fitting Factory",
        "file": "File",
        "open_csv": "Open CSV",
        "export_report": "Export TXT Report",
        "exit": "Exit",
        "help": "Help",
        "instructions": "Instructions",
        "about": "About",
        "language": "Language",
        "chinese": "中文",
        "english": "English",
        "section_file": "1  Data File",
        "section_columns": "2  Data Columns and Error",
        "section_model": "3  Fitting Model and Parameters",
        "section_result": "4  Fitting Results",
        "x_column": "X Column",
        "y_column": "Y Column",
        "error_mode": "Error Mode",
        "error_source": "Error Source",
        "data_preview": "Data Preview",
        "model": "Model",
        "degree": "Degree",
        "formula": "Formula",
        "parameters": "Parameters",
        "smart_initial": "Smart Initial Guess",
        "start_fitting": "Start Fitting",
        "generate_report": "Generate TXT Report",
        "monte_carlo": "Monte Carlo Analysis (1000)",
        "no_file": "No file selected",
        "valid_removed": "Valid rows: {valid}   Removed rows: {removed}",
        "status": "Status: {message}",
        "waiting_csv": "Waiting for a CSV file",
        "csv_loaded": "CSV loaded. Confirm the columns and model.",
        "error_changed": "Error settings changed. Fit again.",
        "model_changed": "Model or parameters changed. Fit again.",
        "config_changed": "Data columns or parameters changed. Fit again.",
        "guess_ready": "Initial values generated. Ready to fit.",
        "fitting": "Fitting curve...",
        "fit_failed_status": "Fitting failed. Check the data and parameters.",
        "fit_success": "Fitting succeeded. View the plots or generate a report.",
        "monte_carlo_running": "Running 1,000 Monte Carlo resamples...",
        "monte_carlo_done": "Monte Carlo analysis completed.",
        "monte_carlo_failed": "Monte Carlo Analysis Failed",
        "monte_carlo_title": "Parameter Distributions",
        "report_saved_status": "Report saved: {path}",
        "file_info": "{name}\nEncoding: {encoding}   {rows} rows × {columns} columns",
        "r_squared_empty": "R²: --",
        "r_squared_na": "R²: N/A",
        "r_squared_value": "R²: {value}",
        "rmse_empty": "RMSE: --",
        "rmse_value": "RMSE: {value}",
        "select_csv": "Select a CSV File",
        "csv_files": "CSV Files",
        "all_files": "All Files",
        "csv_read_failed": "CSV Read Failed",
        "guess_warning": "Initial Guess Warning",
        "guess_failed": "Initial Guess Failed",
        "high_degree": "High-degree Polynomial Warning",
        "high_degree_question": (
            "Polynomial degrees 6–10 may overfit or oscillate near the edges. "
            "Continue?"
        ),
        "fit_failed": "Fitting Failed",
        "fit_warning": "Fitting Warning",
        "no_result": "No Result",
        "fit_first": "Complete a successful fit first.",
        "save_report": "Save Fitting Report",
        "text_files": "Text Files",
        "report_save_failed": "Report Save Failed",
        "save_success": "Saved",
        "report_saved": "Fitting report saved to:\n{path}",
        "preview_title": "Data Preview - {name}",
        "help_text": (
            "1. Open a CSV file with headers.\n"
            "2. Select X, Y, and an error mode.\n"
            "3. Select a model and use a smart guess or enter parameters manually.\n"
            "4. Start fitting and inspect the fit, residuals, R², and RMSE.\n"
            "5. Generate a TXT report after a successful fit."
        ),
        "about_text": (
            "CSV Curve Fitting Factory\n"
            "Python Course Project, Topic 38\n"
            "Supports polynomial, exponential, sine, and logistic fitting."
        ),
        "need_csv": "Open a CSV file first.",
        "degree_integer": "Polynomial degree must be an integer from 1 to 10.",
        "degree_range": "Polynomial degree must be between 1 and 10.",
        "parameter_number": "Parameter {name} must be a number.",
        "parameter_finite": "Parameter {name} must be finite.",
    },
}

MODEL_LABELS = {
    "zh": {
        "polynomial": "多项式",
        "exponential": "指数",
        "sine": "正弦",
        "logistic": "Logistic",
    },
    "en": {
        "polynomial": "Polynomial",
        "exponential": "Exponential",
        "sine": "Sine",
        "logistic": "Logistic",
    },
}
ERROR_LABELS = {
    "zh": {"none": "无误差", "column": "CSV 误差列", "constant": "统一误差值"},
    "en": {"none": "No Error", "column": "CSV Error Column", "constant": "Constant Error"},
}

ENGLISH_COLUMN_LABELS = {
    "输入量": "Input",
    "输出量": "Output",
    "误差": "Error",
    "自变量": "Independent Variable",
    "因变量": "Dependent Variable",
    "测量误差": "Measurement Error",
    "横坐标": "X Coordinate",
    "纵坐标": "Y Coordinate",
    "时间": "Time",
    "信号": "Signal",
    "温度": "Temperature",
}

PARAMETER_DESCRIPTIONS = {
    "en": {
        "exponential": (
            "scale (offset from baseline at x=0)",
            "growth or decay rate",
            "vertical offset (baseline)",
        ),
        "sine": (
            "amplitude",
            "frequency (cycles per x unit)",
            "phase (radians)",
            "vertical offset",
        ),
        "logistic": (
            "difference between plateaus",
            "growth/decay rate (+ rising, − falling)",
            "x value at the midpoint",
            "lower-plateau baseline",
        ),
    },
}


class Localizer:
    """保存当前语言，并集中刷新已登记控件的文本。"""

    def __init__(self, language: str = "zh") -> None:
        """设置初始语言并创建控件绑定表。"""

        self.language = language
        self._bindings: list[tuple[tk.Misc, str]] = []

    def text(self, key: str, **values) -> str:
        """返回当前语言的格式化文本。"""

        return TEXTS[self.language][key].format(**values)

    def bind(self, widget: tk.Misc, key: str):
        """登记控件及其文本键，并立即设置文本。"""

        self._bindings.append((widget, key))
        widget.configure(text=self.text(key))
        return widget

    def set_language(self, language: str) -> None:
        """切换语言并刷新仍然存在的已登记控件。"""

        if language not in TEXTS:
            raise ValueError(f"Unsupported language: {language}")
        self.language = language
        for widget, key in self._bindings:
            if widget.winfo_exists():
                widget.configure(text=self.text(key))

    def choices(self, kind: str) -> list[str]:
        """返回模型或误差模式的当前语言选项。"""

        labels = MODEL_LABELS if kind == "model" else ERROR_LABELS
        return list(labels[self.language].values())

    def choice_label(self, kind: str, key: str) -> str:
        """把内部选项标识转换为当前语言标签。"""

        labels = MODEL_LABELS if kind == "model" else ERROR_LABELS
        return labels[self.language][key]

    @staticmethod
    def choice_key(kind: str, label: str) -> str:
        """把任一支持语言的标签还原为内部标识。"""

        labels = MODEL_LABELS if kind == "model" else ERROR_LABELS
        for language_labels in labels.values():
            for key, value in language_labels.items():
                if value == label:
                    return key
        raise KeyError(label)


def model_name(model_key: str, degree: int | None, language: str) -> str:
    """返回适合图表显示的本地化模型名称。"""

    if model_key == "polynomial":
        return f"{degree} 阶多项式" if language == "zh" else f"Degree {degree} Polynomial"
    if language == "zh":
        return {"exponential": "指数模型", "sine": "正弦模型", "logistic": "Logistic 模型"}[model_key]
    return f"{MODEL_LABELS[language][model_key]} Model"


def english_parameter_descriptions(model_key: str, degree: int | None) -> tuple[str, ...]:
    """返回与模型参数顺序一致的英文说明。"""

    if model_key != "polynomial":
        return PARAMETER_DESCRIPTIONS["en"][model_key]
    return ("constant term (coefficient of x⁰)",) + tuple(
        f"coefficient of x^{i}" for i in range(1, (degree or 0) + 1)
    )


def localized_column_labels(columns: list[str], language: str) -> dict[str, str]:
    """返回原始列名到显示名的映射；无法可靠翻译的名称保持不变。"""

    if language == "zh":
        return dict(zip(columns, columns, strict=True))
    labels = [ENGLISH_COLUMN_LABELS.get(column, column) for column in columns]
    return {
        column: label if labels.count(label) == 1 else column
        for column, label in zip(columns, labels, strict=True)
    }


_EXACT_MESSAGES = {
    "高阶多项式可能过拟合或在数据边缘产生振荡。": (
        "High-degree polynomials may overfit or oscillate near the data edges."
    ),
    "参数协方差无法可靠估计，请谨慎解释参数误差。": (
        "Parameter covariance could not be estimated reliably; interpret parameter "
        "errors with caution."
    ),
    "指数初值采用了安全默认值，必要时请手动调整。": (
        "Safe default exponential initial values were used; adjust them manually "
        "if needed."
    ),
    "X 列和 Y 列不能选择同一列。": "X and Y cannot use the same column.",
    "选择的 X 或 Y 列不存在。": "The selected X or Y column does not exist.",
    "请选择有效的 CSV 误差列。": "Select a valid CSV error column.",
    "统一误差值必须是数字。": "The constant error value must be numeric.",
    "统一误差值必须是有限正数。": "The constant error value must be finite and positive.",
    "清洗后没有有效数值，请更换数据列或修正 CSV。": (
        "No valid numeric rows remain. Select other columns or correct the CSV file."
    ),
    "X 数据没有变化，无法进行曲线拟合。": "X values do not vary, so curve fitting is not possible.",
    "CSV 文件不存在，请重新选择文件。": "The CSV file does not exist. Select it again.",
    "请选择扩展名为 .csv 的文件。": "Select a file with the .csv extension.",
    "CSV 文件为空，没有可以读取的数据。": "The CSV file is empty.",
    "CSV 格式无法解析，请检查分隔符和每行列数。": (
        "The CSV format could not be parsed. Check the delimiter and column count."
    ),
    "没有读取该文件的权限，请关闭占用程序或更换文件。": (
        "The file cannot be read. Close any program using it or choose another file."
    ),
    "CSV 文件没有数据行。": "The CSV file has no data rows.",
    "CSV 至少需要两列数据，才能选择 X 和 Y。": "The CSV file needs at least two columns for X and Y.",
    "X 和 Y 必须是长度相同的非空数组。": "X and Y must be non-empty arrays of equal length.",
    "智能初值只能使用有限数值。": "Smart initial guesses require finite values.",
    "多项式初值估计失败，请降低阶次。": "Polynomial initial estimation failed. Reduce the degree.",
    "X 数据没有范围，无法估计指数初值。": "X has no range, so exponential initial values cannot be estimated.",
    "X 数据没有范围，无法估计正弦初值。": "X has no range, so sine initial values cannot be estimated.",
    "X 间隔不均匀，正弦频率使用 1/X范围 作为初值。": (
        "X spacing is uneven; 1/X range was used as the initial sine frequency."
    ),
    "有效采样间隔较少，正弦频率使用安全默认值。": (
        "Too few valid sampling intervals; a safe default sine frequency was used."
    ),
    "Y 数据变化太小，不适合 Logistic 拟合。": "Y varies too little for logistic fitting.",
    "X 数据没有范围，无法估计 Logistic 初值。": (
        "X has no range, so logistic initial values cannot be estimated."
    ),
    "所有初始参数都必须是数字。": "All initial parameters must be numeric.",
    "所有初始参数都必须是有限数值。": "All initial parameters must be finite.",
    "拟合参数会导致模型计算溢出，请调整初值或数据尺度。": (
        "The fitted parameters overflow the model. Adjust the initial values or data "
        "scale."
    ),
    "拟合结果包含无效数值，请调整初值或数据尺度。": (
        "The fitting result contains invalid values. Adjust the initial values or data "
        "scale."
    ),
    "蒙特卡洛重采样次数必须大于 0。": "The Monte Carlo iteration count must be greater than zero.",
    "蒙特卡洛重采样全部失败，请检查数据或拟合参数。": (
        "All Monte Carlo resamples failed. Check the data or fitting parameters."
    ),
    "无法识别 CSV 编码，请将文件另存为 UTF-8 或 GB18030 后重试。": (
        "The CSV encoding could not be detected. Save the file as UTF-8 or GB18030 "
        "and try again."
    ),
    "选择多项式模型时必须设置阶次。": "A degree is required for the polynomial model.",
    "未知的误差模式。": "Unknown error mode.",
    "模型参数数量必须大于 0。": "The model must have at least one parameter.",
}


def translate_message(message: str, language: str) -> str:
    """翻译业务层常见中文提示；未知文本原样保留。"""

    if language == "zh":
        return message
    if message in _EXACT_MESSAGES:
        return _EXACT_MESSAGES[message]
    replacements = (
        (r"参数 (.+) 必须是数字。", r"Parameter \1 must be a number."),
        (r"参数 (.+) 必须是有限数值。", r"Parameter \1 must be finite."),
        (
            r"有效数据点只有 (\d+) 个，必须多于模型的 (\d+) 个参数。",
            r"Only \1 valid data points remain; more than \2 model parameters are required.",
        ),
        (
            r"不同的 X 只有 (\d+) 个，至少需要 (\d+) 个。",
            r"Only \1 distinct X values remain; at least \2 are required.",
        ),
        (
            r"当前模型需要 (\d+) 个初始参数。",
            r"The current model requires \1 initial parameters.",
        ),
        (r"未知的拟合模型：(.+)", r"Unknown fitting model: \1"),
        (
            r"读取 CSV 时发生系统错误：(.+)",
            r"A system error occurred while reading the CSV: \1",
        ),
        (
            r"报告保存失败，请更换保存位置：(.+)",
            r"The report could not be saved. Choose another location: \1",
        ),
        (
            r"指数拟合失败，请使用智能初值，或缩放 X 数据后重试。(.*)",
            r"Exponential fitting failed. Use a smart initial guess or rescale X and try again.\1",
        ),
        (
            r"拟合没有收敛，请使用智能初值或调整参数后重试。(.*)",
            r"Fitting did not converge. Use a smart initial guess or adjust the parameters.\1",
        ),
    )
    for pattern, replacement in replacements:
        if re.fullmatch(pattern, message):
            return re.sub(pattern, replacement, message)
    return message
