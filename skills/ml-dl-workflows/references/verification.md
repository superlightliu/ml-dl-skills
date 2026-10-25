# 评估、持久化与恢复层次

以下是原创操作约定。执行时按实际任务缩放，不把这份方法说明当作运行报告。

## 先固定比较条件

比较训练后和重载后的预测前，固定输入样本 ID、顺序、内容、特征名称/类型/顺序、缺失值规则、预处理工件、输出类别顺序及预测类型。记录代码和依赖版本、设备、模型文件哈希与数值容差。逐样本比较形状、输出和最大差异；只比较 accuracy 会漏掉不同预测相互抵消的情况。

Pipeline 应连同已拟合预处理保存。只保存模型参数而忘记词表、缩放量、类别映射或特征顺序，不足以重建同一个预测流程。哈希用于识别文件内容，不证明训练记录的语义真实。

## PyTorch 恢复分三层

| 范围 | 必要状态与条件 | 对照证据支持的结论 |
|---|---|---|
| 固定输入推理 | 模型结构、完整 state_dict（参数与持久 buffers）、预处理/类别映射；同一输入与组批；eval 加适合的梯度模式 | 新进程逐值比较 logits 或概率，仅支持该输入约定下的推理恢复 |
| 固定下一批训练一步 | 上述状态，加 optimizer、全局 step、Python/NumPy/Torch RNG；使用时加 CUDA RNG、scheduler、GradScaler 与梯度累积位置/梯度 | 连续分支和独立恢复分支在同一批上比较 loss、全部参数/buffers、优化器与调度器状态，仅支持该一步 |
| 后续数据流连续重放 | 上述状态，加 sampler 排列/游标、loader generator、数据版本/流偏移、随机变换、worker、分片及预取状态或等价重建机制 | 逐批比较样本 ID、顺序、增强后输入和训练状态，仅支持实测中断点及 loader 配置 |

下层通过不能推出上层通过。保存模型与优化器是继续训练的重要组成；内存中的 state_dict 可能引用当前对象，制作对照快照时应使用独立复制或已保存工件，避免两支共享状态。[PyTorch 保存与加载](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html#saving-loading-a-general-checkpoint-for-inference-and-or-resuming-training)。

优先选 optimizer step 完成且梯度清零后的明确保存边界。中途梯度累积恢复需要额外保存已累计梯度和微批位置。先重建对象并载入状态，再在下一次被测随机操作前恢复 RNG；模型构造和创建 loader iterator 都可能消耗随机数。

只重设 seed 或保存主进程 RNG 不足以证明多 worker 数据流恢复。预取使下一批可能已经生成；无法取得全部状态时，缩小到固定 batch 或受控 epoch 边界。可先用 num_workers=0、固定采样顺序和可控变换设计小验证，但仍需实际比较。[DataLoader 随机性与预取](https://docs.pytorch.org/docs/2.14/data.html#randomness-in-multi-process-data-loading)。

固定版本与随机状态也不保证跨设备、平台或版本逐位相同；预先声明数值容差，并记录确定性设置与不支持操作。[PyTorch 可复现性说明](https://docs.pytorch.org/docs/2.14/notes/randomness.html)。

## 实验记录

[空记录模板](../assets/run-record-template.json) 可以按项目需要删减和扩展。至少能回答：用了哪些数据、如何划分、哪里发生 fit、选择了什么、实际测了什么、保存了什么、恢复到哪一层、有哪些未验证范围。指标必须包含定义、样本范围和数值；未执行项保留空值或明确的未执行状态。

修改数据、预处理、模型、依赖或恢复方式后，针对变化重新检查。保留真实失败与后续修正，不把旧记录的通过状态复制到新运行。
