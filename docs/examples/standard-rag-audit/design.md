# Design Doc: 地方标准研判 RAG 助手（标准研判RAG助手）

## 1. 背景与目标

针对地方标准、行业标准、团体标准等技术性文件，人工逐条核对企业方案/制度是否符合要求效率极低，且难以保证口径一致与引用准确。

本设计目标是构建一个**标准研判 RAG 助手**，在内网环境中完成以下能力：

- 支持 PDF / Word 多格式标准文档导入与条款级解析；
- 支持基于语义 + 条款号/标题的混合检索；
- 支持对企业方案/制度文本进行**合规性分析**与**指标合理性校验**；
- 输出“结论–依据–可引用段落”的结构化报告，带标准号/条款号；
- 当召回不足或证据不充分时，返回 `unknown`，避免胡编。

---

## 2. Standard Operating Procedure（SOP）

- **[步骤1: 标准文档导入]**  
  接收用户上传或指定的标准 PDF / Word 文件（对象存储 URL 或 file_id），完成版面清洗、OCR、条款级结构化解析，并写入标准索引库。

- **[步骤2: 企业材料接收]**  
  接收企业提交的方案/制度/记录文本（支持粘贴文本、文件上传等），归一化成待研判文本。

- **[步骤3: 研判任务定义]**  
  用户选择或输入需研判的标准范围、条款范围（可选）以及研判任务描述（例如“检查排放限值是否达标”）。

- **[步骤4: 相关条款检索（RAG 检索）]**  
  基于标准索引，对研判任务和企业材料构建查询，使用**语义向量检索 + 条款号/标题过滤**进行 Top-k 条款召回。

- **[步骤5: 指标抽取与合理性校验]**  
  从企业材料和召回条款中抽取结构化指标（名称-数值-单位-条件），并与标准要求区间/逻辑进行对比，给出“满足/不满足/不确定”。

- **[步骤6: 合规分析与结论生成]**  
  基于召回条款、指标对比结果与企业文本，由微调后的 LLM 生成合规性结论（status/score），并给出关键理由。

- **[步骤7: 引用报告与可追溯性输出]**  
  整理形成“结论–依据–可引用条款列表”的报告：包含标准号、条款号、条款标题、证据片段。当证据不足时返回 `status=unknown` 并说明原因。

---

## 3. Flow Design

### 3.1 Applicable Design Pattern

- **RAG（Retrieval-Augmented Generation）**
- **Hybrid Retrieval（向量检索 + 结构化过滤）**
- **Tool-augmented Reasoning（通过 Prefab 工具实现指标抽取、区间判断）**

### 3.2 Flow High-level Design

1. **标准文档解析与索引构建**  
   - 将标准 PDF/Word 进行 OCR + 版面分析（Layout/表格/段落），切分为条款级 chunk（256–512 tokens）。  
   - 使用预设 embedding 模型（如 `qwen-embedding`，维度 1024）生成向量，并写入标准向量索引库。  
   - 记录 `standard_index_id`，供后续检索使用。

2. **企业材料归一化**  
   - 将企业方案/制度文件统一转换为纯文本，清理页眉页脚、无关噪声。  
   - 可选：切分为段落级片段，用于构造更精确的检索 query。

3. **研判任务构造**  
   - 根据用户输入的任务描述 + 标准范围，构造检索 query：  
     `query = f"{task_desc} + 企业材料关键句 + 标准关键术语"`。

4. **混合检索（RAG 检索）**  
   - 向量检索：在 `standard_index_id` 对应索引中，基于 embedding 进行 Top-50 召回；  
   - 结构过滤：按标准号、条款号范围、条款标题关键词进行过滤/加权；  
   - 生成最终 Top-k（如 k=10）条款列表 `retrieved_clauses`。

5. **指标抽取与合理性校验**  
   - 从企业材料中抽取涉及的数值/质量指标（名称-数值-单位-场景）；  
   - 从 `retrieved_clauses` 中抽取标准限值/要求（区间、比较符号、单位、条件）；  
   - 对齐单位并进行区间判断，输出每个指标的 `满足/不满足/不确定` 标记。

6. **合规分析与结论生成**  
   - 调用微调后的中文基座模型（如 LoRA-tuned Qwen3），对“企业材料 + 标准条款 + 校验结果”进行综合分析；  
   - 输出整体 `status`（`compliant/partial/non_compliant/unknown`）、`score`（0–100）及主要理由。

7. **报告编排与输出**  
   - 生成结构化响应：  
     - `status`, `score`  
     - `violated_clauses`（带标准号/条款号/标题）  
     - `analysis`（自然语言解释）  
     - `suggestions`（整改建议）  
     - `citations`（可引用的条款原文或片段）  
   - 当 `retrieved_clauses` 为空或置信度低于阈值时，输出 `status=unknown` 并明确说明“未检索到足够证据”。

