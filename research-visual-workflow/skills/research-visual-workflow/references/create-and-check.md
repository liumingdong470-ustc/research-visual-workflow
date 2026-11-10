# 科研图、Origin 与可编辑 PPT

## 科研图

XRD、拉曼和 FTIR 优先按 [图谱编辑](spectra.md) 核对横纵轴、缺测与标注来源。

使用真实数据；先核对列名、单位、缺失值、重复与误差。现成脚本支持 CSV 单横轴、多系列折线或散点，缺失 Y 保留断点。运行前安装 Matplotlib：

~~~powershell
python scripts/plot_csv.py --csv "D:\Work\data.csv" --x time --y control --y treatment --x-label "Time (min)" --y-label "Response (a.u.)" --output "D:\Work\figure.svg"
~~~

用 `--profile` 复用私有风格。投稿图可设置 `--width-mm`、`--height-mm`、`--font-size` 和 `--dpi`，输出 PNG、SVG 或 PDF。复杂图可用 [原生 Origin](origin-complex.md)，或按实际数据另编可复现绘图代码。编辑已有图优先使用源数据。只有位图时说明编辑范围。参考图只提供视觉线索，实验参数、误差和结论以当前数据及方法为准。

## Origin

需要直接打开编辑时按 [原生 Origin 交付](origin-native.md) 生成包含数据的 OPJ、OGG 与预览。新辅助脚本通过 Windows 的 Origin 自动化接口运行，可用于旧版 Origin 2016，无需 originpro。原有 `visual_suite.py origin` 仍适用于已具备兼容 Origin 与 originpro 的 OPJU 路线。只有软件实际保存、重新打开并验证后才报告原生工程完成。解析原有工程时用副本和兼容查看工具，区分图页、缩略图和原始表格。

## PowerPoint

复用颜色和版式层级，保留原生文字、表格和适用的原生图表。编辑已有 PPT 先检查源文件并另存新版。`visual_suite.py ppt` 按 [版式字段](deck-spec.md) 从 deck JSON 和风格 JSON 新建包含可编辑文字与形状的基础演示稿。改现有演示稿、复杂版式或制作 PowerPoint 原生图表时，使用当前环境可用的演示文稿编辑工具。打开或渲染检查页数、文字溢出、对齐和图例，核对图表与数据来源，说明可编辑范围。
