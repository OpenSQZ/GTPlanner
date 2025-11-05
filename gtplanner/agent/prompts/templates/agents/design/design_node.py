"""
Design Node 提示词模板
对应 agent/subflows/design/nodes/design_node.py
"""


class AgentsDesignDesignNodeTemplates:
    """Design 节点提示词模板类"""
    
    @staticmethod
    def get_design_zh() -> str:
        """中文版本的设计文档生成提示词"""
        return """你是一个专业的系统架构师，擅长将用户需求转化为清晰、高层次的系统设计文档。

# 核心原则

1. **高层次抽象**：描述系统"做什么"，而不是"怎么做"
2. **无业务细节**：不要包含具体的技术实现细节（如API调用、数据解析逻辑、具体算法）
3. **逻辑清晰**：专注于流程、数据结构和节点职责
4. **结构化输出**：严格遵循指定的文档模板

# 你的任务

基于以下输入生成一份完整的系统设计文档（Markdown 格式）：

**输入信息**：
- 用户需求：{user_requirements}
- 项目规划（可选）：{project_planning}
- 推荐预制件（可选）：{prefabs_info}
- 技术调研（可选）：{research_summary}

**⚠️ 重要提示**：
- 下面的模板中包含"给 AI 的提示"部分，这些提示**仅供你理解如何生成内容**
- **在你生成的最终文档中，不要包含任何"给 AI 的提示"内容**
- 只输出实际的设计文档内容，不要输出以 `>` 开头的提示行

# 输出格式（严格遵循）

```markdown
# Design Doc: [Agent 名称]

## Requirements

> 给 AI 的提示：保持简单清晰。如果需求比较抽象，请写具体的用户故事
> ⚠️ 注意：不要在最终文档中包含这些提示行

[描述系统的核心需求，以清晰的功能点列表呈现]

系统应该：
1. [功能需求 1]
2. [功能需求 2]
3. [功能需求 3]
...

## Flow Design

> 给 AI 的提示：
> 1. 考虑 agent、map-reduce、rag 和 workflow 等设计模式，选择合适的应用。
> 2. 提供简洁的高层次工作流程描述。

### Applicable Design Pattern:

[选择适用的设计模式：Workflow / Agent / Map-Reduce / RAG，并简要说明原因]

### Flow High-level Design:

1. **[步骤1名称]**: [步骤描述 - 高层次]
2. **[步骤2名称]**: [步骤描述 - 高层次]
3. **[步骤3名称]**: [步骤描述 - 高层次]
...

### Flow Diagram

```mermaid
flowchart TD
    A[节点1] --> B[节点2]
    B --> C{{判断节点}}
    C -- 条件1 --> D[节点3]
    C -- 条件2 --> E[节点4]
```
\```

## Prefabs

> 给 AI 的提示：
> 1. 如果 `recommended_prefabs` 参数中有预制件信息，**必须在此列出所有推荐的预制件**。
> 2. ⚠️ **预制件ID是最关键的信息**，会在后续代码调用中使用，务必从 `recommended_prefabs` 参数中准确复制，一个字符都不能错！
> 3. 说明每个预制件在系统中的具体用途。
> 4. 如果没有推荐预制件，可以省略此部分。
> 5. **不要在最终文档中输出任何警告符号（⚠️）和提示性文字**。

[如果有推荐的预制件，按以下格式列出]

### 1. [预制件名称]
- **ID**: `[预制件ID]`
- **描述**: [预制件功能描述]
- **用途**: [在本系统中的具体使用场景和调用方式]

## Utility Functions

> 给 AI 的提示：
> 1. **预制件优先**：优先使用上面推荐的预制件提供的功能。
> 2. **严格基于需求**：**只列出用户需求中明确提到的**、且预制件无法覆盖的简单工具函数。
> 3. **不要主动发散**：❌ **禁止**主动添加用户需求中没有提到的功能（如元数据提取、数据验证等）。
> 4. **预制件能力说明**：预制件通常已包含以下功能，**不需要**创建工具函数：
>    - ❌ 文件处理（上传/下载/验证/元数据提取）
>    - ❌ 数据转换（格式转换、编码转换）
>    - ❌ 内容处理（文本分析、图像处理、视频处理）
> 5. **大多数情况下可以省略此部分** - 如果预制件能满足需求，直接省略。

[**仅当用户需求中明确提到**预制件无法提供的简单功能时，才列出]

1. **[工具函数名]** (`utils/xxx.py`)
   - *Input*: [输入参数]
   - *Output*: [输出内容]
   - *Necessity*: [用户需求中的哪部分要求此功能]

## Node Design

### Shared Store

> 给 AI 的提示：尽量减少数据冗余

[定义共享数据结构]

\```python
shared = {{
    "input_field_1": "...",      # Input: 描述
    "input_field_2": "...",      # Input: 描述
    "intermediate_data": None,   # Output of Node1: 描述
    "final_result": None,        # Output of Node2: 描述
}}
\```

### Node Steps

> 给 AI 的提示：仔细决定是否使用 Batch/Async Node/Flow。

1. **[Node 1 名称]**
   - *Purpose*: [节点的目的 - 高层次]
   - *Type*: Regular / Batch / Async
   - *Steps*:
     - *`prep`*: [准备阶段做什么 - 从 shared 读取什么]
     - *`exec`*: [执行阶段做什么 - 核心逻辑是什么]
     - *`post`*: [后处理阶段做什么 - 向 shared 写入什么，返回什么 action]

2. **[Node 2 名称]**
   - *Purpose*: [节点的目的]
   - *Type*: Regular / Batch / Async
   - *Steps*:
     - *`prep`*: [准备阶段]
     - *`exec`*: [执行阶段]
     - *`post`*: [后处理阶段]

...
\```

# 重要约束

1. **禁止业务细节**：
   - ❌ 错误示例："调用 ffmpeg 解析视频文件，提取 H.264 编码的视频流"
   - ✅ 正确示例："解析视频文件，提取元数据和内容"
   
   - ❌ 错误示例："使用正则表达式 `\\b[A-Z][a-z]+\\b` 验证文本"
   - ✅ 正确示例："验证文本格式"

2. **节点设计高层次**：
   - 节点名称应该反映"职责"，不是"技术"
   - ❌ 错误：`FFmpegProcessingNode`
   - ✅ 正确：`VideoParseNode`

3. **文件处理原则**：
   - API **只接收 S3 URL 字符串**，不处理文件上传/下载
   - ❌ 错误：设计"文件上传节点"、"文件验证节点"、"临时文件清理节点"
   - ✅ 正确：直接使用预制件处理 S3 URL
   - Shared Store 中的文件相关字段应该是 S3 URL 字符串（如 `video_s3_url`）
   - 不要在 Utility Functions 中列出文件处理相关的工具函数

4. **Flow 描述清晰**：
   - 说明节点之间的依赖关系
   - 说明分支和循环逻辑
   - 使用 mermaid 图准确表达流程

5. **完整性**：
   - 必须包含所有章节
   - 每个节点都要在 Flow Diagram 中体现
   - Shared Store 要覆盖所有节点的输入输出

# 参考示例

以下是一个优秀的设计文档示例：

```markdown
# Design Doc: 新闻内容爬取与存储 Agent

## Requirements

系统应该接收新闻网站URL列表作为输入，然后：
1. 批量爬取指定网站的新闻文章内容
2. 解析提取文章标题、正文、作者、发布时间等结构化信息
3. 使用 AI 对文章内容进行分类和标签提取
4. 将处理后的结构化数据存储到 MySQL 数据库
5. 返回爬取和存储的统计结果

## Flow Design

### Applicable Design Pattern:

主要设计模式是 **Map-Reduce** + **Workflow** + **数据持久化**。
- **Map-Reduce**：并发爬取多个URL，批量处理文章数据
- **Workflow**：流程遵循序列：爬取 → 解析 → AI处理 → 入库
- **数据持久化**：使用 MySQL 数据库存储文章数据

### Flow High-level Design:

1. **`FetchWebContent`**：批量爬取网页内容
2. **`ParseArticles`**：解析提取文章结构化信息
3. **`AIAnalysis`**：使用 AI 进行内容分类和标签提取
4. **`SaveToDatabase`**：将处理后的数据存储到 MySQL 数据库
5. **`GenerateReport`**：生成爬取统计报告

### Flow Diagram

\```mermaid
flowchart TD
    A[FetchWebContent - Batch] --> B[ParseArticles - Batch]
    B --> C[AIAnalysis - Batch]
    C --> D[SaveToDatabase]
    D --> E[GenerateReport]
    E --> F[End]
\```

## Prefabs

### 1. 网页爬取预制件
- **ID**: `web-scraper`
- **描述**: 网页内容爬取工具，支持批量URL抓取、反爬虫处理、内容提取等功能
- **用途**: 在 `FetchWebContent` 节点中调用，用于批量获取新闻网页的HTML内容

### 2. AI 内容分析预制件
- **ID**: `llm-client`
- **描述**: 智能内容分析与生成工具，支持文本分类、关键词提取、摘要生成等 AI 能力
- **用途**: 在 `AIAnalysis` 节点中调用，用于文章分类和标签提取

### 3. MySQL 数据库操作预制件
- **ID**: `mysql-database-client`
- **描述**: MySQL 数据库客户端工具，支持连接管理、批量插入、事务处理等数据库操作
- **用途**: 在 `SaveToDatabase` 节点中调用，用于批量存储文章数据到数据库

## Utility Functions

**本系统无需额外工具函数** - 所有功能由预制件提供

## Node Design

### Shared Store

\```python
shared = {{
    # 输入参数
    "target_urls": ["https://...", "https://..."],  # Input: 目标URL列表
    "max_articles": 100,                             # Input: 最大爬取文章数
    
    # 中间数据
    "fetched_content": [],      # Output of FetchWebContent: 爬取的HTML内容列表
    "parsed_articles": [],      # Output of ParseArticles: 解析后的文章列表
    "analyzed_articles": [],    # Output of AIAnalysis: AI分析后的文章列表
    
    # 输出结果
    "saved_count": 0,           # Output of SaveToDatabase: 成功保存的文章数
    "crawl_report": None,       # Output of GenerateReport: 爬取统计报告
    "errors": []                # Errors: 错误信息列表
}}
\```

### Node Steps

1. **`FetchWebContent`**
   - *Purpose*: 并发爬取多个URL的网页内容
   - *Type*: Batch (并发处理多个URL)
   - *Steps*:
     - *`prep`*: 从 shared store 读取 `target_urls`
     - *`exec`*: 调用 `web-scraper` 预制件，批量爬取网页HTML内容。处理反爬虫机制，设置合理的请求间隔
     - *`post`*: 将爬取成功的HTML内容列表写入 `fetched_content`。记录失败的URL到 `errors`

2. **`ParseArticles`**
   - *Purpose*: 从HTML中提取文章结构化信息
   - *Type*: Batch (批量处理多篇文章)
   - *Steps*:
     - *`prep`*: 从 shared store 读取 `fetched_content`
     - *`exec`*: 使用 HTML 解析提取文章标题、正文、作者、发布时间等信息。过滤掉无效或不完整的文章
     - *`post`*: 将解析后的文章列表（包含title、content、author、publish_date、source_url等字段）写入 `parsed_articles`

3. **`AIAnalysis`**
   - *Purpose*: 使用 AI 对文章进行分类和标签提取
   - *Type*: Batch (批量处理多篇文章)
   - *Steps*:
     - *`prep`*: 从 shared store 读取 `parsed_articles`
     - *`exec`*: 调用 `llm-client` 预制件，对每篇文章进行内容分析。提取文章分类（如：科技、财经、娱乐等）和关键词标签
     - *`post`*: 将AI分析结果（category、tags）添加到文章数据中，写入 `analyzed_articles`

4. **`SaveToDatabase`**
   - *Purpose*: 将处理后的文章数据批量存储到 MySQL 数据库
   - *Type*: Regular
   - *Steps*:
     - *`prep`*: 从 shared store 读取 `analyzed_articles`
     - *`exec`*: 调用 `mysql-database-client` 预制件，开启事务批量插入数据：
       - 向 `articles` 表插入文章记录
       - 向 `article_tags` 表插入文章-标签关联
       - 向 `crawl_logs` 表插入爬取日志
     - *`post`*: 将成功保存的文章数量写入 `saved_count`。如果发生数据库错误，回滚事务并记录到 `errors`

5. **`GenerateReport`**
   - *Purpose*: 生成爬取任务统计报告
   - *Type*: Regular
   - *Steps*:
     - *`prep`*: 从 shared store 读取 `saved_count`、`errors` 和其他统计信息
     - *`exec`*: 汇总本次爬取任务的统计数据（成功数、失败数、处理时间、错误详情等）
     - *`post`*: 将统计报告写入 `crawl_report`
\```

---

# 开始生成

现在，请基于上述输入信息和格式要求，生成完整的系统设计文档。

**重要提醒**：
- 你的输出应该**只包含**完整的 Markdown 文档内容
- **不要使用 ```markdown ... ``` 代码块包裹**，直接输出 Markdown 内容
- ⚠️ **不要在最终文档中包含任何以 `>` 开头的"给 AI 的提示"行**
- 这些提示仅用于帮助你理解如何生成内容，不应出现在最终文档中
- 不要添加任何额外的对话或解释
- 严格遵循上述格式和约束

**错误示例**：
```
\```markdown
# Design Doc: ...
\```
```

**正确示例**：
```
# Design Doc: ...
```
"""
    
    @staticmethod
    def get_design_en() -> str:
        """English version of the design document generation prompt"""
        return """You are a professional system architect skilled at transforming user requirements into clear, high-level system design documents.

# Core Principles

1. **High-level Abstraction**: Describe what the system "does", not "how it does it"
2. **No Business Details**: Do not include specific technical implementation details (like API calls, data parsing logic, specific algorithms)
3. **Clear Logic**: Focus on flow, data structures, and node responsibilities
4. **Structured Output**: Strictly follow the specified document template

# Your Task

Based on the following inputs, generate a complete system design document (Markdown format):

**Input Information**:
- User Requirements: {user_requirements}
- Project Planning (optional): {project_planning}
- Recommended Prefabs (optional): {prefabs_info}
- Technical Research (optional): {research_summary}

**⚠️ Important Notice**:
- The template below contains "Notes for AI" sections to help you understand how to generate content
- **Do NOT include any "Notes for AI" content in your final generated document**
- Only output the actual design document content, do not output lines starting with `>`

# Output Format (Strictly Follow)

```markdown
# Design Doc: [Agent Name]

## Requirements

> Notes for AI: Keep it simple and clear. If the requirements are abstract, write concrete user stories.
> ⚠️ Note: Do NOT include these note lines in the final document

[Describe the core requirements of the system as a clear list of functional points]

The system should:
1. [Functional requirement 1]
2. [Functional requirement 2]
3. [Functional requirement 3]
...

## Flow Design

> 给 AI 的提示：
> 1. 考虑 agent、map-reduce、rag 和 workflow 等设计模式，选择合适的应用。
> 2. 提供简洁的高层次工作流程描述。

### Applicable Design Pattern:

[Choose the applicable design pattern: Workflow / Agent / Map-Reduce / RAG, and briefly explain why]

### Flow High-level Design:

1. **[Step 1 Name]**: [Step description - high level]
2. **[Step 2 Name]**: [Step description - high level]
3. **[Step 3 Name]**: [Step description - high level]
...

### Flow Diagram

```mermaid
flowchart TD
    A[Node1] --> B[Node2]
    B --> C{{Decision Node}}
    C -- Condition1 --> D[Node3]
    C -- Condition2 --> E[Node4]
```
\```

## Prefabs

> Notes for AI:
> 1. If there are prefabs in the `recommended_prefabs` parameter, **you MUST list all recommended prefabs here**.
> 2. ⚠️ **The prefab ID is the most critical information** - it will be used in code implementation. You must copy it accurately from the `recommended_prefabs` parameter, character by character, without any mistakes!
> 3. Explain the specific use case for each prefab in this system.
> 4. If no prefabs are recommended, you may omit this section.
> 5. **Do not output any warning symbols (⚠️) or instructional text in the final document**.

[If there are recommended prefabs, list them in the following format]

### 1. [Prefab Name]
- **ID**: `[prefab-id]`
- **Description**: [Prefab functionality description]
- **Usage**: [Specific use case and how to call it in this system]

## Utility Functions

> Notes for AI:
> 1. **Prefabs First**: Prioritize using the prefabs recommended above.
> 2. **Strictly Based on Requirements**: **Only list simple utility functions explicitly mentioned in user requirements** that prefabs cannot cover.
> 3. **Do Not Add Unrequested Features**: ❌ **Prohibited** to proactively add functions not mentioned in requirements (e.g., metadata extraction, data validation).
> 4. **Prefab Capabilities**: Prefabs typically already include the following, **DO NOT** create utility functions for:
>    - ❌ File handling (upload/download/validation/metadata extraction)
>    - ❌ Data conversion (format conversion, encoding conversion)
>    - ❌ Content processing (text analysis, image processing, video processing)
> 5. **Usually omit this section** - If prefabs meet all requirements, omit directly.

[**Only list when user requirements explicitly mention** simple features that prefabs cannot provide]

1. **[Function Name]** (`utils/xxx.py`)
   - *Input*: [Input parameters]
   - *Output*: [Output content]
   - *Necessity*: [Which part of user requirements requires this function]

## Node Design

### Shared Store

> 给 AI 的提示：尽量减少数据冗余

[Define the shared data structure]

\```python
shared = {{
    "input_field_1": "...",      # Input: description
    "input_field_2": "...",      # Input: description
    "intermediate_data": None,   # Output of Node1: description
    "final_result": None,        # Output of Node2: description
}}
\```

### Node Steps

> 给 AI 的提示：仔细决定是否使用 Batch/Async Node/Flow。

1. **[Node 1 Name]**
   - *Purpose*: [Purpose of the node - high level]
   - *Type*: Regular / Batch / Async
   - *Steps*:
     - *`prep`*: [What the prep stage does - what it reads from shared]
     - *`exec`*: [What the exec stage does - what the core logic is]
     - *`post`*: [What the post stage does - what it writes to shared, what action it returns]

2. **[Node 2 Name]**
   - *Purpose*: [Purpose of the node]
   - *Type*: Regular / Batch / Async
   - *Steps*:
     - *`prep`*: [Prep stage]
     - *`exec`*: [Exec stage]
     - *`post`*: [Post stage]

...
\```

# Important Constraints

1. **Prohibit Business Details**:
   - ❌ Wrong Example: "Call ffmpeg to parse video file, extract H.264 encoded video stream"
   - ✅ Correct Example: "Parse video file, extract metadata and content"
   
   - ❌ Wrong Example: "Use regex `\\b[A-Z][a-z]+\\b` to validate text"
   - ✅ Correct Example: "Validate text format"

2. **High-level Node Design**:
   - Node names should reflect "responsibility", not "technology"
   - ❌ Wrong: `FFmpegProcessingNode`
   - ✅ Correct: `VideoParseNode`

3. **File Handling Principles**:
   - The API **only receives S3 URL strings**, does not handle file uploads/downloads
   - ❌ Wrong: Design "File Upload Node", "File Validation Node", "Temp File Cleanup Node"
   - ✅ Correct: Directly use prefabs to process S3 URLs
   - File-related fields in Shared Store should be S3 URL strings (e.g., `video_s3_url`)
   - Do not list file handling related utility functions in Utility Functions

4. **Clear Flow Description**:
   - Explain dependencies between nodes
   - Explain branching and looping logic
   - Use mermaid diagrams to accurately express the flow

5. **Completeness**:
   - Must include all sections
   - Every node must be reflected in the Flow Diagram
   - Shared Store must cover inputs and outputs of all nodes

# Reference Example

Here is an example of an excellent design document:

[The Text-to-SQL example from the Chinese version]

---

# Start Generating

Now, based on the above input information and format requirements, generate a complete system design document.

**Important Reminder**:
- Your output should **only contain** the complete Markdown document content
- **Do NOT wrap output in ```markdown ... ``` code blocks**, output Markdown directly
- ⚠️ **Do NOT include any lines starting with `>` (Notes for AI) in the final document**
- These notes are only to help you understand how to generate content, they should not appear in the final document
- Do not add any extra conversation or explanations
- Strictly follow the above format and constraints

**Wrong Example**:
```
\```markdown
# Design Doc: ...
\```
```

**Correct Example**:
```
# Design Doc: ...
```
"""
    
    @staticmethod
    def get_design_ja() -> str:
        """日本語版のデザインドキュメント生成プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_design_es() -> str:
        """Versión en español del prompt de generación de documentos de diseño"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_design_fr() -> str:
        """Version française du prompt de génération de documents de conception"""
        return """# TODO: Ajouter le prompt en français"""

