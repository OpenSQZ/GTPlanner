"""
通用文本片段模板
包含各种动态添加的文本片段，如分隔符、标题、提示语等
"""


class CommonTextFragmentsTemplates:
    """通用文本片段模板类"""
    
    # ==================== 中文版本 ====================
    @staticmethod
    def get_previous_planning_header_zh() -> str:
        """中文版本的先前规划标题"""
        return "\n---参考的先前规划---"
    
    @staticmethod
    def get_improvement_points_header_zh() -> str:
        """中文版本的改进点标题"""
        return "\n---需要重点改进的方面---"
    
    @staticmethod
    def get_improvement_instruction_zh() -> str:
        """中文版本的改进指令"""
        return "\n请综合以上所有信息，特别是改进点，生成一个全新的、更优化的流程。"
    
    @staticmethod
    def get_tools_header_zh() -> str:
        """中文版本的工具清单标题"""
        return "\n---推荐工具清单---"
    
    @staticmethod
    def get_research_header_zh() -> str:
        """中文版本的技术调研标题"""
        return "\n---技术调研结果---"
    
    @staticmethod
    def get_no_tools_placeholder_zh() -> str:
        """中文版本的无工具占位符"""
        return "暂无推荐工具"
    
    @staticmethod
    def get_no_research_placeholder_zh() -> str:
        """中文版本的无调研结果占位符"""
        return "暂无技术调研结果"
    
    @staticmethod
    def get_bullet_point_zh() -> str:
        """中文版本的列表项前缀"""
        return "- {content}"

    @staticmethod
    def get_unknown_tool_zh() -> str:
        """中文版本的未知工具"""
        return "未知工具"

    @staticmethod
    def get_tool_format_zh() -> str:
        """中文版本的工具格式"""
        return "- {tool_name} ({tool_type}): {tool_summary}"

    @staticmethod
    def get_research_summary_prefix_zh() -> str:
        """中文版本的研究摘要前缀"""
        return "技术调研摘要："

    @staticmethod
    def get_key_findings_prefix_zh() -> str:
        """中文版本的关键发现前缀"""
        return "关键技术发现："

    @staticmethod
    def get_no_requirements_placeholder_zh() -> str:
        """中文版本的无需求占位符"""
        return "未提供用户需求"

    @staticmethod
    def get_no_planning_placeholder_zh() -> str:
        """中文版本的无规划占位符"""
        return "未提供项目规划"

    @staticmethod
    def get_tool_based_planning_placeholder_zh() -> str:
        """中文版本的基于工具的规划占位符"""
        return "基于推荐的技术工具优化项目规划"

    @staticmethod
    def get_default_project_title_zh() -> str:
        """中文版本的默认项目标题"""
        return "AI Agent项目"
    
    # ==================== 英文版本 ====================
    @staticmethod
    def get_previous_planning_header_en() -> str:
        """English version of previous planning header"""
        return "\n---Reference Previous Planning---"
    
    @staticmethod
    def get_improvement_points_header_en() -> str:
        """English version of improvement points header"""
        return "\n---Key Areas for Improvement---"
    
    @staticmethod
    def get_improvement_instruction_en() -> str:
        """English version of improvement instruction"""
        return "\nPlease integrate all the above information, especially the improvement points, to generate a new and optimized workflow."
    
    @staticmethod
    def get_tools_header_en() -> str:
        """English version of tools header"""
        return "\n---Recommended Tools List---"
    
    @staticmethod
    def get_research_header_en() -> str:
        """English version of research header"""
        return "\n---Technical Research Results---"
    
    @staticmethod
    def get_no_tools_placeholder_en() -> str:
        """English version of no tools placeholder"""
        return "No recommended tools available"
    
    @staticmethod
    def get_no_research_placeholder_en() -> str:
        """English version of no research placeholder"""
        return "No technical research results available"
    
    @staticmethod
    def get_bullet_point_en() -> str:
        """English version of bullet point prefix"""
        return "- {content}"

    @staticmethod
    def get_unknown_tool_en() -> str:
        """English version of unknown tool"""
        return "Unknown tool"

    @staticmethod
    def get_tool_format_en() -> str:
        """English version of tool format"""
        return "- {tool_name} ({tool_type}): {tool_summary}"

    @staticmethod
    def get_research_summary_prefix_en() -> str:
        """English version of research summary prefix"""
        return "Technical Research Summary:"

    @staticmethod
    def get_key_findings_prefix_en() -> str:
        """English version of key findings prefix"""
        return "Key Technical Findings:"

    @staticmethod
    def get_no_requirements_placeholder_en() -> str:
        """English version of no requirements placeholder"""
        return "No user requirements provided"

    @staticmethod
    def get_no_planning_placeholder_en() -> str:
        """English version of no planning placeholder"""
        return "No project planning provided"

    @staticmethod
    def get_tool_based_planning_placeholder_en() -> str:
        """English version of tool-based planning placeholder"""
        return "Optimize project planning based on recommended technical tools"

    @staticmethod
    def get_default_project_title_en() -> str:
        """English version of default project title"""
        return "AI Agent Project"
    
    # ==================== 日文版本 ====================
    @staticmethod
    def get_previous_planning_header_ja() -> str:
        """日本語版の以前の計画ヘッダー"""
        return "\n---参考となる以前の計画---"
    
    @staticmethod
    def get_improvement_points_header_ja() -> str:
        """日本語版の改善点ヘッダー"""
        return "\n---重点的に改善すべき点---"
    
    @staticmethod
    def get_improvement_instruction_ja() -> str:
        """日本語版の改善指示"""
        return "\n上記の情報、特に改善点を総合して、新しく最適化されたフローを生成してください。"
    
    @staticmethod
    def get_tools_header_ja() -> str:
        """日本語版のツールヘッダー"""
        return "\n---推奨ツールリスト---"
    
    @staticmethod
    def get_research_header_ja() -> str:
        """日本語版の研究ヘッダー"""
        return "\n---技術調査結果---"
    
    @staticmethod
    def get_no_tools_placeholder_ja() -> str:
        """日本語版のツールなしプレースホルダー"""
        return "推奨ツールはありません"
    
    @staticmethod
    def get_no_research_placeholder_ja() -> str:
        """日本語版の調査結果なしプレースホルダー"""
        return "技術調査結果はありません"
    
    @staticmethod
    def get_bullet_point_ja() -> str:
        """日本語版の箇条書きプレフィックス"""
        return "- {content}"

    @staticmethod
    def get_unknown_tool_ja() -> str:
        """日本語版の不明なツール"""
        return "不明なツール"

    @staticmethod
    def get_tool_format_ja() -> str:
        """日本語版のツール形式"""
        return "- {tool_name} ({tool_type}): {tool_summary}"

    @staticmethod
    def get_research_summary_prefix_ja() -> str:
        """日本語版の研究要約プレフィックス"""
        return "技術調査要約："

    @staticmethod
    def get_key_findings_prefix_ja() -> str:
        """日本語版の主要発見プレフィックス"""
        return "主要な技術的発見："

    @staticmethod
    def get_no_requirements_placeholder_ja() -> str:
        """日本語版の要件なしプレースホルダー"""
        return "ユーザー要件が提供されていません"

    @staticmethod
    def get_no_planning_placeholder_ja() -> str:
        """日本語版の計画なしプレースホルダー"""
        return "プロジェクト計画が提供されていません"

    @staticmethod
    def get_tool_based_planning_placeholder_ja() -> str:
        """日本語版のツールベース計画プレースホルダー"""
        return "推奨技術ツールに基づいてプロジェクト計画を最適化"

    @staticmethod
    def get_default_project_title_ja() -> str:
        """日本語版のデフォルトプロジェクトタイトル"""
        return "AIエージェントプロジェクト"
    
    # ==================== 西班牙文版本 ====================
    @staticmethod
    def get_previous_planning_header_es() -> str:
        """Versión en español del encabezado de planificación previa"""
        return "\n---Planificación Previa de Referencia---"
    
    @staticmethod
    def get_improvement_points_header_es() -> str:
        """Versión en español del encabezado de puntos de mejora"""
        return "\n---Áreas Clave para Mejora---"
    
    @staticmethod
    def get_improvement_instruction_es() -> str:
        """Versión en español de la instrucción de mejora"""
        return "\nPor favor integre toda la información anterior, especialmente los puntos de mejora, para generar un flujo de trabajo nuevo y optimizado."

    @staticmethod
    def get_tools_header_es() -> str:
        """Versión en español del encabezado de herramientas"""
        return "\n---Lista de Herramientas Recomendadas---"

    @staticmethod
    def get_research_header_es() -> str:
        """Versión en español del encabezado de investigación"""
        return "\n---Resultados de Investigación Técnica---"

    @staticmethod
    def get_no_tools_placeholder_es() -> str:
        """Versión en español del marcador de posición sin herramientas"""
        return "No hay herramientas recomendadas disponibles"

    @staticmethod
    def get_no_research_placeholder_es() -> str:
        """Versión en español del marcador de posición sin investigación"""
        return "No hay resultados de investigación técnica disponibles"

    @staticmethod
    def get_bullet_point_es() -> str:
        """Versión en español del prefijo de viñeta"""
        return "- {content}"

    @staticmethod
    def get_unknown_tool_es() -> str:
        """Versión en español de herramienta desconocida"""
        return "Herramienta desconocida"

    @staticmethod
    def get_tool_format_es() -> str:
        """Versión en español del formato de herramienta"""
        return "- {tool_name} ({tool_type}): {tool_summary}"

    @staticmethod
    def get_research_summary_prefix_es() -> str:
        """Versión en español del prefijo de resumen de investigación"""
        return "Resumen de Investigación Técnica:"

    @staticmethod
    def get_key_findings_prefix_es() -> str:
        """Versión en español del prefijo de hallazgos clave"""
        return "Hallazgos Técnicos Clave:"

    @staticmethod
    def get_no_requirements_placeholder_es() -> str:
        """Versión en español del marcador de posición sin requisitos"""
        return "No se proporcionaron requisitos de usuario"

    @staticmethod
    def get_no_planning_placeholder_es() -> str:
        """Versión en español del marcador de posición sin planificación"""
        return "No se proporcionó planificación del proyecto"

    @staticmethod
    def get_tool_based_planning_placeholder_es() -> str:
        """Versión en español del marcador de posición de planificación basada en herramientas"""
        return "Optimizar la planificación del proyecto basándose en herramientas técnicas recomendadas"

    @staticmethod
    def get_default_project_title_es() -> str:
        """Versión en español del título de proyecto por defecto"""
        return "Proyecto de Agente IA"

    @staticmethod
    def get_no_requirements_placeholder_es() -> str:
        """Versión en español del marcador de posición sin requisitos"""
        return "No se proporcionaron requisitos de usuario"

    @staticmethod
    def get_no_planning_placeholder_es() -> str:
        """Versión en español del marcador de posición sin planificación"""
        return "No se proporcionó planificación del proyecto"
    
    # ==================== 法文版本 ====================
    @staticmethod
    def get_previous_planning_header_fr() -> str:
        """Version française de l'en-tête de planification précédente"""
        return "\n---Planification Précédente de Référence---"
    
    @staticmethod
    def get_improvement_points_header_fr() -> str:
        """Version française de l'en-tête des points d'amélioration"""
        return "\n---Domaines Clés d'Amélioration---"
    
    @staticmethod
    def get_improvement_instruction_fr() -> str:
        """Version française de l'instruction d'amélioration"""
        return "\nVeuillez intégrer toutes les informations ci-dessus, en particulier les points d'amélioration, pour générer un flux de travail nouveau et optimisé."

    @staticmethod
    def get_tools_header_fr() -> str:
        """Version française de l'en-tête des outils"""
        return "\n---Liste des Outils Recommandés---"

    @staticmethod
    def get_research_header_fr() -> str:
        """Version française de l'en-tête de recherche"""
        return "\n---Résultats de Recherche Technique---"

    @staticmethod
    def get_no_tools_placeholder_fr() -> str:
        """Version française du placeholder sans outils"""
        return "Aucun outil recommandé disponible"

    @staticmethod
    def get_no_research_placeholder_fr() -> str:
        """Version française du placeholder sans recherche"""
        return "Aucun résultat de recherche technique disponible"

    @staticmethod
    def get_bullet_point_fr() -> str:
        """Version française du préfixe de puce"""
        return "- {content}"

    @staticmethod
    def get_unknown_tool_fr() -> str:
        """Version française d'outil inconnu"""
        return "Outil inconnu"

    @staticmethod
    def get_tool_format_fr() -> str:
        """Version française du format d'outil"""
        return "- {tool_name} ({tool_type}): {tool_summary}"

    @staticmethod
    def get_research_summary_prefix_fr() -> str:
        """Version française du préfixe de résumé de recherche"""
        return "Résumé de la Recherche Technique:"

    @staticmethod
    def get_key_findings_prefix_fr() -> str:
        """Version française du préfixe des découvertes clés"""
        return "Principales Découvertes Techniques:"

    @staticmethod
    def get_no_requirements_placeholder_fr() -> str:
        """Version française du placeholder sans exigences"""
        return "Aucune exigence utilisateur fournie"

    @staticmethod
    def get_no_planning_placeholder_fr() -> str:
        """Version française du placeholder sans planification"""
        return "Aucune planification de projet fournie"

    @staticmethod
    def get_tool_based_planning_placeholder_fr() -> str:
        """Version française du placeholder de planification basée sur les outils"""
        return "Optimiser la planification du projet basée sur les outils techniques recommandés"

    @staticmethod
    def get_default_project_title_fr() -> str:
        """Version française du titre de projet par défaut"""
        return "Projet d'Agent IA"
