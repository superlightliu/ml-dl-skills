# 安装与卸载

## 方式一：标准库安装器

在本仓库根运行 `python -B scripts/validate.py`，再选择目标项目下的 `.agents/skills` 目录：

```sh
python -B scripts/install.py --dest ../my-project/.agents/skills
python -B scripts/install.py --dest ../my-project/.agents/skills --apply
```

支持 Python 3.10+。默认只预览，`--apply` 才复制完整合集；不自动下载资料、安装 ML 软件、修改客户端设置或调用模型。路径可以绝对或相对，但必须由使用者指定。Windows 可用自己的 Python 可执行文件替代 `python`。

安装前会检查全部目标；内容相同的技能跳过，内容不同则停止，不覆盖。源/目标中的链接或路径重定向会被拒绝。若安装中途失败，请先查看输出的已完成及未完成项，不要假定整个合集已装好。

## 方式二：手动复制

将本仓库 `skills/` 下的 11 个技能目录一同复制到目标项目 `.agents/skills/`。层级应为 `.agents/skills/ml-dl-study-coach/SKILL.md`，而不是再嵌套一个 `skills/`。目录应保持同级，便于跨技能引用。不要把 `progress/` 或自己的资料混入发布源目录。

Codex 当前文档列出项目 `.agents/skills` 与用户 `~/.agents/skills` 等发现位置；选择项目范围可以避免影响其他项目。详见 [OpenAI 技能文档](https://learn.chatgpt.com/docs/build-skills)。其他客户端按其技能安装说明使用同一 `SKILL.md` 结构。

## 方式三：仓库插件市场

本仓库包含 `plugin.json`、兼容清单 `.codex-plugin/plugin.json` 与 `.agents/plugins/marketplace.json`。支持该功能的 Codex 客户端可添加仓库来源：

```sh
codex plugin marketplace add superlightliu/ml-dl-skills
```

添加后，在桌面客户端刷新或重启，打开插件目录，选择 ML & DL Learning Skills 来源中的 ml-dl-skills 并安装。CLI 中可输入 `/plugins` 选择并安装；安装后开启新会话加载技能。不同客户端的插件界面和可用功能可能不同；此方式的格式与命令依据 [OpenAI 插件分发文档](https://developers.openai.com/plugins/build/plugins)。如果客户端不支持仓库市场，使用前两种方式。仓库市场分发不等于公开官方目录上架。

## 第一次使用

打开安装目标项目，按客户端需要刷新技能或开启新会话，选择 `ml-dl-study-coach` 或显式输入 `$ml-dl-study-coach`。只应加载问题相关资料。学习进度默认未知，技能不会把示例输出当成用户成绩。需要保存学习记录时，明确指定自己的工作目录。

## 更新与卸载

更新前保存自己修改过的技能。安装器遇到差异会停止；先对比新旧版本，再自行决定替换。不要用脚本强制覆盖本地改动。

卸载时只移除当初安装的 11 个同名目录，或通过插件界面卸载。个人学习记录和教材应放在技能目录以外，卸载技能不应删除它们。不要删除整个 `.agents` 或其他项目技能。
