---
name: probabilistic-ml-advanced
description: "用中文辅助阅读 Kevin P. Murphy 的 Probabilistic Machine Learning: Advanced Topics，按问题定位图模型、近似推断、生成模型、隐结构、序贯决策和因果主题。用于区分模型、目标、算法及诊断条件；提供原创阅读导航，不附教材正文。"
---

# 概率机器学习高级阅读导航

把问题写成观测、潜变量、参数、目标量、计算预算与评价场景。不能因为数据或模型复杂，就跳过目标和假设。

查 [topic-route.md](references/topic-route.md) 选择问题入口和诊断动作；查 [source-guide.md](references/source-guide.md) 取得官方阅读入口。只读回答当前问题需要的材料。用户没有本地教材时使用官方资源；无法取得原文时明确说明未核对该书表述，不虚构页码、公式编号或已读记录。

## 推断与方法比较

1. 先写概率分解或目标函数，说明哪些量可精确计算、哪些需要近似。配分函数、边缘似然、后验与预测分布的计算困难分别定位。
2. 按目标选择阅读路线。需要期望、样本、概率密度、点估计或动作时，所需算法能力并不相同。
3. 对近似方法核对支持、独立性、可微性、可识别性和收敛相关条件。把模型误设、近似误差、优化误差与 Monte Carlo 误差分开。
4. 比较方法时固定目标量、数据和预算，再说明各自能给出的诊断。不同目标上的一个分数不能直接构成优劣结论。
5. 用可枚举的小模型或一维分布构造原创检查，尽可能提供精确参考值。数值对照用于暴露条件遗漏，不冒充一般收敛证明。
6. 涉及行动、强化学习或因果时，额外明确反馈机制、信息可见性、策略或干预含义；观察分布本身不能自动识别干预效果。

以中文解释并保留必要英文检索词。书中结论、额外假设、独立推导和实际运行结果分别表述。学习者要练习时先给问题和分级提示；明确要解法时直接提供，不把听过讲解记为独立掌握。只有实际执行后才报告计算或训练结果。

## 互补入口

- 概率对象与基本统计推断：[probabilistic-ml-intro](../probabilistic-ml-intro/SKILL.md)。
- 优化与线性代数前提：[ml-math-foundations](../ml-math-foundations/SKILL.md)。
- 深度生成的历史理论脉络：[deep-learning-theory](../deep-learning-theory/SKILL.md)。
- 现代网络直觉与理解检查：[understanding-deep-learning](../understanding-deep-learning/SKILL.md)。
- 实验、复现和资源约束：[ml-dl-workflows](../ml-dl-workflows/SKILL.md)。

互补技能按需使用。没有实际数据或执行结果时，只能给假设下的分析和验证方案，不补写校准、收敛或性能结论。
