"""
节点识别节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/node_identification_node.py
"""


class AgentsDeepDesignNodeIdentificationNodeTemplates:
    """节点识别节点提示词模板类"""
    
    @staticmethod
    def get_node_identification_zh() -> str:
        """中文版本的节点识别提示词"""
        return """你是pocketflow架构师。基于Agent需求，识别必要的Node节点。

**上下文：**
- Agent分析：{analysis_markdown}
- 用户需求：{user_requirements}
- 项目规划：{short_planning}
- 技术调研：{research_info}
- 推荐工具：{tools_info}

**关键原则：**
1. 单一职责，职责不重叠
2. 优先AsyncNode
3. 覆盖核心功能即可
4. 只设计后端处理Node，无前端相关Node

**严格按照Markdown格式输出：**

# Node识别

## Node列表

### 1. [Node名称]
- **类型**: [Node/AsyncNode]
- **职责**: [简要说明，15字内]
- **输入**: [数据类型]
- **输出**: [数据类型]

### 2. [Node名称]
- **类型**: [Node/AsyncNode]
- **职责**: [简要说明，15字内]
- **输入**: [数据类型]
- **输出**: [数据类型]

重要：每个Node描述不超过15字，只列出必要的Node"""
    
    @staticmethod
    def get_node_identification_en() -> str:
        """English version of node identification prompt"""
        return """You are a professional pocketflow system architect specializing in identifying and defining various Node components needed in the system.

Please identify the required Node components based on the following information:

**Agent Analysis Results:**
{analysis_markdown}

**User Requirements:**
{user_requirements}

**Project Planning:**
{short_planning}

**Technical Research Results:**
{research_info}

**Recommended Tools:**
{tools_info}

Please perform the following Node identification work:

1. **Core Functional Node Identification**:
   - Based on requirements analysis, identify Nodes needed to implement core functions
   - Each Node should have a single, clear responsibility
   - Ensure clear responsibility boundaries between Nodes

2. **Data Processing Node Identification**:
   - Identify Nodes related to data input, transformation, and output
   - Include Nodes for data validation, format conversion, storage, etc.
   - Consider data flow integrity and consistency

3. **External Integration Node Identification**:
   - Identify Nodes for integration with external systems, APIs, and services
   - Include Nodes for third-party tool calls, database operations, etc.
   - Consider error handling and retry mechanisms

4. **Control Flow Node Identification**:
   - Identify Nodes related to process control
   - Include Nodes for conditional judgment, loop processing, parallel execution, etc.
   - Ensure process flexibility and controllability

5. **Auxiliary Function Node Identification**:
   - Identify auxiliary Nodes for logging, monitoring, caching, etc.
   - Include Nodes related to error handling and performance optimization
   - Consider system observability and maintainability

For each identified Node, please provide:
- Node name and brief description
- Main responsibilities and functions
- Input and output data types
- Dependencies with other Nodes
- Implementation complexity assessment

Please output Node identification results in a structured format to provide a foundation for subsequent Flow design."""
    
    @staticmethod
    def get_node_identification_ja() -> str:
        """日本語版のノード識別プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_node_identification_es() -> str:
        """Versión en español del prompt de identificación de nodos"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_node_identification_fr() -> str:
        """Version française du prompt d'identification de nœuds"""
        return """# TODO: Ajouter le prompt en français"""
