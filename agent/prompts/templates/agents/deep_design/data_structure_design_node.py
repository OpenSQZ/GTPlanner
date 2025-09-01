"""
数据结构设计节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/data_structure_design_node.py
"""


class AgentsDeepDesignDataStructureDesignNodeTemplates:
    """数据结构设计节点提示词模板类"""
    
    @staticmethod
    def get_data_structure_design_zh() -> str:
        """中文版本的数据结构设计提示词"""
        return """你是一个专业的数据架构设计师，专门为pocketflow框架设计shared存储数据结构。

请基于以下信息设计完整的shared数据结构：

**Agent分析结果：**
{analysis_markdown}

**Node识别结果：**
{nodes_markdown}

**Flow设计：**
{flow_markdown}

**用户需求：**
{user_requirements}

**项目规划：**
{short_planning}

**技术调研结果：**
{research_info}

**推荐工具：**
{tools_info}

请进行以下数据结构设计工作：

1. **核心数据模型设计**：
   - 设计支持整个Agent运行的核心数据结构
   - 定义数据实体、属性和关系
   - 确保数据模型的完整性和一致性

2. **shared字典结构设计**：
   - 设计pocketflow的shared存储结构
   - 定义各个Node之间共享的数据格式
   - 确保数据传递的高效性和准确性

3. **输入输出数据格式**：
   - 定义系统输入数据的标准格式
   - 设计各个处理阶段的中间数据格式
   - 规范最终输出数据的结构和格式

4. **状态管理数据结构**：
   - 设计Flow执行状态的数据结构
   - 定义错误处理和恢复所需的状态信息
   - 确保状态数据的可追踪性和可恢复性

5. **配置和元数据结构**：
   - 设计系统配置参数的数据结构
   - 定义Node和Flow的元数据格式
   - 确保配置的灵活性和可维护性

6. **性能优化数据结构**：
   - 设计缓存数据的结构和策略
   - 优化大数据量处理的数据格式
   - 考虑内存使用和访问效率

请严格按照以下JSON格式输出数据结构设计：

{
    "shared_structure_description": "shared存储的整体描述",
    "shared_fields": [
        {
            "field_name": "字段名称",
            "data_type": "数据类型（如：str, dict, list等）",
            "description": "字段描述",
            "purpose": "字段用途",
            "read_by_nodes": ["读取此字段的Node列表"],
            "written_by_nodes": ["写入此字段的Node列表"],
            "example_value": "示例值或结构",
            "required": true/false
        }
    ],
    "data_flow_patterns": [
        {
            "pattern_name": "数据流模式名称",
            "description": "数据流描述",
            "involved_fields": ["涉及的字段"],
            "flow_sequence": ["数据流转顺序"]
        }
    ],
    "shared_example": {
        "field1": "示例值1",
        "field2": {},
        "field3": []
    }
}

对于数据结构设计，请提供：
- 完整的数据结构定义（JSON Schema格式）
- 详细的字段说明和约束条件
- 数据流转和变换规则
- 数据验证和错误处理机制
- 性能优化建议

请以结构化的格式输出数据结构设计结果，确保设计的完整性和实用性。"""
    
    @staticmethod
    def get_data_structure_design_en() -> str:
        """English version of data structure design prompt"""
        return """You are a professional data architecture designer specializing in designing shared storage data structures for the pocketflow framework.

Please design a complete shared data structure based on the following information:

**Agent Analysis Results:**
{analysis_markdown}

**Node Identification Results:**
{nodes_markdown}

**Flow Design:**
{flow_markdown}

**User Requirements:**
{user_requirements}

**Project Planning:**
{short_planning}

**Technical Research Results:**
{research_info}

**Recommended Tools:**
{tools_info}

Please perform the following data structure design work:

1. **Core Data Model Design**:
   - Design core data structures supporting the entire Agent operation
   - Define data entities, attributes, and relationships
   - Ensure data model integrity and consistency

2. **Shared Dictionary Structure Design**:
   - Design pocketflow's shared storage structure
   - Define shared data formats between various Nodes
   - Ensure efficiency and accuracy of data transfer

3. **Input/Output Data Formats**:
   - Define standard formats for system input data
   - Design intermediate data formats for various processing stages
   - Standardize final output data structure and format

4. **State Management Data Structures**:
   - Design data structures for Flow execution states
   - Define state information needed for error handling and recovery
   - Ensure traceability and recoverability of state data

5. **Configuration and Metadata Structures**:
   - Design data structures for system configuration parameters
   - Define metadata formats for Nodes and Flows
   - Ensure configuration flexibility and maintainability

6. **Performance Optimization Data Structures**:
   - Design cache data structures and strategies
   - Optimize data formats for large data volume processing
   - Consider memory usage and access efficiency

For data structure design, please provide:
- Complete data structure definitions (JSON Schema format)
- Detailed field descriptions and constraint conditions
- Data flow and transformation rules
- Data validation and error handling mechanisms
- Performance optimization recommendations

Please output data structure design results in a structured format, ensuring design completeness and practicality."""
    
    @staticmethod
    def get_data_structure_design_ja() -> str:
        """日本語版のデータ構造設計プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_data_structure_design_es() -> str:
        """Versión en español del prompt de diseño de estructura de datos"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_data_structure_design_fr() -> str:
        """Version française du prompt de conception de structure de données"""
        return """# TODO: Ajouter le prompt en français"""
