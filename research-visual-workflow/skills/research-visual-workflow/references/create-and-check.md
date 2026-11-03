# 科研图、Origin 与可编辑 PPT

## 科研图

使用真实数据；先核对列名、单位、缺失值、重复与误差。现成脚本支持 CSV 单横轴、多系列折线或散点，缺失 Y 保留断点。运行前安装 Matplotlib：

~~~powershell
python scripts/plot_csv.py --csv "D:\Work\data.csv" --x time --y control --y treatment --x-label "Time (min)" --y-label "Response (a.u.)" --output "D:\Work\figure.svg"
~~~

可加 --profile 指向私有 JSON。脚本输出 PNG、SVG 或 PDF；复杂图（误差棒、多面板、拟合）根据实际数据另编可复现绘图代码。不能从参考图复制实验参数、误差和结论。编辑已有数据图时优先用源数据重绘；只有位图时说明编辑局限。检查对比度、组别区分、裁切与轴单位。

## Origin

Windows 需要兼容的 Origin/OriginPro 与 originpro。用 visual_suite.py origin，先以 --dry-run 核对数据。只有软件实际导出并检查 OPJU 与 PNG 后才报告可编辑工程完成。旧版本环境可用 Python 画图，不能把 SVG 或 PNG 当作 OPJU。解析原有 OPJU 时用副本和兼容查看工具，区分图页、缩略图和原始表格。

## PowerPoint

复用颜色和版式层级，保留原生文字、表格和适用的原生图表。编辑已有 PPT 先检查源文件并另存新版。基础生成可用 visual_suite.py ppt，按 [版式字段](deck-spec.md) 提供 deck JSON 和风格 JSON；复杂版式或原生图表使用当前环境的演示文稿工具。打开或渲染检查页数、文字溢出、对齐和图例；核对图表与数据来源，说明可编辑范围。
