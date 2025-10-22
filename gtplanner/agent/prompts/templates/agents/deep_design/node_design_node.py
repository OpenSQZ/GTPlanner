"""
节点设计节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/node_design_node.py
"""


class AgentsDeepDesignNodeDesignNodeTemplates:
    """节点设计节点提示词模板类"""
    
    @staticmethod
    def get_node_design_zh() -> str:
        """中文版本的节点设计提示词"""
        return """你是pocketflow Node设计师。为指定Node设计实现方案。

**当前Node：**
{node_info_text}

**上下文：**
- Node列表：{nodes_markdown}
- Agent分析：{analysis_markdown}
- Flow设计：{flow_markdown}
- 数据结构：{data_structure_json}
- 用户需求：{user_requirements}
- 项目规划：{short_planning}
- 技术调研：{research_info}
- 推荐工具：{tools_info}

**关键约定：**
- AsyncNode: 用 prep_async/exec_async/post_async
- 同步Node: 用 prep/exec/post
- exec阶段不能访问shared

**严格按照Markdown格式输出：**

# Node设计: [Node名]

## 基本信息
- **类型**: [AsyncNode/Node]
- **职责**: [简述，15字内]

## Prep阶段
- **读取**: [shared字段]
- **验证**: [简述，10字内]

## Exec阶段
- **逻辑**: [简述，15字内]
- **关键步骤**: [1-2步即可]

## Post阶段
- **写入**: [shared字段]
- **Action**: [返回的action]

## 数据访问
- **读**: [字段]
- **写**: [字段]

重要：每部分保持简洁，重点在核心逻辑"""

    
    @staticmethod
    def get_node_design_en() -> str:
        """English version of node design prompt"""
        return """You are a professional pocketflow Node designer specializing in designing Node implementations based on the pocketflow framework.

Please design detailed Node implementation solutions based on the following information:

{node_info_text}**Node Information:**
{nodes_markdown}

**Agent Analysis Results:**
{analysis_markdown}

**Flow Design:**
{flow_markdown}

**Data Structure Design:**
{data_structure_json}

**User Requirements:**
{user_requirements}

**Project Planning:**
{short_planning}

**Technical Research Results:**
{research_info}

**Recommended Tools:**
{tools_info}

Please perform the following Node design work:

1. **Node Class Structure Design**:
   - Design Node class inheriting from pocketflow.AsyncNode
   - Define basic attributes and configuration of the Node
   - Ensure Node reusability and extensibility

2. **prep_async Method Design**:
   - Design data preparation and validation logic
   - Define input parameter acquisition and processing
   - Implement error checking and exception handling

3. **exec_async Method Design**:
   - Design core business logic implementation
   - Define asynchronous processing flows and algorithms
   - Implement integration calls with external services

4. **post_async Method Design**:
   - Design result processing and output logic
   - Define shared data updates and transfers
   - Implement state management and process control

5. **Auxiliary Method Design**:
   - Design private auxiliary method implementations
   - Define utility functions and common logic
   - Implement code modularity and maintainability

6. **Error Handling and Logging**:
   - Design comprehensive exception handling mechanisms
   - Implement detailed logging and monitoring
   - Ensure Node robustness and debuggability

For each Node design, please provide:
- Complete Python class implementation code
- Detailed method descriptions and parameter definitions
- Error handling and boundary condition processing
- Performance optimization and best practice recommendations
- Unit test case design

Please output Node design results in a structured format, ensuring code quality and maintainability."""
    
    @staticmethod
    def get_node_design_ja() -> str:
        """日本語版のノード設計プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_node_design_es() -> str:
        """Versión en español del prompt de diseño de nodos"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_node_design_fr() -> str:
        """Version française du prompt de conception de nœuds"""
        return """# TODO: Ajouter le prompt en français"""
