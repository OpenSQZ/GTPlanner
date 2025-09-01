"""
文档生成节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/document_generation_node.py
"""


class AgentsDeepDesignDocumentGenerationNodeTemplates:
    """文档生成节点提示词模板类"""
    
    @staticmethod
    def get_document_generation_zh() -> str:
        """中文版本的文档生成提示词"""
        return """你是一个专业的技术文档编写专家，专门负责生成完整的Agent系统设计文档。

请基于以下信息生成完整的Markdown格式的Agent设计文档：

**项目标题：** {project_title}

**用户需求：**
{user_requirements}

**项目规划：**
{short_planning}

**推荐工具：**
{tools_info}

**技术调研结果：**
{research_findings}

**Agent分析结果：**
{analysis_markdown}

**识别的Node列表：**
{nodes_markdown}

**Flow设计：**
{flow_markdown}

**数据结构设计：**
{data_structure_markdown}

**详细Node设计：**
{node_design_markdown}

请生成一份完整的Markdown格式的Agent设计文档，必须包含以下部分：

# {project_title}

## 项目需求
基于Agent分析结果，清晰描述项目目标和功能需求。

## 工具函数
如果需要的话，列出所需的工具函数（如LLM调用、数据处理等）。

## Flow设计
详细描述pocketflow的Flow编排，包含：
- Flow的整体设计思路
- 节点连接和Action驱动的转换逻辑
- 完整的执行流程描述

### Flow图表
使用Mermaid flowchart TD语法，生成完整的Flow图表。

## 数据结构
详细描述shared存储的数据结构，包含：
- shared存储的整体设计
- 各个字段的定义和用途
- 数据流转模式

## Node设计
为每个Node提供详细设计，包含：
- Purpose（目的）
- Design（设计类型，如Node、AsyncNode等）
- Data Access（数据访问模式）
- 详细的prep/exec/post三阶段设计

请确保文档：
1. 遵循pocketflow的最佳实践
2. 体现关注点分离原则
3. 包含完整的Action驱动逻辑
4. 提供清晰的数据流设计
5. 使用专业的技术文档格式

输出完整的Markdown格式文档"""
    
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
