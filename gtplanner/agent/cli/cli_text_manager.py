"""
CLI多语言文本管理器
用于管理CLI界面的多语言文本显示
"""

from typing import Dict, Any


class CLITextManager:
    """CLI多语言文本管理器"""
    
    # 中文文本
    _texts_zh = {
        # 信号处理
        "interrupt_signal_graceful": "\n🛑 [yellow]接收到中断信号，正在优雅退出...[/yellow]",
        "interrupt_signal": "\n🛑 [yellow]接收到中断信号[/yellow]",
        "confirm_exit": "确定要退出吗？",
        "goodbye": "\n👋 [yellow]再见！[/yellow]",
        
        # 会话管理
        "create_new_session": "🆕 [green]创建新会话:[/green] {session_id}",
        "session_loaded": "📂 [green]已加载会话:[/green] {session_id}",
        "session_load_failed": "❌ [red]加载会话失败:[/red] {session_id}",
        "no_session_found": "❌ [red]未找到匹配的会话:[/red] {partial_id}",
        "specify_session_id": "❌ [red]请指定会话ID[/red]",
        
        # 错误信息
        "context_build_failed": "❌ [red]无法构建上下文[/red]",
        "cli_exception": "💥 [red]CLI异常:[/red] {error}",
        "cli_run_exception": "❌ [bold red]CLI运行异常:[/bold red] {error}",
        "streaming_cleanup_error": "⚠️ [yellow]清理流式会话时出错: {error}[/yellow]",
        "database_save_warning": "⚠️ [yellow]保存结果到数据库时出现问题[/yellow]",
        
        # 处理状态
        "processing_requirement": "🚀 [blue]处理需求:[/blue] {requirement}",
        "user_interrupt": "\n👋 用户中断，再见！",
        
        # 欢迎信息
        "welcome_title": "🚀 现代化GTPlanner CLI",
        "welcome_subtitle": "欢迎使用基于新流式响应架构的智能规划助手！",
        "new_features": "✨ 新特性",
        "usage_method": "🎯 使用方法",
        "config_options": "⚙️ 配置选项",
        "available_commands": "📝 可用命令",
        "streaming_enabled": "启用",
        "streaming_disabled": "禁用",
        "usage_description": "直接输入您的需求，我将通过现代化的流式响应为您提供智能规划服务。",
        
        # 帮助信息
        "help_title": "帮助信息",
        "command_help": "📖 命令帮助",
        "basic_commands": "基本命令",
        "session_management": "会话管理",
        "config_options_help": "配置选项",
        "usage_examples": "使用示例",
        
        # 命令描述
        "help_command": "显示此帮助信息",
        "quit_command": "退出程序",
        "sessions_command": "查看所有会话列表",
        "new_command": "创建新会话（可选标题）",
        "load_command": "加载指定会话（支持部分ID匹配）",
        "current_command": "显示当前会话信息",
        "streaming_command": "开启/关闭流式响应",
        "timestamps_command": "开启/关闭时间戳显示",
        "metadata_command": "开启/关闭元数据显示",
    }
    
    # 英文文本
    _texts_en = {
        # 信号处理
        "interrupt_signal_graceful": "\n🛑 [yellow]Interrupt signal received, gracefully exiting...[/yellow]",
        "interrupt_signal": "\n🛑 [yellow]Interrupt signal received[/yellow]",
        "confirm_exit": "Are you sure you want to exit?",
        "goodbye": "\n👋 [yellow]Goodbye![/yellow]",
        
        # 会话管理
        "create_new_session": "🆕 [green]New session created:[/green] {session_id}",
        "session_loaded": "📂 [green]Session loaded:[/green] {session_id}",
        "session_load_failed": "❌ [red]Failed to load session:[/red] {session_id}",
        "no_session_found": "❌ [red]No matching session found:[/red] {partial_id}",
        "specify_session_id": "❌ [red]Please specify session ID[/red]",
        
        # 错误信息
        "context_build_failed": "❌ [red]Failed to build context[/red]",
        "cli_exception": "💥 [red]CLI exception:[/red] {error}",
        "cli_run_exception": "❌ [bold red]CLI runtime exception:[/bold red] {error}",
        "streaming_cleanup_error": "⚠️ [yellow]Error cleaning up streaming session: {error}[/yellow]",
        "database_save_warning": "⚠️ [yellow]Issue saving results to database[/yellow]",
        
        # 处理状态
        "processing_requirement": "🚀 [blue]Processing requirement:[/blue] {requirement}",
        "user_interrupt": "\n👋 User interrupted, goodbye!",
        
        # 欢迎信息
        "welcome_title": "🚀 Modern GTPlanner CLI",
        "welcome_subtitle": "Welcome to the intelligent planning assistant based on new streaming response architecture!",
        "new_features": "✨ New Features",
        "usage_method": "🎯 Usage",
        "config_options": "⚙️ Configuration Options",
        "available_commands": "📝 Available Commands",
        "streaming_enabled": "Enabled",
        "streaming_disabled": "Disabled",
        "usage_description": "Simply enter your requirements, and I will provide intelligent planning services through modern streaming responses.",
        
        # 帮助信息
        "help_title": "Help Information",
        "command_help": "📖 Command Help",
        "basic_commands": "Basic Commands",
        "session_management": "Session Management",
        "config_options_help": "Configuration Options",
        "usage_examples": "Usage Examples",
        
        # 命令描述
        "help_command": "Show this help information",
        "quit_command": "Exit the program",
        "sessions_command": "View all session list",
        "new_command": "Create new session (optional title)",
        "load_command": "Load specified session (supports partial ID matching)",
        "current_command": "Show current session information",
        "streaming_command": "Enable/disable streaming response",
        "timestamps_command": "Enable/disable timestamp display",
        "metadata_command": "Enable/disable metadata display",
    }
    
    # 日文文本
    _texts_ja = {
        # 信号处理
        "interrupt_signal_graceful": "\n🛑 [yellow]割り込み信号を受信、正常に終了中...[/yellow]",
        "interrupt_signal": "\n🛑 [yellow]割り込み信号を受信[/yellow]",
        "confirm_exit": "終了してもよろしいですか？",
        "goodbye": "\n👋 [yellow]さようなら！[/yellow]",
        
        # 会話管理
        "create_new_session": "🆕 [green]新しいセッションを作成:[/green] {session_id}",
        "session_loaded": "📂 [green]セッションを読み込み:[/green] {session_id}",
        "session_load_failed": "❌ [red]セッションの読み込みに失敗:[/red] {session_id}",
        "no_session_found": "❌ [red]一致するセッションが見つかりません:[/red] {partial_id}",
        "specify_session_id": "❌ [red]セッションIDを指定してください[/red]",
        
        # エラー情報
        "context_build_failed": "❌ [red]コンテキストの構築に失敗[/red]",
        "cli_exception": "💥 [red]CLI例外:[/red] {error}",
        "cli_run_exception": "❌ [bold red]CLI実行時例外:[/bold red] {error}",
        "streaming_cleanup_error": "⚠️ [yellow]ストリーミングセッションのクリーンアップエラー: {error}[/yellow]",
        "database_save_warning": "⚠️ [yellow]データベースへの結果保存に問題があります[/yellow]",
        
        # 処理状態
        "processing_requirement": "🚀 [blue]要件を処理中:[/blue] {requirement}",
        "user_interrupt": "\n👋 ユーザーが中断しました、さようなら！",
        
        # ウェルカム情報
        "welcome_title": "🚀 モダンGTPlanner CLI",
        "welcome_subtitle": "新しいストリーミングレスポンスアーキテクチャに基づくインテリジェント計画アシスタントへようこそ！",
        "new_features": "✨ 新機能",
        "usage_method": "🎯 使用方法",
        "config_options": "⚙️ 設定オプション",
        "available_commands": "📝 利用可能なコマンド",
        "streaming_enabled": "有効",
        "streaming_disabled": "無効",
        "usage_description": "要件を直接入力してください。モダンなストリーミングレスポンスを通じてインテリジェントな計画サービスを提供します。",
        
        # ヘルプ情報
        "help_title": "ヘルプ情報",
        "command_help": "📖 コマンドヘルプ",
        "basic_commands": "基本コマンド",
        "session_management": "セッション管理",
        "config_options_help": "設定オプション",
        "usage_examples": "使用例",
        
        # コマンド説明
        "help_command": "このヘルプ情報を表示",
        "quit_command": "プログラムを終了",
        "sessions_command": "すべてのセッションリストを表示",
        "new_command": "新しいセッションを作成（オプションのタイトル）",
        "load_command": "指定されたセッションを読み込み（部分ID一致をサポート）",
        "current_command": "現在のセッション情報を表示",
        "streaming_command": "ストリーミングレスポンスを有効/無効",
        "timestamps_command": "タイムスタンプ表示を有効/無効",
        "metadata_command": "メタデータ表示を有効/無効",
    }
    
    def __init__(self, language: str = "zh"):
        """
        初始化CLI文本管理器
        
        Args:
            language: 语言代码 (zh/en/ja/es/fr)
        """
        self.language = language
        self._texts = {
            "zh": self._texts_zh,
            "en": self._texts_en,
            "ja": self._texts_ja,
            "es": self._get_texts_es(),
            "fr": self._get_texts_fr()
        }
    
    def get_text(self, key: str, **kwargs) -> str:
        """
        获取指定语言的文本
        
        Args:
            key: 文本键
            **kwargs: 格式化参数
            
        Returns:
            格式化后的文本
        """
        texts = self._texts.get(self.language, self._texts_zh)
        text = texts.get(key, self._texts_zh.get(key, f"[Missing text: {key}]"))
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text
    
    def _get_texts_es(self) -> Dict[str, str]:
        """获取西班牙文文本"""
        return {
            # 信号处理
            "interrupt_signal_graceful": "\n🛑 [yellow]Señal de interrupción recibida, saliendo correctamente...[/yellow]",
            "interrupt_signal": "\n🛑 [yellow]Señal de interrupción recibida[/yellow]",
            "confirm_exit": "¿Está seguro de que desea salir?",
            "goodbye": "\n👋 [yellow]¡Adiós![/yellow]",

            # 会话管理
            "create_new_session": "🆕 [green]Nueva sesión creada:[/green] {session_id}",
            "session_loaded": "📂 [green]Sesión cargada:[/green] {session_id}",
            "session_load_failed": "❌ [red]Error al cargar la sesión:[/red] {session_id}",
            "no_session_found": "❌ [red]No se encontró sesión coincidente:[/red] {partial_id}",
            "specify_session_id": "❌ [red]Por favor especifique el ID de sesión[/red]",

            # 错误信息
            "context_build_failed": "❌ [red]Error al construir el contexto[/red]",
            "cli_exception": "💥 [red]Excepción CLI:[/red] {error}",
            "cli_run_exception": "❌ [bold red]Excepción de ejecución CLI:[/bold red] {error}",
            "streaming_cleanup_error": "⚠️ [yellow]Error limpiando sesión de streaming: {error}[/yellow]",
            "database_save_warning": "⚠️ [yellow]Problema guardando resultados en la base de datos[/yellow]",

            # 处理状态
            "processing_requirement": "🚀 [blue]Procesando requisito:[/blue] {requirement}",
            "user_interrupt": "\n👋 Usuario interrumpido, ¡adiós!",

            # 欢迎信息
            "welcome_title": "🚀 GTPlanner CLI Moderno",
            "welcome_subtitle": "¡Bienvenido al asistente de planificación inteligente basado en nueva arquitectura de respuesta streaming!",
            "new_features": "✨ Nuevas Características",
            "usage_method": "🎯 Uso",
            "config_options": "⚙️ Opciones de Configuración",
            "available_commands": "📝 Comandos Disponibles",
            "streaming_enabled": "Habilitado",
            "streaming_disabled": "Deshabilitado",
            "usage_description": "Simplemente ingrese sus requisitos, y proporcionaré servicios de planificación inteligente a través de respuestas streaming modernas.",

            # 帮助信息
            "help_title": "Información de Ayuda",
            "command_help": "📖 Ayuda de Comandos",
            "basic_commands": "Comandos Básicos",
            "session_management": "Gestión de Sesiones",
            "config_options_help": "Opciones de Configuración",
            "usage_examples": "Ejemplos de Uso",

            # 命令描述
            "help_command": "Mostrar esta información de ayuda",
            "quit_command": "Salir del programa",
            "sessions_command": "Ver lista de todas las sesiones",
            "new_command": "Crear nueva sesión (título opcional)",
            "load_command": "Cargar sesión especificada (soporta coincidencia parcial de ID)",
            "current_command": "Mostrar información de sesión actual",
            "streaming_command": "Habilitar/deshabilitar respuesta streaming",
            "timestamps_command": "Habilitar/deshabilitar visualización de timestamps",
            "metadata_command": "Habilitar/deshabilitar visualización de metadatos",
        }

    def _get_texts_fr(self) -> Dict[str, str]:
        """获取法文文本"""
        return {
            # 信号处理
            "interrupt_signal_graceful": "\n🛑 [yellow]Signal d'interruption reçu, sortie en cours...[/yellow]",
            "interrupt_signal": "\n🛑 [yellow]Signal d'interruption reçu[/yellow]",
            "confirm_exit": "Êtes-vous sûr de vouloir quitter ?",
            "goodbye": "\n👋 [yellow]Au revoir ![/yellow]",

            # 会话管理
            "create_new_session": "🆕 [green]Nouvelle session créée:[/green] {session_id}",
            "session_loaded": "📂 [green]Session chargée:[/green] {session_id}",
            "session_load_failed": "❌ [red]Échec du chargement de la session:[/red] {session_id}",
            "no_session_found": "❌ [red]Aucune session correspondante trouvée:[/red] {partial_id}",
            "specify_session_id": "❌ [red]Veuillez spécifier l'ID de session[/red]",

            # 错误信息
            "context_build_failed": "❌ [red]Échec de la construction du contexte[/red]",
            "cli_exception": "💥 [red]Exception CLI:[/red] {error}",
            "cli_run_exception": "❌ [bold red]Exception d'exécution CLI:[/bold red] {error}",
            "streaming_cleanup_error": "⚠️ [yellow]Erreur lors du nettoyage de la session streaming: {error}[/yellow]",
            "database_save_warning": "⚠️ [yellow]Problème lors de la sauvegarde des résultats dans la base de données[/yellow]",

            # 处理状态
            "processing_requirement": "🚀 [blue]Traitement de l'exigence:[/blue] {requirement}",
            "user_interrupt": "\n👋 Utilisateur interrompu, au revoir !",

            # 欢迎信息
            "welcome_title": "🚀 GTPlanner CLI Moderne",
            "welcome_subtitle": "Bienvenue dans l'assistant de planification intelligent basé sur la nouvelle architecture de réponse streaming !",
            "new_features": "✨ Nouvelles Fonctionnalités",
            "usage_method": "🎯 Utilisation",
            "config_options": "⚙️ Options de Configuration",
            "available_commands": "📝 Commandes Disponibles",
            "streaming_enabled": "Activé",
            "streaming_disabled": "Désactivé",
            "usage_description": "Entrez simplement vos exigences, et je fournirai des services de planification intelligente via des réponses streaming modernes.",

            # 帮助信息
            "help_title": "Informations d'Aide",
            "command_help": "📖 Aide des Commandes",
            "basic_commands": "Commandes de Base",
            "session_management": "Gestion des Sessions",
            "config_options_help": "Options de Configuration",
            "usage_examples": "Exemples d'Utilisation",

            # 命令描述
            "help_command": "Afficher ces informations d'aide",
            "quit_command": "Quitter le programme",
            "sessions_command": "Voir la liste de toutes les sessions",
            "new_command": "Créer une nouvelle session (titre optionnel)",
            "load_command": "Charger la session spécifiée (supporte la correspondance partielle d'ID)",
            "current_command": "Afficher les informations de la session actuelle",
            "streaming_command": "Activer/désactiver la réponse streaming",
            "timestamps_command": "Activer/désactiver l'affichage des timestamps",
            "metadata_command": "Activer/désactiver l'affichage des métadonnées",
        }

    def set_language(self, language: str):
        """设置语言"""
        if language in self._texts:
            self.language = language
