# PyTorch 检查点

先记录实际 PyTorch 版本。下列模式说明引用 2.14 文档；其他版本以对应官方文档与最小验证为准。文档行为不表示当前环境已安装或执行过这些 API。

## 从输入到参数更新

| 检查位置 | 对初学代码最有用的检查 |
|---|---|
| 输入 | 写出每个轴、dtype 和 device；特征与标签来自同一批样本；预处理不能使用测试统计量 |
| 输出与损失 | 普通批量 C 类分类常用 logits [B, C]；CrossEntropyLoss 的类别索引目标通常为 long 型 [B]，有效索引在 0 到 C-1（另有 ignore_index）；不要先 softmax 再作为 logits 输入 |
| 梯度 | 目标参数是否 requires_grad，损失是否连接到它；意外 detach、转 NumPy、重新构造张量可能切断图；backward 默认累加梯度 |
| 更新 | optimizer 是否包含正确参数，清零与 step 顺序是否符合设计；需要梯度累积时明确微批与归一化规则 |
| 评价 | 先切 eval，再按是否需要梯度选择上下文；评价后继续训练要恢复 train |
| 指标 | 按指标实际分母聚合，例如有效样本/token 数或有效权重之和；不能对大小不同或权重不同的 batch 均值简单等权平均 |

CrossEntropyLoss 也支持与输入同形的浮点概率目标；不能把该接口的 dtype/shape 规则与类别索引接口混用。具体维度、高维分类、权重和归约规则见[官方 CrossEntropyLoss](https://docs.pytorch.org/docs/2.14/generated/torch.nn.CrossEntropyLoss.html)。

## 模型模式与梯度模式分别控制

| 操作 | 控制内容 | 不能推断的事情 |
|---|---|---|
| model.eval() | 等价于 train(False)，切换模块的 training 状态；Dropout、BatchNorm 等按自身定义改变行为 | 不关闭 autograd，不修改参数 requires_grad |
| torch.no_grad() | 上下文内不记录普通反向计算图；通常用于不需要反传的计算 | 不切换 eval；接受 requires_grad 的张量工厂函数有例外；不关闭前向 AD |
| torch.inference_mode() | 除停止反向图记录，还省去 view tracking/version counter，并关闭前向 AD | 不切换 eval；新建 inference tensor 不应直接用于之后需要 autograd 记录的运算 |

依据：[eval 与 autograd](https://docs.pytorch.org/docs/2.14/notes/autograd.html#evaluation-mode-nn-module-eval)、[no_grad](https://docs.pytorch.org/docs/2.14/generated/torch.no_grad.html)、[inference_mode](https://docs.pytorch.org/docs/2.14/generated/torch.autograd.grad_mode.inference_mode.html)。

常规纯预测可组合 eval 和 inference_mode；若产物之后还要参与训练图，考虑 no_grad 并明确图的截断位置。需要输入梯度的评价任务可以在 eval 下保留梯度。选择上下文依据用途，不承诺某一种总是更快。

BatchNorm 默认 track_running_stats=True：train 使用当前批统计并更新运行统计，eval 使用已保存统计。train 配合 no_grad 或 inference_mode 仍可能更新 buffers。track_running_stats=False 时，train 和 eval 都依赖当前批统计，同一样本换组批可能改变输出；它也不等于冻结 affine 参数。依据：[BatchNorm2d](https://docs.pytorch.org/docs/2.14/generated/torch.nn.BatchNorm2d.html)。

## 保存检查点前先定义用途

纯推理需保留模型结构、完整 state_dict、预处理与类别约定。继续训练还要考虑 optimizer、step、随机数、scheduler、GradScaler 和梯度累积状态；需要连续重放数据则增加 loader 与采样状态。仅模型加载成功不能证明训练恢复。

验证按[工程恢复层次](../../ml-dl-workflows/references/verification.md)比较真实输出或更新，而不是只检查文件存在。保存最佳状态时不要误以为 `best_state = model.state_dict()` 自动产生独立快照；使用即时保存或独立深复制，并按正确设备与对象重建。[PyTorch 保存与加载](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)。
