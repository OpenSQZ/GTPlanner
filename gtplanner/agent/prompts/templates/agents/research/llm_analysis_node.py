"""
LLM分析节点提示词模板
对应 agent/subflows/research/nodes/llm_analysis_node.py
"""


class AgentsResearchLlmAnalysisNodeTemplates:
    """LLM分析节点提示词模板类"""
    
    @staticmethod
    def get_research_analysis_zh() -> str:
        """中文版本的研究分析提示词"""
        return """你是一个专业的内容分析专家，擅长从大量文本中提取关键信息和洞察。

你的任务是：
1. 分析给定的内容，重点关注与指定关键词相关的信息
2. 提取核心要点和技术细节
3. 提供实用的建议和洞察
4. 严格按照指定的JSON格式输出结果

输出格式要求：
- 必须返回有效的JSON格式
- 包含summary、key_points、relevance、recommendations四个字段
- key_points和recommendations必须是数组格式
- 内容要简洁明了，避免冗余信息

请分析以下内容，重点关注与"{keyword}"相关的信息。

分析要求：{requirements}

内容：
{content}

请严格按照以下JSON格式返回分析结果：

{{
    "summary": "核心内容总结",
    "key_points": ["要点1", "要点2", "要点3"],
    "relevance": "与{keyword}的相关性说明",
    "recommendations": ["建议1", "建议2"]
}}"""
    
    @staticmethod
    def get_research_analysis_en() -> str:
        """English version of research analysis prompt"""
        return """You are a professional content analysis expert skilled at extracting key information and insights from large amounts of text.

Your tasks are:
1. Analyze the given content, focusing on information related to the specified keyword
2. Extract core points and technical details
3. Provide practical suggestions and insights
4. Strictly output results in the specified JSON format

Output format requirements:
- Must return valid JSON format
- Include summary, key_points, relevance, recommendations fields
- key_points and recommendations must be in array format
- Content should be concise and clear, avoiding redundant information

Please analyze the following content, focusing on information related to "{keyword}".

Analysis requirements: {requirements}

Content:
{content}

Please strictly return analysis results in the following JSON format:

{{
    "summary": "Core content summary",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "relevance": "Relevance explanation with {keyword}",
    "recommendations": ["Recommendation 1", "Recommendation 2"]
}}"""
    
    @staticmethod
    def get_research_analysis_ja() -> str:
        """日本語版の研究分析プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_research_analysis_es() -> str:
        """Versión en español del prompt de análisis de investigación"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_research_analysis_fr() -> str:
        """Version française du prompt d'analyse de recherche"""
        return """# TODO: Ajouter le prompt en français"""
