# Research Visual Workflow｜科研图、Origin 与 PPT

一个 Codex Skill，从参考图提取风格、整理私有图库，再用自己的数据制作科研图和可编辑演示稿。入口为 [SKILL.md](skills/research-visual-workflow/SKILL.md)。

| 你想做什么 | 在 Codex 发送的示例指令 |
| --- | --- |
| [分析参考图并入库](skills/research-visual-workflow/references/private-library.md) | `$research-visual-workflow 把附件逐张命名、打标签，说明适合的科研图和 PPT 场景，并加入我的私有库。` |
| [科研图与投稿排版](skills/research-visual-workflow/references/publication-style.md) | `$research-visual-workflow 用附件数据做论文折线图，按目标期刊的单栏宽度导出 SVG 和 PNG。` |
| [XRD、拉曼、FTIR](skills/research-visual-workflow/references/spectra.md) | `$research-visual-workflow 重绘附件里的 XRD 图谱，保留原始数据和缺测断线，只标我给出的峰位。` |
| [Origin 原生图](skills/research-visual-workflow/references/origin-native.md)与[复杂多面板](skills/research-visual-workflow/references/origin-complex.md) | `$research-visual-workflow 把分组柱图和矩阵热图排成双面板。误差棒用 SD，热图区分零值与缺测。交付含数据的 OPJ、OGG 和 PNG。` |
| [新建或修改可编辑 PPT](skills/research-visual-workflow/references/create-and-check.md#powerpoint) | `$research-visual-workflow 按参考图的配色和版式修改附件 PPT，保留可编辑文字和原生图表，另存 PPTX。` |

## 安装和使用

1. 在 GitHub 选择 **Code → Download ZIP** 并解压。将 `skills/research-visual-workflow` 整个文件夹复制到 `~/.agents/skills/`。Windows 的目标目录为 `%USERPROFILE%\.agents\skills\research-visual-workflow`。[Codex Skill 安装说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)
2. 在解压后的仓库根目录运行 `python -m pip install -r skills/research-visual-workflow/requirements.txt`。下文的 `python` 指 Python 3.10 或更新版本。若 `python --version` 显示旧版，可把解压目录交给 Codex，并发送「请用本机已有的 Python 3.12 安装这个 Skill 的依赖」。生成原生 Origin 工程还需要 Windows 和本机安装的 Origin。
3. 打开 Codex 对话，上传数据或可分享的参考图，再发送上表的对应指令。如果列表里还没有出现该 Skill，重启 Codex。

## 用合成数据试跑

在完整仓库根目录运行。第一条生成论文图预览，第二条检查混合多面板输入。若已安装可用的 Origin，去掉第二条的 `--dry-run` 即可导出原生工程。

```powershell
python skills/research-visual-workflow/scripts/plot_csv.py --csv examples/data.csv --x time --y control --y treatment --x-label "Time (min)" --y-label "Response (a.u.)" --width-mm 89 --height-mm 55 --font-size 7 --output outputs/paper.svg
python skills/research-visual-workflow/scripts/origin_complex.py --spec examples/origin-complex/06-mixed.json --output-dir outputs/demo-origin --dry-run
```

[`examples/`](examples/) 还包含三种合成图谱、六个复杂 Origin 输入，以及基础 PPT 的页面与风格配置。

## 本地增加参考图

可以在 Codex 用第一条指令逐张入库。仅在本机处理时，从已安装的 Skill 目录运行 `python scripts/private_refs.py inbox`，把图片放进返回的目录，再运行 `python scripts/private_refs.py add --inbox`。已有图库可直接绑定到仓库外的路径。[本地图库流程](skills/research-visual-workflow/references/private-library.md)

## 上传到 GitHub

1. 解压经过检查的发布 ZIP，打开其中包含 `README.md` 的 `research-visual-workflow` 文件夹。
2. 在 GitHub 新建公开仓库，选择 **Add file → Upload files**（新建的空仓库可用上传现有文件入口）。上传该文件夹**里面**的全部内容并保留目录结构，包括 `.gitignore`。[GitHub 上传指南](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)
3. 提交后，确认首页显示本说明，且能打开 `skills/research-visual-workflow/SKILL.md`。把仓库链接分享给同学即可。

公开包仅包含代码、文档和合成示例。修改后从仓库根目录运行 `python scripts/build_release.py --output ../research-visual-workflow-public.zip`，按发布清单重新打包并复核内容。
