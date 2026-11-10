# 直接在 Origin 打开和编辑

## 交付约定

用户说“图片直接导入 Origin 后编辑”“可修改曲线”“给我 Origin 源文件”时，交付真正的 Origin 原生文件。

- `figure.opj` 为完整工程，内含数值表、曲线、坐标轴、图例和其他原生对象，兼容 Origin 2016。
- `figure.ogg` 为可直接加入现有项目的单图文件。导出前在独立实例中设置 `@sow=1`，使单图携带工作簿数据，并验证单独打开后的数据与曲线。
- `preview.png` 用于预览。修改曲线、样式和数据时打开 OPJ 或 OGG。

新版本可按用户要求保存 OPJU/OGGU，但需由兼容版本实际另存并重新验证。用户当前用 Origin 2016 时优先交付 OPJ/OGG。

生成任务可使用原始数据或明确的合成数据，Skill 自动建表、出图和封装。用户打开交付文件即可编辑。只有截图时，源曲线重建仍需用户授权数字化，并注明近似性；图像像素本身不提供精确的源数据。

## 辅助脚本

在 Windows 上使用已安装且许可可用的 Origin，通过独立的 `Origin.ApplicationSI` 实例运行，不触碰用户已打开的工程。脚本将准备好的数据直接写入 Origin 内部表格并绘图，用户无需手工导入 CSV。

~~~powershell
python scripts/origin_native.py --csv data.csv --kind xrd --x angle --y sample-A --y sample-B --y-label "Intensity (counts)" --output-dir result-native
~~~

辅助脚本支持数值 X 轴的折线、散点和 XRD、Raman、FTIR 图谱。空白 Y 保留缺测，FTIR 默认波数降序。可用 `--x-range`、`--x-direction`、`--x-label` 和 `--profile` 控制范围、方向和颜色。`--offset` 将原始列和显示偏移列同时封装，并标明偏移。

`--dry-run` 只检查输入。`--output-dir` 须为新目录，验证通过后才交付成品目录。若 COM 注册在 32 位表中，指定 `--powershell` 指向系统 `SysWOW64/WindowsPowerShell/v1.0/powershell.exe`。图谱列名和轴标题使用纯文本，避免 LabTalk 命令字符。旧版 Origin 的中文和特殊字符需在目标机器检查。

## 实际验证

1. 保存 OPJ 后在独立实例里重新打开，逐项比对工作表数值和缺测位置。
2. 确认曲线是连接工作表的原生绘图对象，并在内存中修改一条曲线属性来验证可编辑性。
3. 在新项目中单独打开 OGG，确认无需外部数据文件仍有曲线与相应数据。
4. 导出并检查 PNG，核对坐标方向、单位、图例、断线与裁切。

运行失败时保留输入并给出实际阻塞原因，可交付验证过的数据准备或脚本。把重新打开且通过检查的原生对象作为交付依据。分组柱图、误差棒、堆叠柱图、矩阵热图和混合多面板走 [复杂 Origin 图](origin-complex.md)。编辑既有原生工程先另存副本。

## 来源

- [Origin COM 建页与数据传输](https://docs.originlab.com/com/classes/application/createpage/)
- [Origin COM 保存工程](https://docs.originlab.com/com/classes/application/save/)
- [OGG 携带工作簿数据的设置，Origin 2016 起支持](https://docs.originlab.com/quick-help/how-to-save-column-label-with-graph/)
