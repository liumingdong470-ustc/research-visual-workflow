# 复杂 Origin 图

适用于需要直接在 Origin 打开修改的复杂二维图。交付完整 `figure.opj`、可加入已有项目的 `figure.ogg`、Origin 导出的 `preview.png` 和 `verification.json`。Windows 需安装可运行的 Origin。原生导出已在 Origin 2016 的独立自动化实例验证。

## 选择图形

| `kind` | 输入 | 原生对象 |
| --- | --- | --- |
| `grouped-bar` | 顺序固定的 `categories`，各系列给 `name`、`values` 和可选的对称 `errors` | 分组柱、独立的 Y Error 列和误差棒 |
| `stacked-bar` | 类别和完整的非负分量 | 同一类别的原生堆叠柱与分量图例 |
| `heatmap` | `matrix`、可选等间距 `x`、`y`、`scale` 和 `palette` | 数值矩阵、逐格色块和数值色标 |
| `panels` | `rows`、`columns` 和按行排列的 `panels` | 同一 Origin 图页中的独立图层和 a、b 等面板标签 |

柱图与 XY 面板可有 1–4 个系列。单系列柱使用 `grouped-bar`。面板支持 2–6 层，可混排上述图形与 `line`、`scatter`。折线和散点使用递增的数字 `x` 及对应 `series`。多面板标题用 `title`，轴标签用 `x_label`、`y_label`，热图色标用 `z_label`。混排热图的横轴名会与面板标题并排。需要跨面板比较数值时，为可比面板指定同一个 `y_range` 或 `scale`，并核对量纲。

## 数据约定

- `null` 表示缺测。分组柱及热图保留真实零值和缺测。热图支持最多 36 个缺测格，并为每格添加 `NA` 标记。数据更新后复核图上的缺测标注。
- 给出 `errors` 时同时给 `error_kind`，例如 `SD`、`SEM` 或 `95% CI half-width`。当前输入使用非负对称误差量，误差量与柱值须一一对应。核实样本量和误差定义，在图注说明。
- 堆叠柱使用可相加的分量。数据缺失时先确认其处理方式。按百分比展示时，明确归一化分母并单独保留原始分量。
- 热图矩阵第一行对应最小 `y`，显示在图的上方。列从左到右对应递增的 `x`。省略坐标时采用从 1 开始的索引。`palette` 可用 `sequential` 或 `diverging`。发散色标的 `scale` 须围绕 0 对称。
- `y_range` 须覆盖所有观察值和误差，并包含柱图的 0 基线。热图 `scale` 覆盖全部实测格。数值、类别顺序和方向以用户输入为准。

## 命令

在 Skill 目录运行。先用 `--dry-run` 检查输入，实际导出时去掉该参数。旧版 COM 如果注册在 32 位表中，使用下面的 PowerShell 路径。在可使用原生位数 COM 的环境下可省略 `--powershell`。

```powershell
python scripts/origin_complex.py --spec figure-spec.json --output-dir result-native --powershell "$env:WINDIR/SysWOW64/WindowsPowerShell/v1.0/powershell.exe"
```

完整仓库根目录的 `examples/origin-complex/` 提供六份合成输入。按需要从 CSV、Excel 或用户提供的数据准备一份 JSON。复杂图脚本使用 `default`、`clean` 或 `skill` 内置主题，热图使用顺序或发散色阶。需要统一成私有参考配色时，在 Origin 中调整并复核柱图、曲线和色标。输出目录使用新名称，保留源数据和现有工程。

## 成品检查

逐项回读 OPJ 和独立 OGG 中的工作表、矩阵和缺测位置，检查图层数、绑定的数据列和色标范围。另在内存中验证原生数据可修改。核对 PNG 中误差棒、柱基线、矩阵方向和面板标签的实际显示。需要不对称误差、双轴、自定义嵌套图层或非等距热图时按实际 Origin 模板制作，并独立验证。

- [Origin 误差棒数据列](https://docs.originlab.com/quick-help/errbar-display-in-plot/)
- [矩阵图像图和单元格](https://docs.originlab.com/origin-help/image-plot)
- [原生图层合并](https://docs.originlab.com/x-function/ref/merge_graph/)
