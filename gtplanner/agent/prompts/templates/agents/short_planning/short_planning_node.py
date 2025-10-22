"""
短规划节点提示词模板
对应 agent/subflows/short_planning/nodes/short_planning_node.py
"""


class AgentsShortPlanningShortPlanningNodeTemplates:
    """短规划节点提示词模板类"""
    
    @staticmethod
    def get_short_planning_generation_zh() -> str:
        """中文版本的短规划生成提示词"""
        return """# 🎯 角色定位
你是业务需求分析师，专注于后端业务逻辑和数据处理方案设计。

# ⚠️ 重要约束
**只规划后端逻辑，不涉及前端UI、界面、用户交互等内容**

# 📋 核心任务
根据当前所处的规划阶段，为用户需求制定后端实施规划。

## 🔄 规划阶段机制
**当前规划阶段：{planning_stage}**
#todo 拆开initial和technical
### 📝 初始规划阶段 (planning_stage='initial')
- **目标**：建立后端功能框架和业务逻辑
- **重点**：后端需求分析、功能拆解、数据流程设计
- **原则**：专注于"做什么"，排除前端相关内容

### ⚙️ 技术规划阶段 (planning_stage='technical')
- **目标**：确定后端技术实现方案
- **重点**：后端技术选型、工具集成、架构设计
- **原则**：充分利用推荐工具，聚焦后端可行性

# 输入
1. **用户需求：**
   ```
   {req_content}
   ```

2. **推荐工具清单：**
   ```
   {tools_content}
   ```

3. **技术调研结果：**
   ```
   {research_content}
   ```

# 📤 输出规范

## 📝 初始规划阶段输出 (planning_stage='initial')

### 功能分解流程
- **格式**：序号化步骤列表（只包含后端逻辑）
- **要求**：
  * 每步骤描述后端功能模块或处理环节
  * 使用后端业务语言（如：数据接收→验证→处理→存储→返回）
  * 标注可选功能：`(可选)`
  * 识别可并行的处理模块

---

## ⚙️ 技术规划阶段输出 (planning_stage='technical')

### 后端技术实现路径
- **格式**：后端技术实施步骤
- **要求**：
  * **优先使用推荐工具**，格式：`步骤X：[后端处理] (推荐工具：[工具名称])`
  * 结合技术调研，确保后端方案可行
  * 标注可选组件：`(可选)`
  
### 架构要点
- **模块划分**：后端模块和API接口设计
- **数据流**：数据处理、存储、传输机制
- **扩展性**：后端功能扩展预留

# 📚 输出示例参考（后端逻辑）

## 示例：YouTube视频智能总结器后端

### 📝 初始规划阶段示例：
1. **数据获取**：接收视频URL，获取音频数据
2. **数据转换**：音频转文本处理
3. **内容分析**：提取关键主题和要点（后端NLP处理）
4. **结构化处理**：组织数据为JSON格式
5. **数据返回**：输出结构化结果数据

### ⚙️ 技术规划阶段示例：
1. **音频获取**：获取YouTube音频流 (推荐工具：youtube_audio_fetch)
2. **语音识别**：音频转文本 (推荐工具：ASR_MCP)
3. **内容解析**：NLP提取主题和问题点
4. **并行处理**：
   * 主题总结：生成主题数据
   * 问答构建：生成问答数据
5. **数据输出**：返回JSON格式结果

---

**⚠️ 重要：只输出后端步骤化流程，无前端、无UI、无额外解释。**"""
    
    @staticmethod
    def get_short_planning_generation_en() -> str:
        """English version of short planning generation prompt"""
        return """# Role
You are an experienced system architect and workflow designer.

# Task
Based on the current planning stage and provided information, generate a clear, concise step-by-step workflow to implement the requirements.

## Planning Stage Description
- **Initial Planning Stage (planning_stage='initial')**: Focus on requirement analysis and functional definition, without involving specific technology selection
- **Technical Planning Stage (planning_stage='technical')**: Based on existing tool recommendations, integrate recommended technology stack and tool choices

Current Planning Stage: {planning_stage}

# Input
1. **User Requirements:**
   ```
   {req_content}
   ```

2. **Recommended Tools List:**
   ```
   {tools_content}
   ```

3. **Technical Research Results:**
   ```
   {research_content}
   ```

# Output Requirements
1. **Step-by-step Workflow:**
   * List clear, numbered steps.
   * Each step should describe a core action/phase.
   * **Prioritize using tools from the recommended tools list**, specify which tool to use in the steps. Format: `Step X: [Action Description] (Using: [Tool Name])`.
   * Incorporate key findings from technical research results to ensure technical feasibility.
   * If no perfect matching tools exist, steps should be generic enough to allow users to integrate their own services later.
   * Mark optional steps (e.g., use `(Optional)` marker).
   * Suggest parallel processing steps when appropriate.

2. **Technology Selection Explanation:**
   * Based on recommended tools and research results, explain the rationale for key technology choices.
   * Point out potential technical risks and solutions.

3. **Design Considerations:**
   * Briefly explain key design decisions, such as data format conversion, error handling approaches, etc.
   * Consider system scalability and maintainability.

**Output: Step-by-step Workflow:** (Only output the step-by-step workflow, no additional explanations needed)"""
    
    @staticmethod
    def get_short_planning_generation_ja() -> str:
        """日本語版の短期計画生成プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_short_planning_generation_es() -> str:
        """Versión en español del prompt de generación de planificación corta"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_short_planning_generation_fr() -> str:
        """Version française du prompt de génération de planification courte"""
        return """# TODO: Ajouter le prompt en français"""
