# 检索金标、指标与对照

冻结文档 ID、语料/查询内容、相关集合、切块规则、模型 revision、向量归一化、相似度与平局处理。开发集用于模型、参数和阈值选择；测试查询的金标不参与这些选择。结果 ID 应唯一且存在于本次语料，金标也要核对语料归属。

## 多相关文档下的指标

令 R_q 为查询 q 的非空相关集合，L_q(k) 为前 k 个无重复结果：

- Recall_q@k = 命中的相关文档数 / |R_q|。
- Hit_q@k = 是否至少命中一个相关文档，取 0 或 1。
- RR_q@k = 首个相关结果的一基排名的倒数；前 k 无命中则为 0。MRR@k 对全部有效查询平均，不能只平均命中的查询。

例如 5 篇相关文档中，前 4 条结果命中 2 篇，首个命中在第 3 名，则 Recall@4=2/5、Hit@4=1、RR@4=1/3。每查询恰有一个相关文档时，Hit 与 Recall 必然相同；多相关场景不可互换，虽然某些查询仍可能数值相等。

宏 Recall 是逐查询 Recall 的均值；微 Recall 是总命中相关数除以总相关数。明确所用平均方法。空金标使 Recall 分母为 0：预先声明处理规则，报告数量，并另评无答案/拒答能力。相关性定义参考[信息检索教材](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html)；[Sentence Transformers v3.4.1 实现](https://raw.githubusercontent.com/UKPLab/sentence-transformers/v3.4.1/sentence_transformers/evaluation/InformationRetrievalEvaluator.py) 的 accuracy@k 对应这里的 Hit@k，使用工具时不要只凭名称映射指标。

## 分开回答三个问题

| 对照 | 固定什么 | 能回答什么 |
|---|---|---|
| BM25 与精确稠密检索 | 同一语料单位、查询、金标；记录分词及 BM25 参数、嵌入模型与编码方法 | 词法和语义表示在该相关性任务中的差异 |
| ANN 与精确稠密 top-k | 同一向量、ID、过滤、度量、k 与平局规则 | 近似索引保留精确邻居的程度 |
| 候选加重排的最终系统 | 候选深度、过滤与重排策略 | 端到端相关性、延迟、资源和错误来源 |

可把近似邻居对齐定义为 `|ANN_topk ∩ exact_topk| / k`，其中 k 不大于候选数，称为 ANN agreement@k 以区别业务金标 Recall。精确近邻保留率高，不保证文档语义相关。[Faiss 索引选择](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index#then-flat)。BM25 的参数与分词约定影响结果，依据[原作者综述](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)。

余弦相似度越大越近，L2 距离越小越近；单位向量点积才等于余弦。相似度 0.8 不表示 80% 正确率，线性缩放或 softmax 也不自动校准概率。需要拒答阈值或概率时，用独立标注开发数据选择或拟合，再用隔离测试验证。[Faiss 度量说明](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances#how-can-i-index-vectors-for-cosine-similarity)。

恢复检索工件时，在新进程对相同查询比较向量、分数与排序，记录容差和平局规则；仅文件能加载不足以证明检索行为相同。
