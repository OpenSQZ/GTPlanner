"""
预制件推荐节点提示词模板
对应 agent/nodes/node_prefab_recommend.py
"""


class AgentsPrefabRecommendNodePrefabRecommendTemplates:
    """预制件推荐节点提示词模板类"""
    
    @staticmethod
    def get_prefab_recommendation_zh() -> str:
        """中文版本的预制件推荐提示词"""
        return """你是一个专业的预制件筛选专家，负责从候选预制件列表中筛选出最适合用户查询需求的预制件。

**重要说明：你的任务是筛选决策，不是排序。只返回你认为真正适合用户需求的预制件，如果候选预制件都不合适，可以返回空列表。**

用户查询: {query}

候选预制件列表:
{prefabs_info}

请仔细分析用户查询的意图，考虑以下因素：
1. 预制件功能与查询需求的**直接匹配度**
2. 预制件名称和描述是否**真正适合**解决用户问题
3. 预制件的标签是否与用户需求相关
4. 预制件描述中是否包含用户需要的**核心功能**

筛选标准：
- 只选择与用户查询**高度相关**的预制件
- 优先选择功能**直接匹配**的预制件
- 如果某个预制件与查询需求不匹配，**不要选择它**
- 最多返回{top_k}个预制件，但如果合适的预制件少于{top_k}个，只返回合适的

请返回JSON格式的结果：

{{
    "selected_prefabs": [
        {{
            "index": 预制件在原列表中的索引,
            "reason": "选择这个预制件的具体理由，说明它如何满足用户需求"
        }}
    ],
    "analysis": "整体分析说明，解释筛选逻辑"
}}

注意：
- 只返回真正合适的预制件，不要为了凑数而选择不相关的预制件
- 索引必须是有效的（0到{prefabs_count}）
- 按相关性从高到低排序
- 如果没有合适的预制件，selected_prefabs可以为空数组"""
    
    @staticmethod
    def get_prefab_recommendation_en() -> str:
        """English version of prefab recommendation prompt"""
        return """You are a professional prefab filtering expert responsible for selecting the most suitable prefabs from a candidate list based on user query requirements.

**Important Note: Your task is filtering decisions, not ranking. Only return prefabs you believe are truly suitable for user needs. If no candidate prefabs are appropriate, you can return an empty list.**

User Query: {query}

Candidate Prefabs List:
{prefabs_info}

Please carefully analyze the user query intent, considering the following factors:
1. **Direct match level** between prefab functionality and query requirements
2. Whether the prefab name and description are **truly suitable** for solving user problems
3. Whether prefab tags are relevant to user needs
4. Whether prefab descriptions contain **core functionalities** needed by users

Filtering Criteria:
- Only select prefabs **highly relevant** to user queries
- Prioritize prefabs with **direct functional matches**
- If a prefab doesn't match query requirements, **don't select it**
- Return at most {top_k} prefabs, but if suitable prefabs are fewer than {top_k}, only return suitable ones

Please return results in JSON format:

{{
    "selected_prefabs": [
        {{
            "index": "Prefab index in original list",
            "reason": "Specific reason for selecting this prefab, explaining how it meets user needs"
        }}
    ],
    "analysis": "Overall analysis explanation, explaining filtering logic"
}}

Notes:
- Only return truly suitable prefabs, don't select irrelevant prefabs just to fill numbers
- Index must be valid (0 to {prefabs_count})
- Sort by relevance from high to low
- If no suitable prefabs exist, selected_prefabs can be an empty array"""
    
    @staticmethod
    def get_prefab_recommendation_ja() -> str:
        """日本語版の Prefab 推薦プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_prefab_recommendation_es() -> str:
        """Versión en español del prompt de recomendación de prefabs"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_prefab_recommendation_fr() -> str:
        """Version française du prompt de recommandation de prefabs"""
        return """# TODO: Ajouter le prompt en français"""

