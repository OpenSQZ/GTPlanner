"""
短规划节点提示词模板
对应 agent/subflows/short_planning/nodes/short_planning_node.py
"""


class AgentsShortPlanningShortPlanningNodeTemplates:
    """短规划节点提示词模板类"""
    
    @staticmethod
    def get_short_planning_generation_zh() -> str:
        """中文版本的短规划生成提示词"""
        return """# 角色
你是一个经验丰富的系统架构师和工作流设计师。

# 任务
根据用户提供的【用户需求】、【推荐工具清单】和【技术调研结果】，生成一个清晰、简洁的步骤化流程，用于实现该需求。

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

# 输出要求
1. **步骤化流程：**
   * 列出清晰的、序号化的步骤。
   * 每个步骤应描述一个核心动作/阶段。
   * **优先使用推荐工具清单中的工具**，在步骤中指明使用哪个工具。格式如：`步骤X：[动作描述] (使用：[工具名称])`。
   * 结合技术调研结果中的关键发现，确保技术方案的可行性。
   * 如果无完全匹配工具，步骤应足够通用，允许用户后续集成自己的服务。
   * 指明可选步骤（例如，使用 `(可选)` 标记）。
   * 如果合适，可以建议并行处理的步骤。

2. **技术选型说明：**
   * 基于推荐工具和调研结果，说明关键技术选择的理由。
   * 指出潜在的技术风险和解决方案。

3. **设计考虑：**
   * 简要说明关键的设计决策，例如数据格式转换、错误处理思路等。
   * 考虑系统的可扩展性和维护性。

# 示例（用于理解输出格式和风格）
**用户需求示例：** YouTube视频总结器：将视频总结为Topic和QA。
**可用工具/MCP清单示例：**
youtube_audio_fetch: 获取YouTube视频的音频
ASR_MCP: 将音频转换为文本

**期望输出示例：**
1. Fetch: 获取YouTube视频内容 (如果输入是视频链接，可考虑使用 youtube_audio_fetch MCP 获取音频；如果直接是音频文件，则跳过此工具)。
2. ToText (可选): 如果上一步获取的是音频，将音频转换为文本 (可考虑使用 ASR_MCP)。如果输入已是文本，则跳过此步骤。
3. Extract: 从文本中提取关键主题 (Topics) 和潜在问题 (Questions)。
4. Process:
   * 并行处理每个Topic：为每个Topic生成总结。
   * 并行处理每个Question：为每个Question生成或定位答案的亮点。
5. Output: 生成结构化的输出，例如JSON或可视化的HTML信息图，包含Topic总结和QA对。
---

**输出：步骤化流程：**(只输出步骤化流程，不需要有多余的解释)"""
    
    @staticmethod
    def get_short_planning_generation_en() -> str:
        """English version of short planning generation prompt"""
        return """# Role
You are an experienced system architect and workflow designer.

# Task
Based on the provided【User Requirements】,【Recommended Tools List】, and【Technical Research Results】, generate a clear, concise step-by-step workflow to implement the requirements.

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