### 3.3 Flow Diagram

```mermaid
flowchart TD
    A[步骤1: 标准文档导入与解析] --> B[步骤2: 标准向量索引构建]
    B --> C[步骤3: 企业材料归一化]
    C --> D[步骤4: 研判任务构造]
    D --> E[步骤5: 混合检索(语义+条款号/标题)]
    E --> F[步骤6: 指标抽取与合理性校验]
    F --> G[步骤7: 合规分析(LLM推理)]
    G --> H[步骤8: 报告编排与结果输出]
```

---

## 4. Prefabs

### 4.1 标准文档解析与索引预制件

* **ID**: `standard_doc_indexer`  
* **描述**:  
  接收标准 PDF/Word 文件，完成 OCR、版式解析、条款级切分与向量化，将结果写入标准索引库并返回 `standard_index_id`。  
* **输入**:  
  * `file_url` / `file_id`  
  * `standard_meta`（标准号、名称、版本等，可选）  
* **输出**:  
  * `standard_index_id`  
  * `clause_list`（可选，用于调试：条款号 + 标题 + 正文）

### 4.2 标准条款混合检索预制件

* **ID**: `standard_clause_hybrid_retriever`  
* **描述**:  
  在指定标准索引中，基于语义向量检索 + 条款号/标题过滤，召回与研判任务相关的标准条款。  
* **输入**:  
  * `standard_index_id`  
  * `query`  
  * `top_k`（默认 10）  
  * `clause_filters`（标准号/条款号范围、标题关键词，可选）  
* **输出**:  
  * `retrieved_clauses`: 列表，每项包含：`standard_no, clause_no, clause_title, clause_text, score`

### 4.3 指标抽取与合理性校验预制件

* **ID**: `indicator_extractor_and_validator`  
* **描述**:  
  双通道抽取“企业指标”和“标准指标”，并进行区间/逻辑校验。  
* **输入**:  
  * `enterprise_text`  
  * `retrieved_clauses`  
* **输出**:  
  * `indicator_table`: 列表，每项包含  
    * `name, enterprise_value, enterprise_unit`  
    * `standard_range, standard_unit`  
    * `status`（`pass/fail/unknown`）  
  * `indicators_summary`（自然语言概括，可选）

### 4.4 合规分析预制件

* **ID**: `compliance_analysis_engine`  
* **描述**:  
  基于指标校验结果和相关条款，由微调后的 LLM 输出整体合规结论。  
* **输入**:  
  * `enterprise_text`  
  * `retrieved_clauses`  
  * `indicator_table`  
  * `task_desc`  
* **输出**:  
  * `compliance_result`（结构见下文）

### 4.5 引用报告生成预制件

* **ID**: `compliance_report_generator`  
* **描述**:  
  生成可对外展示的研判报告，明确列出结论、主要依据、引用条款列表，并在证据不足时返回 `unknown`。  
* **输入**:  
  * `compliance_result`  
  * `retrieved_clauses`  
* **输出**:  
  * `reference_report`（Markdown/HTML 风格文本）  
  * `citations`（结构化引用信息）

---

## 5. Utility Functions / Modules

1. **文件内容提取工具** (`utils/file_content_extractor.py`)  
   * *Input*: `file_url` / `file_id`  
   * *Output*: `file_text`  
   * *NOTE*: 支持扫描件 PDF 的 OCR，以及 Word/可复制 PDF 的直接提取。

2. **文本分段与清洗工具** (`utils/text_chunker.py`)  
   * *Input*: `file_text`  
   * *Output*: 条款/段落级 chunk 列表（携带标准号/条款号/标题等元信息）。

3. **指标正则模板库** (`utils/indicator_patterns.py`)  
   * 封装常见“数值/质量/浓度”等指标抽取的正则与解析逻辑，用于辅助 LLM 提高稳定性。

---

## 6. Node Design

### 6.1 Shared Store

```python
shared = {
    "file_url": "...",              # Input: 标准 PDF/Word 文件 URL 或 file_id
    "standard_meta": {},            # 标准号、名称、版本等
    "standard_index_id": None,      # 标准向量索引ID
    "file_text": None,              # 解析后的标准全文文本
    "enterprise_text": "...",       # 企业材料文本
    "task_desc": "...",             # 研判任务描述
    "retrieved_clauses": None,      # 混合检索得到的条款列表
    "indicator_table": None,        # 指标抽取与校验结果
    "compliance_result": None,      # 合规分析结果（见下）
    "reference_report": None,       # 可对外展示的研判报告
    "citations": None,              # 结构化引用列表
}
```

