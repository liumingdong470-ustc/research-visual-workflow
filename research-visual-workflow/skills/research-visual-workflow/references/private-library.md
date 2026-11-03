# 私有参考库

以本 Skill 目录为工作目录。使用本机 Python 3.10+；安装 requirements.txt 中该任务所需依赖。Pillow 用于测色和入库。

## 一次绑定

对已有兼容库（含 styles.sqlite、catalog.json、assets/、profiles/），直接配置外部目录：

~~~powershell
python scripts/private_refs.py configure --library "D:\PrivateReferences"
python scripts/private_refs.py status
~~~

配置保存在用户目录的 .research-visual-workflow/settings.json。未配置时默认使用其 library 子目录。单次调用也可在子命令后指定 --library，不改变配置。

## 方式 A：对话上传后追加

确认用户允许在会话中分析附件。先打开图，提炼配色、构图、标注和用途。用 visual_suite.py style 生成配色草稿，在私有目录保存经复核的配置，区分实测与观察推断。透明背景要人工复核；不要从像素图断言字体名。然后执行：

~~~powershell
python scripts/private_refs.py add --image "D:\Incoming\reference.png" --profile "D:\PrivateReferences\reviewed.json" --title "多组时间曲线" --tag "动力学"
~~~

一份审核配置只对应一张图。返回名称和记录 ID；同一文件内容不会重复新增。

## 方式 B：本机投递

~~~powershell
python scripts/private_refs.py inbox
python scripts/private_refs.py add --inbox
~~~

第一条返回投递目录。把图片复制进去，再在本机终端运行第二条。过程只调用本机 Pillow 和 SQLite，不访问网络；按内容去重，原投递图保留。自动标题取文件名，自动配色是草稿，不分析科学含义。只处理该目录的直接子文件。

## 搜索与取用

~~~powershell
python scripts/private_refs.py search --query "动力学"
python scripts/private_refs.py show --id "替换为记录ID"
~~~

检索是关键词匹配。选中后按用户允许的范围打开记录和图片，用其 profile 作为风格输入。真实实验数据与参考图的颜色分开管理。
