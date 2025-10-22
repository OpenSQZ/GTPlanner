"""
文档生成节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/document_generation_node.py
"""


class AgentsDeepDesignDocumentGenerationNodeTemplates:
    """文档生成节点提示词模板类"""
    
    @staticmethod
    def get_document_generation_zh() -> str:
        """中文版本的文档生成提示词"""
        return """你是技术文档专家。整合所有设计结果，生成简洁的Agent设计文档。

**上下文：**
- 项目标题：{project_title}
- 用户需求：{user_requirements}
- 项目规划：{short_planning}
- 推荐工具：{tools_info}
- 技术调研：{research_findings}
- Agent分析：{analysis_markdown}
- Node列表：{nodes_markdown}
- Flow设计：{flow_markdown}
- 数据结构：{data_structure_markdown}
- Node设计：{node_design_markdown}

**文档要求：**
1. 整合上述信息，去除冗余
2. 保持简洁，重点突出
3. 适合下游AI生成代码
4. **只包含后端逻辑，不涉及前端UI、界面、用户交互等内容**

**严格按照Markdown格式输出：**

# {project_title}

## 项目概述
[2-3句话说明项目目标和功能]

## 核心功能
- [功能1]
- [功能2]

## Flow设计
### Flow图
```mermaid
[Flow图表]
```

### 编排代码
```python
[编排代码]
```

## 数据结构 (shared)
```json
[JSON格式的shared结构]
```

## Node设计

### [Node1名称]
- **类型**: [AsyncNode/Node]
- **职责**: [简述]
- **Prep**: 读取 [字段]
- **Exec**: [核心逻辑]
- **Post**: 写入 [字段], 返回 [action]

### [Node2名称]
- **类型**: [AsyncNode/Node]
- **职责**: [简述]
- **Prep**: 读取 [字段]
- **Exec**: [核心逻辑]
- **Post**: 写入 [字段], 返回 [action]

重要：整合所有信息，删除重复内容，保持文档精简"""
    
    @staticmethod
    def get_document_generation_en() -> str:
        """English version of document generation prompt"""
        return """You are a professional technical documentation expert specializing in generating complete Agent system design documents.

Please generate a complete Markdown format Agent design document based on the following information:

**Project Title:** {project_title}

**User Requirements:**
{user_requirements}

**Project Planning:**
{short_planning}

**Recommended Tools:**
{tools_info}

**Technical Research Results:**
{research_findings}

**Agent Analysis Results:**
{analysis_markdown}

**Identified Node List:**
{nodes_markdown}

**Flow Design:**
{flow_markdown}

**Data Structure Design:**
{data_structure_markdown}

**Detailed Node Design:**
{node_design_markdown}

Please generate a complete Markdown format Agent design document that must include the following sections:

# {project_title}

## Project Requirements
Based on Agent analysis results, clearly describe project objectives and functional requirements.

## Utility Functions
If needed, list required utility functions (such as LLM calls, data processing, etc.).

## Flow Design
Detailed description of pocketflow Flow orchestration, including:
- Overall Flow design philosophy
- Node connections and Action-driven transition logic
- Complete execution process description

### Flow Diagram
Use Mermaid flowchart TD syntax to generate a complete Flow diagram.

## Data Structure Design
Detailed description of shared data structures, including:
- Core data models
- Input/output formats
- State management structures

## Node Implementation
For each identified Node, provide:
- Node responsibilities and functional descriptions
- Detailed implementation solutions
- Key method design explanations

## Deployment and Operation
Describe system deployment requirements and operation methods.

## Testing Strategy
Provide testing solutions and validation methods.

Please ensure the document structure is clear, content is complete, technical details are accurate, and it's easy for development teams to understand and implement."""
    
    @staticmethod
    def get_document_generation_ja() -> str:
        """日本語版のドキュメント生成プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_document_generation_es() -> str:
        """Versión en español del prompt de generación de documentos"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_document_generation_fr() -> str:
        """Version française du prompt de génération de documents"""
        return """# TODO: Ajouter le prompt en français"""
