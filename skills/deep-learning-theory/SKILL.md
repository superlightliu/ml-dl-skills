---
name: deep-learning-theory
description: 用中文辅助阅读 Goodfellow、Bengio、Courville 的 Deep Learning（2016），按问题定位数值计算、网络训练、表征和概率生成主题，核对公式、假设与历史语境。用于理论答疑和原创反例；不附教材正文，也不将历史方法评价视为当前排名。
---

# Deep Learning 理论阅读导航

按当前疑问选择一个主要理论入口，再补必要前提。先判断问题属于数值计算、网络优化、泛化、表征还是概率推断。

查 [topic-route.md](references/topic-route.md) 选择问题入口和诊断动作；查 [source-guide.md](references/source-guide.md) 取得官方阅读入口。只读回答当前问题需要的材料。用户没有本地教材时使用官方资源；无法取得原文时明确说明未核对该书表述，不虚构页码、公式编号或已读记录。

## 理论阅读工作流

1. 将问题写成数据、模型族、目标、算法和评价协议；避免把容量、优化成功与泛化混作一个结论。
2. 对数学式先检查轴、形状、支持集及可微性。对官方 HTML 中的复杂公式，按可用工具核对原始显示，不能把抽取乱码当作确定公式。
3. 逐步连接定义、假设和结论。数值稳定性的变形、统计目标的等价与算法近似需分别解释。
4. 设计独立微型计算图、离散分布或低维矩阵，检查边界情况；只在有实际执行时称为数值验证。
5. 对概率生成问题分清归一化、后验推断、采样与评价。能采样、能算密度和能算后验是不同能力。
6. 将 2016 年语境中的经验判断与当前问题分开。需要当前模型、框架 API 或硬件结论时另查相应官方或原始来源。

以中文解释并保留必要英文检索词。书中结论、额外假设、独立推导和实际运行结果分别表述。学习者要练习时先给问题和分级提示；明确要解法时直接提供，不把听过讲解记为独立掌握。只有实际执行后才报告计算或训练结果。

## 互补入口

- 数学先修：[ml-math-foundations](../ml-math-foundations/SKILL.md)。
- 初学训练实践：[dl-foundations](../dl-foundations/SKILL.md)。
- 网络结构的理解检查：[understanding-deep-learning](../understanding-deep-learning/SKILL.md)。
- 更多现代概率推断与生成主题：[probabilistic-ml-advanced](../probabilistic-ml-advanced/SKILL.md)。
- 以代码为中心的阅读：[d2l-english-reference](../d2l-english-reference/SKILL.md)。

这些互补入口是可选的。未读取的原图、证明和参考文献保持未核对，不依据本导航推断全书已读或个人已掌握。
