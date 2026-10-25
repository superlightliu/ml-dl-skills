# XGBoost 轮次与预测范围

本节具体 API 语义以 XGBoost 2.1.4 Python 的树 booster 为参照；其他版本、gblinear、切片模型或自定义训练策略先核对实际行为。它是对齐流程，不是现成模型或运行证明。

## 明确要比较哪个模型

在该版本中，sklearn wrapper 有 best_iteration 时会据此确定默认预测范围；原生 Booster.predict / inplace_predict 的默认范围使用完整模型。best_iteration 是从 0 开始的轮索引，iteration_range 的结束端不包含在内，因此选定 b 后使用 `(0, b + 1)`。轮数与树数不同，多分类或 num_parallel_tree 可每轮产生多棵树。依据：[wrapper 源码](https://raw.githubusercontent.com/dmlc/xgboost/v2.1.4/python-package/xgboost/sklearn.py)、[原生源码](https://raw.githubusercontent.com/dmlc/xgboost/v2.1.4/python-package/xgboost/core.py)。

## 保存与核对

同次训练保留：模型文件及 SHA-256、版本、run_id、实际 boosted rounds、用于此工件的最佳轮、输入/类别约定、预处理工件及原训练记录。训练记录应说明监控集、指标、最大化或最小化、patience、min_delta、callback、每轮结果与停止原因；发生切片或 save_best 时记录工件轮次映射。

重载时先验证文件与记录属于同次训练，再核对实际轮数。若模型含 best_iteration，要求它是有效整数且满足 `0 <= b < num_boosted_rounds()`，并与可信记录一致。缺失属性不等于最佳轮为 0。

属性缺失时，只从已核实、与该模型绑定的原训练记录恢复明确保存的索引。只有曲线时，还需要完整选择规则与切片映射才能审计；不能把事后 argmin 自动当作训练时最佳轮。缺记录、哈希冲突或范围越界时，报告无法可靠恢复最佳轮，停止该目标的等价比较。不能用最后一轮、n_estimators - 1、树总数或另一运行的最佳轮补值。

完整模型也可以是合法预测目标，但要由原训练目标或明确的新选择支持，并单独评价；它不等于恢复了缺失的最佳轮。

## 新进程逐值比较

训练端与重载端都显式使用相同 iteration_range，同时对齐特征顺序/类型、missing、base_margin、预处理、objective、类别顺序与输出类型。二分类 wrapper 的正类概率要与对应原生概率比较，不能拿类别标签去比概率。使用切片工件时，以该工件的轮次映射为准，模型改变后更新哈希。

`b + 1 == num_boosted_rounds()` 只表示范围覆盖现有轮次，不能证明提前终止。是否实际早停要看配置上限与训练日志；标准训练和自定义 callback 的选择规则也可能不同。[XGBoost train 源码](https://raw.githubusercontent.com/dmlc/xgboost/v2.1.4/python-package/xgboost/training.py)。
