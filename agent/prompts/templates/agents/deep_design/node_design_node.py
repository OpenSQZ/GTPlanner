"""
节点设计节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/node_design_node.py
"""


class AgentsDeepDesignNodeDesignNodeTemplates:
    """节点设计节点提示词模板类"""
    
    @staticmethod
    def get_node_design_zh() -> str:
        """中文版本的节点设计提示词"""
        return """你是一个专业的pocketflow Node设计师，专门设计基于pocketflow框架的Node实现。

请基于以下信息设计详细的Node实现方案：

```
{node_info_text}
```

**Node信息：**
```
{nodes_markdown}
```
**Agent分析结果：**
{analysis_markdown}

**Flow设计：**
{flow_markdown}

**数据结构设计：**
{data_structure_json}

**用户需求：**
{user_requirements}

**项目规划：**
{short_planning}

**技术调研结果：**
{research_info}

**推荐工具：**
{tools_info}

请进行以下Node设计工作：


**重要：Node类型和方法名约定**
- **AsyncNode**: 使用异步方法名 prep_async、exec_async、post_async
- **同步Node**: 使用同步方法名 prep、exec、post

请根据Node类型选择正确的方法名，并严格按照以下Markdown格式输出Node设计结果：

# Node详细设计结果

## [Node名称]

### 基本信息
- **Node类型**: [AsyncNode 或 Node]
- **目的**: [Node目的]

### Prep阶段设计 (AsyncNode使用PrepAsync阶段设计)
- **描述**: [prep/prep_async阶段的详细描述]
- **从shared读取**: [从shared读取的数据字段，用逗号分隔]
- **验证逻辑**: [数据验证逻辑]
- **准备步骤**: [准备步骤，用分号分隔]

### Exec阶段设计 (AsyncNode使用ExecAsync阶段设计)
- **描述**: [exec/exec_async阶段的详细描述]
- **核心逻辑**: [核心处理逻辑描述]
- **处理步骤**: [处理步骤，用分号分隔]
- **错误处理**: [错误处理策略]

### Post阶段设计 (AsyncNode使用PostAsync阶段设计)
- **描述**: [post/post_async阶段的详细描述]
- **结果处理**: [结果处理逻辑]
- **更新shared**: [更新到shared的数据，用逗号分隔]
- **Action逻辑**: [Action决策逻辑]
- **可能Actions**: [可能返回的Action列表，用逗号分隔]

### 数据访问
- **读取字段**: [读取的shared字段，用逗号分隔]
- **写入字段**: [写入的shared字段，用逗号分隔]

### 重试配置
- **最大重试**: [最大重试次数]次
- **等待时间**: [等待时间]秒

设计要求：
1. **方法名约定**：
   - AsyncNode: 严格遵循prep_async/exec_async/post_async三阶段分离
   - 同步Node: 严格遵循prep/exec/post三阶段分离
2. exec/exec_async阶段不能直接访问shared
3. 明确的Action驱动逻辑
4. 考虑错误处理和重试
5. 确保与Flow中其他Node的协调

重要：请严格按照上述Markdown格式输出，直接输出完整的Markdown文档。"""

    
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
