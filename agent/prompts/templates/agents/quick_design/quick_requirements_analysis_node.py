"""
快速需求分析节点提示词模板
对应 agent/subflows/quick_design/nodes/quick_requirements_analysis_node.py
"""


class AgentsQuickDesignQuickRequirementsAnalysisNodeTemplates:
    """快速需求分析节点提示词模板类"""
    
    @staticmethod
    def get_quick_requirements_analysis_zh() -> str:
        """中文版本的快速需求分析提示词"""
        return """你是一位资深的软件架构师和技术评审专家。你的任务是基于用户提供的【用户需求】、【项目规划】、【推荐工具】和【技术调研结果】，并结合常见的【设计原则与思维模型】，分析其中可能存在的不足、风险、遗漏点，并给出具体的优化思路或建议。

**请特别关注【项目规划】所揭示的系统交互、数据流转和关键步骤，并结合【推荐工具】和【技术调研结果】进行综合分析。**


**用户需求：**
{user_requirements}

**项目规划：**
{short_planning}

**推荐工具：**
{tools_info}

**技术调研结果：**
{research_summary}


【设计原则与思维模型】参考（你也可以根据你的知识库补充）：
* **KISS (Keep It Simple, Stupid):** 是否过于复杂？流程步骤是否可以简化？
* **DRY (Don't Repeat Yourself):** 是否有重复的设计或逻辑？流程中是否有重复或冗余的环节？
* **SOLID 原则 (针对面向对象设计):** 是否符合单一职责、开闭原则等？（如果适用）
* **高内聚、低耦合:** 模块划分是否合理？依赖关系是否清晰？流程中的各个环节是否能映射到合理的模块？
* **可扩展性 (Scalability):** 未来如何支持更多用户或功能？流程设计是否考虑到未来的扩展需求（如增加新步骤、分支流程）？
* **可维护性 (Maintainability):** 设计是否清晰易懂，方便后续修改？流程描述是否清晰，易于理解和维护？
* **安全性 (Security):** 是否考虑了常见的安全风险（如SQL注入、XSS、权限控制等）？流程中涉及数据传递和操作的环节是否有安全隐患？
* **性能 (Performance):** 关键路径的性能预期如何？是否有潜在瓶颈？流程中的关键步骤或高频操作是否有效率问题？
* **可用性 (Usability/Availability):** 系统是否易用？容错和恢复机制如何？流程设计是否符合用户习惯，异常处理是否周全？
* **可测试性 (Testability):** 设计是否方便进行单元测试、集成测试？流程的各个节点和分支是否易于测试？
* **文档完整性与清晰度:** （如果输入是文档片段）信息是否完整，表达是否清晰？是否有歧义？
* **流程的完整性与合理性:** 【项目规划】本身是否覆盖了所有必要场景？步骤是否逻辑连贯？是否存在遗漏的关键环节或不合理的跳转？
* **工具选型的合理性:** 【推荐工具】是否适合项目需求？是否存在更好的替代方案？工具之间的兼容性如何？
* **技术调研的充分性:** 【技术调研结果】是否覆盖了关键技术点？是否有遗漏的风险点或技术难点？

你的输出应该是一个结构化的列表，包含：
1. **[识别到的不足/风险点]:** 清晰指出具体问题。**（请结合项目规划、推荐工具和技术调研进行分析）**
2. **[对应的优化思路/建议]:** 针对每个问题给出具体的、可操作的改进建议。**（请结合技术选型和最佳实践进行阐述）**
3. **[可选：需要用户澄清的问题]:** 如果信息不足以做出判断（例如技术选型不明确，关键决策点不清楚等），可以向用户提出针对性的问题。

请确保你的分析具有建设性，并能帮助用户完善他们的设计。"""
    
    @staticmethod
    def get_quick_requirements_analysis_en() -> str:
        """English version of quick requirements analysis prompt"""
        return """You are a professional requirements analyst specializing in analyzing user requirements and extracting key information.

Please conduct requirements analysis based on the following information:

**User Requirements:**
{user_requirements}

**Project Planning:**
{short_planning}

**Recommended Tools:**
{tools_info}

**Technical Research Results:**
{research_summary}

Please analyze and output the following content:

1. **Core Requirements Identification**:
   - Clarify user's core objectives and expectations
   - Identify key functional requirements
   - Analyze non-functional requirements (performance, security, usability, etc.)

2. **Technical Feasibility Assessment**:
   - Based on recommended tools and research results, assess technical implementation feasibility
   - Identify potential technical challenges and risks
   - Propose technology selection recommendations

3. **Requirements Priority Ranking**:
   - Categorize requirements by importance and urgency
   - Identify core functions for MVP (Minimum Viable Product)
   - Plan feature iteration sequence

4. **Constraint Analysis**:
   - Identify project constraints (time, resources, technology, etc.)
   - Analyze external dependencies and integration requirements
   - Assess risk factors

Please output analysis results in a structured format for subsequent design work."""
    
    @staticmethod
    def get_quick_requirements_analysis_ja() -> str:
        """日本語版の高速要件分析プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_quick_requirements_analysis_es() -> str:
        """Versión en español del prompt de análisis rápido de requisitos"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_quick_requirements_analysis_fr() -> str:
        """Version française du prompt d'analyse rapide des exigences"""
        return """# TODO: Ajouter le prompt en français"""
