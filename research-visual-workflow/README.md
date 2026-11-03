# Research Visual Workflow｜科研图与 PPT

一个适用于本地 Codex 的 Skill：分析参考图、管理私有风格库、制作或修改科研图、Origin 图和可编辑 PPT。Skill 入口是 [SKILL.md](skills/research-visual-workflow/SKILL.md)。

## 安装与调用

1. 下载仓库 ZIP 并解压，保留 skills/research-visual-workflow 整个目录。把它复制到本机 Codex 用户级 Skill 目录（Windows 文档示例：%USERPROFILE%\.agents\skills\research-visual-workflow），或把解压目录交给 Codex，请它代为安装。见 [Codex Skill 说明](https://learn.chatgpt.com/docs/build-skills)。
2. 用 Python 3.10+；需要执行脚本时，在 Skill 目录运行 python -m pip install -r requirements.txt。Origin 自动导出另需兼容 Origin 和 originpro。
3. 新建本地对话，上传材料，点名 Skill：

~~~text
$research-visual-workflow 把附件逐张加入我的私有参考库；记录配色、用途和检索标签。
~~~

~~~text
$research-visual-workflow 用附件数据画科研图，参考我本地库的风格，输出 SVG 和 PNG。
~~~

~~~text
$research-visual-workflow 根据附件修改现有 PPT，另存为可编辑 PPTX。
~~~

## 如何增加参考材料

- **适合会话分析的图片：** 拖进 Codex，发送上面的入库指令。首次如要复用旧库，提供旧库的本地路径。
- **只留在本机的图片：** 按 [本地图库流程](skills/research-visual-workflow/references/private-library.md) 建立投递文件夹。放入图片，运行 python scripts/private_refs.py add --inbox。本地脚本读图并写入 SQLite，无需给对话上传图片。

真实图库和公开仓库分开。图库路径和个人设置不要提交；这不是加密工具，也不会改变 Codex 对话的数据处理方式。需要仅本地处理时，直接在本机终端运行投递脚本。

## 上传到 GitHub

1. 从检查过的发布 ZIP 解压到新目录；只选该包里的内容，保持 skills/ 的层级。
2. 在 GitHub 选 **New repository**，建议命名 research-visual-workflow，并选择所需可见性。[创建仓库](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)
3. 在仓库选择 **Add file → Upload files**（空仓库可从上传现有文件入口进入），上传解压后的内容并提交。确认仓库中能看到 skills/research-visual-workflow/SKILL.md。[上传文件](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)

重新打包时，从仓库根目录运行 python scripts/build_release.py --output ../research-visual-workflow-public.zip。仅发布清单中的文本文件；发布前仍需检查修改过的内容。将参考材料、索引、缓存和生成成果留在本机私有位置。

## 公共示例

examples/ 中的表格、风格和演示稿说明均为合成示例。通用辅助脚本保留 Visual Figure Suite 的 MIT 许可。
