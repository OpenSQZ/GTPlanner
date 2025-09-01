"""
节点识别节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/node_identification_node.py
"""


class AgentsDeepDesignNodeIdentificationNodeTemplates:
    """节点识别节点提示词模板类"""
    
    @staticmethod
    def get_node_identification_zh() -> str:
        """中文版本的节点识别提示词"""
        return """你是一个专业的pocketflow系统架构师，专门负责识别和定义系统中需要的各种Node节点。

请基于以下信息识别系统所需的Node节点：

**Agent分析结果：**
```
{analysis_markdown}
```

**用户需求：**
{user_requirements}

**项目规划：**
{short_planning}

**技术调研结果：**
{research_info}

**推荐工具：**
{tools_info}

请严格按照以下Markdown格式输出Node识别结果：

# Node识别结果

## 概述
基于Agent需求分析，识别出以下Node：

## 识别的Node列表

### 1. [Node名称1]

- **Node类型**: [Node/AsyncNode/BatchNode等]
- **目的**: [Node的具体目的和职责]
- **职责**: [Node负责的具体功能]
- **输入期望**: [期望的输入数据类型]
- **输出期望**: [期望的输出数据类型]
- **复杂度**: [简单/中等/复杂]
- **处理类型**: [数据预处理/核心计算/结果后处理/IO操作等]
- **推荐重试**: [是/否]

### 2. [Node名称2]

- **Node类型**: [Node/AsyncNode/BatchNode等]
- **目的**: [Node的具体目的和职责]
- **职责**: [Node负责的具体功能]
- **输入期望**: [期望的输入数据类型]
- **输出期望**: [期望的输出数据类型]
- **复杂度**: [简单/中等/复杂]
- **处理类型**: [数据预处理/核心计算/结果后处理/IO操作等]
- **推荐重试**: [是/否]

## Node类型统计
- **AsyncNode**: [数量]个
- **Node**: [数量]个
- **BatchNode**: [数量]个

## 设计理由
[为什么选择这些Node的设计理由]

识别要求：
1. 每个Node都有明确的单一职责
2. Node之间职责不重叠
3. 覆盖Agent的所有核心功能
4. 考虑数据流的完整性（输入→处理→输出）
5. 优先使用AsyncNode提高性能
6. 考虑错误处理和重试需求

常见Node模式参考：
- InputValidationNode: 输入验证和预处理
- DataRetrievalNode: 数据获取和检索
- CoreProcessingNode: 核心业务逻辑处理
- ResultFormattingNode: 结果格式化
- OutputDeliveryNode: 结果输出和传递

重要：请严格按照上述Markdown格式输出，直接输出完整的Markdown文档。"""
    
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
