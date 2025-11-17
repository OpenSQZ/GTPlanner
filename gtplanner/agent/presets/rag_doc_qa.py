"""
RAG document QA preset prompt.

Designed to steer GTPlanner toward a retrieval-oriented Agent PRD with
clear data, indexing, retrieval, generation, and evaluation expectations.
"""

RAG_DOC_QA_PROMPT = """
[预设] RAG 文档问答 / 标准研判助手

你要规划的 Agent 面向法规、标准、长文档问答。请用简洁 Markdown 输出，务必覆盖以下视角：

1) 背景与目标
   - 目标用户、决策场景（合规审核、条款检索、变更影响）
   - 明确 in-scope / out-of-scope

2) 数据源与入库
   - 支持格式：PDF、Word、扫描件/OCR、表格、附录
   - 必要元数据：标准/条例编号、章节/条款号、版本/发布日期、适用地区/行业标签
   - 切分策略：章节/标题切分 + 滑窗，单块长度上限与重叠
   - 结构化字段抽取：条款编号、标题、要求内容、处罚/合规级别

3) 向量化与存储
   - Embedding 模型选择、维度、多语支持、延迟取舍
   - 索引设计：HNSW/IVF/Flat，更新/重建策略
   - 哪些字段入索引，哪些留作查询过滤

4) 检索与重排
   - 主检索：向量/关键词混合；top_k 默认与上限
   - 过滤条件：standard_id、行业、年份/版本、语言
   - Rerank 方案：使用时机、模型/服务

5) 生成与安全
   - LLM 选择与提示模板；引用格式（条款号 + 片段）
   - 歧义/低置信/无法回答的处理策略
   - 输出格式：面向下游的结构化 JSON / Markdown

6) 评估与监控
   - 数据集构建：金标问答、条款级标签、对照负样本
   - 指标：准确率、召回/覆盖率、可溯源性、延迟、幻觉率
   - 线上信号：用户反馈闭环、日志、告警阈值

语气保持务实、可落地，方便直接交付给开发/运维团队。
"""
