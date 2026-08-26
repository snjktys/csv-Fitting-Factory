# CSV 数据曲线拟合工厂

这是《Python 课程设计指导书》第 38 题的桌面程序。用户无需编写代码，即可导入 CSV 数据，选择数学模型，完成曲线拟合并查看残差、R² 和 RMSE。

## 一、已实现功能

- Tkinter + ttk 桌面图形界面；
- 读取 UTF-8-SIG、UTF-8、GB18030 编码的 CSV；
- 支持中文文件名和中文表头；
- 选择 X、Y 数据列；
- 三种误差模式：无误差、CSV 误差列、统一误差值；
- 多项式、指数、正弦、Logistic 四种模型；
- 手动参数输入与智能初值；
- 使用 `scipy.optimize.curve_fit` 拟合；
- 显示原始数据、误差棒、拟合曲线和残差图；
- 计算 R²、RMSE 和参数标准误差；
- 预览 CSV 前 100 行；
- 导出 UTF-8-SIG 编码的 TXT 拟合报告；
- 对文件、数据、参数、拟合和报告保存错误提供中文提示。

## 二、运行环境

- Windows 10/11；
- Python 3.10～3.12；
- 依赖见 `requirements.txt`。

## 三、安装依赖

请在项目根目录打开 PowerShell 或终端，然后执行：

```powershell
python -m pip install -r requirements.txt
```

建议使用 Conda 或 Python 虚拟环境，避免依赖影响其他项目。

## 四、启动程序

在项目根目录执行：

```powershell
python -m src.main
```

如果电脑上有多个 Python，也可以填写 Python 的完整路径后运行。

## 五、使用步骤

1. 点击“打开 CSV”，选择带表头的 CSV 文件；
2. 选择 X 列和 Y 列；
3. 选择误差模式：
   - “无误差”：不绘制误差棒；
   - “CSV 误差列”：从文件中选择一列有限正数作为误差；
   - “统一误差值”：输入一个正数，例如 `0.1`；
4. 选择多项式、指数、正弦或 Logistic 模型；
5. 点击“智能初值”，也可以手动修改参数；
6. 点击“开始拟合”；
7. 查看拟合图、残差图、R² 和 RMSE；
8. 点击“生成 TXT 报告”保存结果。

## 六、示例数据

`data` 目录包含四份可以直接演示的 CSV：

| 文件 | 建议模型 | X 列 | Y 列 | 误差列 |
|---|---|---|---|---|
| `polynomial_sample.csv` | 二阶多项式 | `x` | `y` | `error` |
| `exponential_sample.csv` | 指数 | `x` | `y` | `error` |
| `sine_sample.csv` | 正弦 | `time` | `signal` | `error` |
| `logistic_sample.csv` | Logistic | `x` | `y` | `error` |

## 七、运行测试

```powershell
python -m pytest -q
```

当前版本自动化测试结果为 `27 passed`。测试报告位于 `docs/测试报告.md`。

## 八、项目结构

```text
csv-Fitting-Factory/
├─ data/                  # 四种模型的示例 CSV
├─ docs/                  # 需求、设计、测试和过程文档
├─ src/                   # 程序源代码
├─ tests/                 # 自动化测试
├─ AI_USAGE.md            # AI 使用说明
├─ README.md              # 本运行说明
├─ requirements.txt       # Python 依赖
└─ .gitignore             # Git 忽略规则
```

## 九、常见问题

### 1. CSV 打不开

检查文件是否为 `.csv`，并尝试将文件另存为 UTF-8 CSV。程序会自动尝试 UTF-8-SIG、UTF-8 和 GB18030。

### 2. 拟合失败

先点击“智能初值”；仍失败时检查模型是否适合数据，或调整参数、缩放 X 数据。

### 3. 没有显示误差棒

只有选择“CSV 误差列”或“统一误差值”时才绘制误差棒。误差必须是有限正数。

### 4. 高阶多项式出现警告

6～10 阶多项式容易过拟合或在数据边缘振荡。一般实验数据优先尝试 1～5 阶。

### 5. R² 显示 N/A

如果全部 Y 值相同，R² 在数学上没有定义，程序会显示 N/A。

## 十、AI 使用提醒

本项目当前源代码主要由 AI 辅助生成，并经过自动化测试和运行检查。按照课程要求，提交前学生本人必须逐个模块阅读、运行、修改和理解，确保能够在答辩中解释核心逻辑并现场修改。详细记录见 `AI_USAGE.md`。
