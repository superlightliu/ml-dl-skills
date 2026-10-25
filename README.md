# ML & DL Learning Skills

**用中文学机器学习，以可核对的推导、真实作答和可信实验建立理解。**

[English](README.en.md) · [安装](docs/INSTALLATION.md) · [提示词示例](docs/EXAMPLES.md) · [教材与来源](THIRD_PARTY_NOTICES.md) · [更新记录](CHANGELOG.md)

这是一个包含 **11 个 Agent Skills** 的可安装合集：学习教练、机器学习与深度学习基础、数学支撑、八本教材的阅读导航，以及机器学习项目实施与评估工作流。适用于支持 `SKILL.md` 的代理客户端，并提供 Codex 插件清单与仓库市场目录。

公开版包含原创指导、检索导航和空白模板；不附教材 PDF、原书摘录、长篇翻译、模型权重、个人学习记录或预装训练环境。教材相关技能帮助定位来源、比较前提与组织推导，不能替代获得原著。英文材料可以按问题用中文讲解，保留关键术语。

## 能做什么

- 从真实回答判断起点，安排可调整的学习路线，逐步给提示。
- 区分数据泄漏、泛化误差、概率建模、优化与数值实现问题。
- 按主题选择 ISLP、MML、UDL、D2L、PML I/II、ESL 或 Deep Learning，再核对实际来源。
- 为分类、回归、图像、检索、不平衡学习和时间序列项目确定划分、基线、指标及恢复证据。
- 将学习表现与工具运行结果分开：没有真实作答就保持 `not_assessed`，没有实跑就不声称实验成功。

## 快速安装

需要 Git 和 Python 3.10+。安装与校验脚本仅使用 Python 标准库，不安装 ML 依赖。

```sh
git clone https://github.com/superlightliu/ml-dl-skills.git
cd ml-dl-skills
python -B scripts/validate.py
python -B scripts/install.py --dest ../my-project/.agents/skills
python -B scripts/install.py --dest ../my-project/.agents/skills --apply
```

把 `../my-project` 改成自己的项目位置。第一条安装命令只预览；加 `--apply` 才复制。应安装完整合集，保证技能间的相对链接可用。已有相同内容可以跳过；遇到不同内容会停止，不覆盖自己的修改。支持手动复制及插件方式，见[安装说明](docs/INSTALLATION.md)。

打开目标项目后，在支持的客户端选择技能或输入：

```text
请使用 $ml-dl-study-coach。先了解我的目标和基础，再用一道问题判断从哪里开始。
```

## 技能目录

| 技能 | 用途 |
| --- | --- |
| [ml-dl-study-coach](skills/ml-dl-study-coach/SKILL.md) | 诊断、学习路线、提示与真实作答进度 |
| [ml-foundations](skills/ml-foundations/SKILL.md) | 机器学习基础与 ISLP 阅读导航 |
| [dl-foundations](skills/dl-foundations/SKILL.md) | 张量、反向传播、训练与推理的概念带练 |
| [ml-math-foundations](skills/ml-math-foundations/SKILL.md) | 线性代数、概率、微积分和优化；MML 导航 |
| [ml-dl-workflows](skills/ml-dl-workflows/SKILL.md) | 数据划分、评估、模型范围与恢复证据 |
| [understanding-deep-learning](skills/understanding-deep-learning/SKILL.md) | UDL 的模型、训练、生成建模阅读导航 |
| [d2l-english-reference](skills/d2l-english-reference/SKILL.md) | D2L 英文教材的概念与实现定位 |
| [probabilistic-ml-intro](skills/probabilistic-ml-intro/SKILL.md) | PML Introduction 的概率建模路线 |
| [probabilistic-ml-advanced](skills/probabilistic-ml-advanced/SKILL.md) | PML Advanced 的推断与高级模型导航 |
| [statistical-learning-theory](skills/statistical-learning-theory/SKILL.md) | ESL 的方法比较、假设与统计学习阅读导航 |
| [deep-learning-theory](skills/deep-learning-theory/SKILL.md) | Goodfellow 等《Deep Learning》的理论导航 |

## 使用与边界

只解释概念时无需 GPU、API Key 或 ML 库。获取在线资料需要客户端具备浏览能力；也可以提供合法持有的资料片段。执行代码时，由使用者选择环境、数据和输出位置，并按项目需要另行安装依赖。工作流技能不附已经跑好的六类模型案例，也不承诺特定业务成绩。

默认使用中文；可以要求英文或双语。技能本身不提供遥测、账户系统或后台任务；所用代理服务、浏览器和模型仍遵循各自的数据政策。敏感项目数据不应提交到本仓库 Issue。

这是独立开源项目，发布到 GitHub 不代表已获任何平台官方目录收录或认证。

## 验证与贡献

```sh
python -B scripts/validate.py
```

运行安装器回归测试前，按[贡献指南](CONTRIBUTING.md#本地检查)设置专用测试目录。自动检查关注结构、引用、安装边界和可移植性；教学行为还需要真实请求验证。有关贡献、问题反馈和版本发布，见 [CONTRIBUTING.md](CONTRIBUTING.md)、[SECURITY.md](SECURITY.md) 和 [发布指南](docs/RELEASING.md)。

本仓库原创文件采用 [MIT](LICENSE) 许可。外部教材及其名称、页面、图片和代码属于各自权利人，不在本仓库 MIT 授权范围内；详见[第三方说明](THIRD_PARTY_NOTICES.md)。