`compliance_result` 建议结构：

```python
compliance_result = {
    "status": "compliant | partial | non_compliant | unknown",
    "score": 0-100,
    "key_findings": [
        # 关键结论摘要
    ],
    "violated_clauses": [
        {
            "standard_no": "...",
            "clause_no": "...",
            "title": "...",
            "reason": "不符合原因说明",
        }
    ],
    "indicator_summary": "指标达标/不达标概述",
    "analysis": "综合分析说明",
    "suggestions": "整改/优化建议",
}
```

### 6.2 Node Steps

1. **[标准文档导入与解析节点]**  
   * *Purpose*: 接收标准文件，完成文本提取与基础清洗。  
   * *Type*: Regular  
   * *prep*: 从 shared 中读取 `file_url`, `standard_meta`。  
   * *exec*: 调用 `file_content_extractor` 提取 `file_text`；进行基础清洗。  
   * *post*: 写入 `file_text` 至 shared。

2. **[标准索引构建节点]**  
   * *Purpose*: 对标准条款进行切分与向量索引构建。  
   * *Type*: Regular  
   * *prep*: 读取 `file_text`, `standard_meta`。  
   * *exec*: 调用 `standard_doc_indexer`，得到 `standard_index_id` 和（可选）条款列表。  
   * *post*: 写入 `standard_index_id` 至 shared。

3. **[企业材料归一化节点]**  
   * *Purpose*: 将企业材料统一为可分析的文本形式。  
   * *Type*: Regular  
   * *prep*: 读取输入的企业文件 / 文本。  
   * *exec*: 清洗噪声、合并成 `enterprise_text`。  
   * *post*: 写入 `enterprise_text` 至 shared。

4. **[研判任务构造节点]**  
   * *Purpose*: 根据用户意图构造检索 query。  
   * *Type*: Regular  
   * *prep*: 读取 `task_desc`, `enterprise_text`。  
   * *exec*: 由 LLM/规则生成适合检索的 `query` 文本。  
   * *post*: 将 `query` 写入 shared。

5. **[混合检索节点]**  
   * *Purpose*: 在标准索引中检索相关条款。  
   * *Type*: Regular  
   * *prep*: 读取 `standard_index_id`, `query`。  
   * *exec*: 调用 `standard_clause_hybrid_retriever`，得到 `retrieved_clauses`。  
   * *post*: 写入 `retrieved_clauses`，若列表为空则标记可能 `status=unknown`。

6. **[指标抽取与合理性校验节点]**  
   * *Purpose*: 结构化对比企业指标与标准要求。  
   * *Type*: Regular  
   * *prep*: 读取 `enterprise_text`, `retrieved_clauses`。  
   * *exec*: 调用 `indicator_extractor_and_validator`，生成 `indicator_table`。  
   * *post*: 写入 `indicator_table` 至 shared。

7. **[合规分析节点]**  
   * *Purpose*: 基于条款与指标给出整体研判结论。  
   * *Type*: Regular  
   * *prep*: 读取 `enterprise_text`, `retrieved_clauses`, `indicator_table`, `task_desc`。  
   * *exec*: 调用 `compliance_analysis_engine`（LLM），生成 `compliance_result`。  
   * *post*: 写入 `compliance_result` 至 shared。

8. **[引用报告生成节点]**  
   * *Purpose*: 生成最终研判报告，支持对外引用。  
   * *Type*: Regular  
   * *prep*: 读取 `compliance_result`, `retrieved_clauses`。  
   * *exec*: 调用 `compliance_report_generator`，生成 `reference_report` 与 `citations`。  
   * *post*: 将 `reference_report`, `citations` 写入 shared，作为对外输出。

---

## 7. 非功能需求与评估指标

* **部署环境**：  
  * 依赖的向量库、LLM 服务通过 URL 调用；  
  * 所有标准文档与企业材料仅存储于本地安全存储。

* **性能目标**：  
  * 单次研判（标准长度 ≤ 200 页，企业材料 ≤ 20 页）端到端延迟 ≤ 5s（不含首次建索引）。  
  * 标准索引构建可异步批处理。

* **效果指标（示例）**：  
  * Top-3 条款召回率 ≥ 0.9（在标注数据集上）；  
  * 研判结论与专家标注一致率 ≥ 0.8；  
  * 指标抽取数值/单位匹配准确率 ≥ 0.9。

* **可追溯性**：  
  * 每次研判保留 `compliance_result` 与 `citations`，支持审计追踪；  
  * 标准版本与模型版本需可回溯，以便复现实验与结果。
````
