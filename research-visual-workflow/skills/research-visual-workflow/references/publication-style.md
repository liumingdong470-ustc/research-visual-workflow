# 论文图与样式对照

1. **先定尺寸。** 用目标期刊的最终栏宽、字号与文件格式。以 Nature 主刊为例，官方指南列出单栏 89 mm、双栏 183 mm、图中文字 5–7 pt。按实际成品尺寸查看标签、线条和面板间距。[Nature 制图指南](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/)
2. **保留数据含义。** 图注说明样本量与误差定义，缺测和真实零值分开显示。分组用颜色配合线型、点形或纹理。可比热图共用色标，只有存在有意义的中心值时用发散色阶。
3. **导出并检查。** 折线与散点可用 `plot_csv.py` 指定毫米尺寸、字号及位图分辨率。图谱可用 `plot_spectra.py` 指定毫米尺寸。核对坐标轴、图例、面板标签和所用字体。保留矢量输出及源文件；最终提交格式按期刊要求。
4. **公平对照。** 对比默认版、整合 Skill 版和按论文规范制作的版本时，使用同一数据、相同轴范围、单位与缺测规则。记录真正改变的配色、线型、字号和布局。要称为某第三方 Skill 的实测版本，需实际调用该 Skill 并记录版本。

以下命令从完整仓库根目录运行，用合成数据测试单栏折线。实际投稿时按期刊与图形内容复核。

```powershell
python skills/research-visual-workflow/scripts/plot_csv.py --csv examples/data.csv --x time --y control --y treatment --x-label "Time (min)" --y-label "Response (a.u.)" --width-mm 89 --height-mm 55 --font-size 7 --output outputs/paper.svg
```
