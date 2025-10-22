"""
结果组装节点提示词模板
对应 agent/subflows/research/nodes/result_assembly_node.py
"""


class AgentsResearchResultAssemblyNodeTemplates:
    """结果组装节点提示词模板类"""
    
    @staticmethod
    def get_research_summary_zh() -> str:
        """中文版本的研究总结提示词"""
        return """你是一个专业的研究总结专家，负责将多个研究分析结果整合成一个综合性的研究报告。

请基于以下研究分析结果，生成一个综合性的研究总结：

{analysis_results}

输出要求：
1. **研究总结**：整合所有分析结果的核心发现
2. **关键技术点**：列出最重要的技术要点和发现
3. **实施建议**：基于研究结果提供具体的实施建议
4. **风险评估**：指出潜在的技术风险和挑战
5. **后续研究方向**：建议进一步研究的方向

请以清晰的结构化格式输出，便于理解和使用。"""
    
    @staticmethod
    def get_research_summary_en() -> str:
        """English version of research summary prompt"""
        return """You are a professional research summary expert responsible for integrating multiple research analysis results into a comprehensive research report.

Please generate a comprehensive research summary based on the following research analysis results:

{analysis_results}

Output requirements:
1. **Research Summary**: Integrate core findings from all analysis results
2. **Key Technical Points**: List the most important technical points and discoveries
3. **Implementation Recommendations**: Provide specific implementation suggestions based on research results
4. **Risk Assessment**: Point out potential technical risks and challenges
5. **Future Research Directions**: Suggest directions for further research

Please output in a clear structured format for easy understanding and use."""
    
    @staticmethod
    def get_research_summary_ja() -> str:
        """日本語版の研究総括プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_research_summary_es() -> str:
        """Versión en español del prompt de resumen de investigación"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_research_summary_fr() -> str:
        """Version française du prompt de résumé de recherche"""
        return """# TODO: Ajouter le prompt en français"""
