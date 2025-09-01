#!/usr/bin/env python3
"""
现代化GTPlanner CLI

基于新的流式响应架构的CLI实现：
1. 集成StreamingSession和CLIStreamHandler
2. 使用StatelessGTPlanner而不是旧的ReActOrchestratorFlow
3. 支持类型安全的流式响应（StreamEventType/StreamCallbackType）
4. 保持会话管理和配置功能
5. 优雅的中断处理和资源清理

使用方式:
    python cli/modern_gtplanner_cli.py                    # 启动交互式CLI
    python cli/modern_gtplanner_cli.py "设计用户管理系统"   # 直接处理需求
    python cli/modern_gtplanner_cli.py --load <session_id> # 加载指定会话
"""

import sys
import asyncio
import argparse
import signal
from typing import Optional, Dict, Any, List
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.align import Align

# 导入新的流式响应架构
from agent.stateless_planner import StatelessGTPlanner
from agent.context_types import AgentContext, Message, MessageRole
from agent.streaming import StreamingSession, CLIStreamHandler, streaming_manager

# 导入新的SQLite会话管理
from agent.persistence.sqlite_session_manager import SQLiteSessionManager

# 导入CLI多语言文本管理器
from agent.cli.cli_text_manager import CLITextManager


class ModernGTPlannerCLI:
    """基于新流式响应架构的现代化GTPlanner CLI"""

    def __init__(self,
                 enable_streaming: bool = True,
                 show_timestamps: bool = False,
                 show_metadata: bool = False,
                 verbose: bool = False,
                 language: str = "zh"):
        """
        初始化现代化CLI

        Args:
            enable_streaming: 是否启用流式响应
            show_timestamps: 是否显示时间戳
            show_metadata: 是否显示元数据
            verbose: 是否显示详细信息
            language: 界面语言 (zh/en/ja/es/fr)，默认为中文
        """
        self.console = Console()
        self.enable_streaming = enable_streaming
        self.show_timestamps = show_timestamps
        self.show_metadata = show_metadata
        self.verbose = verbose
        self.language = language
        self.running = True

        # 初始化CLI文本管理器
        self.text_manager = CLITextManager(language)

        # ASCII艺术字内容
        self.ascii_art = [
            " _____  _____ ______  _                                  ",
            "|  __ \\|_   _|| ___ \\| |                                 ",
            "| |  \\/  | |  | |_/ /| |  __ _  _ __   _ __    ___  _ __ ",
            "| | __   | |  |  __/ | | / _` || '_ \\ | '_ \\  / _ \\| '__|",
            "| |_\\ \\  | |  | |    | || (_| || | | || | | ||  __/| |   ",
            " \\____/  \\_/  \\_|    |_| \\__,_||_| |_||_| |_| \\___||_|   ",
            "                                                         ",
            "                                                         "
        ]
        
        # 使用新的StatelessGTPlanner
        self.planner = StatelessGTPlanner()

        # 使用新的SQLite会话管理器
        self.session_manager = SQLiteSessionManager()
        
        # 流式响应组件
        self.current_streaming_session: Optional[StreamingSession] = None
        self.cli_handler: Optional[CLIStreamHandler] = None
        
        # 设置信号处理
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器，优雅处理中断"""
        def signal_handler(signum, frame):
            self.console.print(self.text_manager.get_text("interrupt_signal_graceful"))
            self.running = False
            # 触发异步清理
            if self.current_streaming_session:
                asyncio.create_task(self._cleanup_streaming_session())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def show_ascii_logo(self):
        """显示ASCII艺术字logo，使用渐变色"""
        # 创建渐变色的ASCII艺术字
        gradient_text = Text()

        # RGB(106, 137, 244) 渐变色
        start_color = (106, 137, 244)  # 蓝色
        end_color = (180, 190, 254)    # 浅蓝色

        total_lines = len(self.ascii_art)

        for i, line in enumerate(self.ascii_art):
            # 计算当前行的颜色（渐变）
            ratio = i / max(1, total_lines - 1)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)

            # 添加带颜色的行
            gradient_text.append(line + "\n", style=f"rgb({r},{g},{b})")

        # 居中显示
        self.console.print(Align.center(gradient_text))
        self.console.print()  # 添加空行
    
    async def _cleanup_streaming_session(self):
        """清理流式会话资源"""
        if self.current_streaming_session:
            try:
                await self.current_streaming_session.stop()
                self.current_streaming_session = None
                self.cli_handler = None
            except Exception as e:
                self.console.print(self.text_manager.get_text("streaming_cleanup_error", error=e))
    
    def _create_streaming_session(self, session_id: str) -> StreamingSession:
        """创建流式会话和处理器"""
        # 创建流式会话
        streaming_session = streaming_manager.create_session(session_id)
        
        # 创建CLI处理器
        cli_handler = CLIStreamHandler(
            show_timestamps=self.show_timestamps,
            show_metadata=self.show_metadata
        )
        
        # 添加处理器到会话
        streaming_session.add_handler(cli_handler)
        
        return streaming_session
    
    def _build_agent_context(self) -> Optional[AgentContext]:
        """构建AgentContext（使用SQLiteSessionManager）"""
        # 直接使用SQLiteSessionManager的build_agent_context方法
        return self.session_manager.build_agent_context()
    
    def show_welcome(self):
        """显示欢迎信息"""
        welcome_text = self._build_welcome_text()

        self.console.print(Panel(
            Markdown(welcome_text),
            title=self.text_manager.get_text("welcome_title"),
            border_style="blue"
        ))

    def _build_welcome_text(self) -> str:
        """构建多语言欢迎文本"""
        streaming_status = self.text_manager.get_text("streaming_enabled" if self.enable_streaming else "streaming_disabled")
        timestamps_status = self.text_manager.get_text("streaming_enabled" if self.show_timestamps else "streaming_disabled")
        metadata_status = self.text_manager.get_text("streaming_enabled" if self.show_metadata else "streaming_disabled")

        if self.language == "zh":
            return f"""
# {self.text_manager.get_text("welcome_title")}

{self.text_manager.get_text("welcome_subtitle")}

## {self.text_manager.get_text("new_features")}
- 🌊 **真实流式响应**: 基于StreamEventType/StreamCallbackType的类型安全架构
- 🎯 **无状态设计**: 使用StatelessGTPlanner，支持高并发和水平扩展
- 🔧 **智能工具调用**: 实时显示工具执行状态和进度
- 💬 **优雅交互**: Rich库美化显示，支持中断处理
- 📊 **会话管理**: 完整的会话创建、加载、切换功能

## {self.text_manager.get_text("usage_method")}
{self.text_manager.get_text("usage_description")}

## {self.text_manager.get_text("config_options")}
- 流式响应: {streaming_status}
- 时间戳显示: {timestamps_status}
- 元数据显示: {metadata_status}

## {self.text_manager.get_text("available_commands")}
- `/help` - {self.text_manager.get_text("help_command")}
- `/sessions` - {self.text_manager.get_text("sessions_command")}
- `/new` - {self.text_manager.get_text("new_command")}
- `/load <session_id>` - {self.text_manager.get_text("load_command")}
- `/config` - 配置选项
- `/quit` - {self.text_manager.get_text("quit_command")}
            """
        elif self.language == "en":
            return f"""
# {self.text_manager.get_text("welcome_title")}

{self.text_manager.get_text("welcome_subtitle")}

## {self.text_manager.get_text("new_features")}
- 🌊 **Real Streaming Response**: Type-safe architecture based on StreamEventType/StreamCallbackType
- 🎯 **Stateless Design**: Using StatelessGTPlanner, supports high concurrency and horizontal scaling
- 🔧 **Smart Tool Calls**: Real-time display of tool execution status and progress
- 💬 **Elegant Interaction**: Rich library beautified display with interrupt handling support
- 📊 **Session Management**: Complete session creation, loading, and switching functionality

## {self.text_manager.get_text("usage_method")}
{self.text_manager.get_text("usage_description")}

## {self.text_manager.get_text("config_options")}
- Streaming Response: {streaming_status}
- Timestamp Display: {timestamps_status}
- Metadata Display: {metadata_status}

## {self.text_manager.get_text("available_commands")}
- `/help` - {self.text_manager.get_text("help_command")}
- `/sessions` - {self.text_manager.get_text("sessions_command")}
- `/new` - {self.text_manager.get_text("new_command")}
- `/load <session_id>` - {self.text_manager.get_text("load_command")}
- `/config` - Configuration options
- `/quit` - {self.text_manager.get_text("quit_command")}
            """
        else:
            # 对于其他语言，使用简化版本
            return f"""
# {self.text_manager.get_text("welcome_title")}

{self.text_manager.get_text("welcome_subtitle")}

## {self.text_manager.get_text("usage_method")}
{self.text_manager.get_text("usage_description")}

## {self.text_manager.get_text("config_options")}
- Streaming: {streaming_status}
- Timestamps: {timestamps_status}
- Metadata: {metadata_status}

## {self.text_manager.get_text("available_commands")}
- `/help` - {self.text_manager.get_text("help_command")}
- `/sessions` - {self.text_manager.get_text("sessions_command")}
- `/new` - {self.text_manager.get_text("new_command")}
- `/load <session_id>` - {self.text_manager.get_text("load_command")}
- `/quit` - {self.text_manager.get_text("quit_command")}
            """
    
    def show_help(self):
        """显示帮助信息"""
        help_text = self._build_help_text()

        self.console.print(Panel(
            Markdown(help_text),
            title=self.text_manager.get_text("help_title"),
            border_style="green"
        ))

    def _build_help_text(self) -> str:
        """构建多语言帮助文本"""
        if self.language == "zh":
            return f"""
## {self.text_manager.get_text("command_help")}

### {self.text_manager.get_text("basic_commands")}
- `/help` - {self.text_manager.get_text("help_command")}
- `/quit` - {self.text_manager.get_text("quit_command")}

### {self.text_manager.get_text("session_management")}
- `/sessions` - {self.text_manager.get_text("sessions_command")}
- `/new [title]` - {self.text_manager.get_text("new_command")}
- `/load <session_id>` - {self.text_manager.get_text("load_command")}
- `/current` - {self.text_manager.get_text("current_command")}

### {self.text_manager.get_text("config_options_help")}
- `/config` - 显示当前配置
- `/streaming on|off` - {self.text_manager.get_text("streaming_command")}
- `/timestamps on|off` - {self.text_manager.get_text("timestamps_command")}
- `/metadata on|off` - {self.text_manager.get_text("metadata_command")}

### {self.text_manager.get_text("usage_examples")}
```
我想做一个在线教育平台
/new 教育平台项目
/load 0a73b715    # 完整ID
/load 0a73        # 部分ID匹配
/streaming off
```
            """
        elif self.language == "en":
            return f"""
## {self.text_manager.get_text("command_help")}

### {self.text_manager.get_text("basic_commands")}
- `/help` - {self.text_manager.get_text("help_command")}
- `/quit` - {self.text_manager.get_text("quit_command")}

### {self.text_manager.get_text("session_management")}
- `/sessions` - {self.text_manager.get_text("sessions_command")}
- `/new [title]` - {self.text_manager.get_text("new_command")}
- `/load <session_id>` - {self.text_manager.get_text("load_command")}
- `/current` - {self.text_manager.get_text("current_command")}

### {self.text_manager.get_text("config_options_help")}
- `/config` - Show current configuration
- `/streaming on|off` - {self.text_manager.get_text("streaming_command")}
- `/timestamps on|off` - {self.text_manager.get_text("timestamps_command")}
- `/metadata on|off` - {self.text_manager.get_text("metadata_command")}

### {self.text_manager.get_text("usage_examples")}
```
I want to build an online education platform
/new Education Platform Project
/load 0a73b715    # Full ID
/load 0a73        # Partial ID matching
/streaming off
```
            """
        else:
            # 对于其他语言，使用简化版本
            return f"""
## {self.text_manager.get_text("command_help")}

### {self.text_manager.get_text("basic_commands")}
- `/help` - {self.text_manager.get_text("help_command")}
- `/quit` - {self.text_manager.get_text("quit_command")}

### {self.text_manager.get_text("session_management")}
- `/sessions` - {self.text_manager.get_text("sessions_command")}
- `/new [title]` - {self.text_manager.get_text("new_command")}
- `/load <session_id>` - {self.text_manager.get_text("load_command")}
- `/current` - {self.text_manager.get_text("current_command")}

### {self.text_manager.get_text("config_options_help")}
- `/streaming on|off` - {self.text_manager.get_text("streaming_command")}
- `/timestamps on|off` - {self.text_manager.get_text("timestamps_command")}
- `/metadata on|off` - {self.text_manager.get_text("metadata_command")}
            """
    
    async def process_user_input(self, user_input: str) -> bool:
        """
        处理用户输入（新架构）
        
        Args:
            user_input: 用户输入内容
            
        Returns:
            是否继续运行
        """
        # 处理命令
        if user_input.startswith('/'):
            return await self._handle_command(user_input)
        
        # 确保有当前会话
        if not self.session_manager.current_session_id:
            session_id = self.session_manager.create_new_session()
            self.console.print(self.text_manager.get_text("create_new_session", session_id=session_id))

        try:
            # 构建AgentContext（不包含当前用户输入，避免重复保存）
            context = self._build_agent_context()
            if not context:
                self.console.print(self.text_manager.get_text("context_build_failed"))
                return True
            
            # 创建流式会话（统一流式架构，总是创建）
            streaming_session = self._create_streaming_session(
                self.session_manager.current_session_id
            )
            self.current_streaming_session = streaming_session

            # 只有在启用流式显示时才启动流式会话
            if self.enable_streaming:
                await streaming_session.start()

            # 使用StatelessGTPlanner处理，传递语言参数
            result = await self.planner.process(user_input, context, streaming_session, language=self.language)

            # 处理结果
            if result.success:
                # 使用SQLiteSessionManager的update_from_agent_result方法，传递用户输入以避免重复保存
                update_success = self.session_manager.update_from_agent_result(result, user_input=user_input)

                if not update_success:
                    self.console.print(self.text_manager.get_text("database_save_warning"))
                
                # 如果没有启用流式响应，显示结果
                if not self.enable_streaming and result.new_messages:
                    # 查找最后一个assistant消息
                    last_assistant_message = None
                    for msg in reversed(result.new_messages):
                        if msg.role.value == "assistant":
                            last_assistant_message = msg
                            break

                    if last_assistant_message:
                        self.console.print(Panel(
                            last_assistant_message.content,
                            title="🤖 GTPlanner",
                            border_style="blue"
                        ))
            else:
                self.console.print(f"❌ [red]处理失败:[/red] {result.error}")



        except Exception as e:
            self.console.print(f"💥 [red]处理异常:[/red] {str(e)}")
            if self.verbose:
                import traceback
                self.console.print(traceback.format_exc())

        finally:
            # 清理流式会话
            if self.current_streaming_session:
                await self._cleanup_streaming_session()
        
        return True

    async def _handle_command(self, command: str) -> bool:
        """处理CLI命令"""
        parts = command[1:].split()
        if not parts:
            return True

        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd == "help":
            self.show_help()

        elif cmd == "quit" or cmd == "exit":
            self.console.print(self.text_manager.get_text("goodbye"))
            return False

        elif cmd == "sessions":
            self._show_sessions()

        elif cmd == "new":
            title = " ".join(args) if args else None
            session_id = self.session_manager.create_new_session(title)
            self.console.print(self.text_manager.get_text("create_new_session", session_id=session_id))

        elif cmd == "load":
            if not args:
                self.console.print(self.text_manager.get_text("specify_session_id"))
            else:
                partial_id = args[0]
                success, loaded_id, matches = self.session_manager.load_session_by_partial_id(partial_id)

                if success:
                    self.console.print(self.text_manager.get_text("session_loaded", session_id=loaded_id))
                elif matches:
                    # 找到多个匹配，显示选择界面
                    selected_session = self._show_session_selection(matches, partial_id)
                    if selected_session:
                        if self.session_manager.load_session(selected_session["session_id"]):
                            self.console.print(self.text_manager.get_text("session_loaded", session_id=selected_session['session_id']))
                        else:
                            self.console.print(self.text_manager.get_text("session_load_failed", session_id=selected_session['session_id']))
                else:
                    self.console.print(self.text_manager.get_text("no_session_found", partial_id=partial_id))

        elif cmd == "current":
            self._show_current_session()

        elif cmd == "config":
            self._show_config()

        elif cmd == "streaming":
            if args and args[0].lower() in ["on", "off"]:
                self.enable_streaming = args[0].lower() == "on"
                status = "启用" if self.enable_streaming else "禁用"
                self.console.print(f"🌊 [blue]流式响应已{status}[/blue]")
            else:
                self.console.print("❌ [red]用法: /streaming on|off[/red]")

        elif cmd == "timestamps":
            if args and args[0].lower() in ["on", "off"]:
                self.show_timestamps = args[0].lower() == "on"
                status = "启用" if self.show_timestamps else "禁用"
                self.console.print(f"⏰ [blue]时间戳显示已{status}[/blue]")
            else:
                self.console.print("❌ [red]用法: /timestamps on|off[/red]")

        elif cmd == "metadata":
            if args and args[0].lower() in ["on", "off"]:
                self.show_metadata = args[0].lower() == "on"
                status = "启用" if self.show_metadata else "禁用"
                self.console.print(f"📊 [blue]元数据显示已{status}[/blue]")
            else:
                self.console.print("❌ [red]用法: /metadata on|off[/red]")

        else:
            self.console.print(f"❓ [yellow]未知命令:[/yellow] {cmd}")
            self.console.print("💡 [blue]输入 /help 查看可用命令[/blue]")

        return True

    def _show_session_selection(self, matches: List[Dict[str, Any]], partial_id: str) -> Optional[Dict[str, Any]]:
        """
        显示会话选择界面

        Args:
            matches: 匹配的会话列表
            partial_id: 用户输入的部分ID

        Returns:
            用户选择的会话信息或None
        """
        self.console.print(f"\n🔍 [yellow]找到 {len(matches)} 个匹配 '{partial_id}' 的会话，请选择：[/yellow]\n")

        # 创建选择表格
        table = Table(title="匹配的会话")
        table.add_column("序号", style="cyan", width=6)
        table.add_column("会话ID", style="green", width=20)
        table.add_column("标题", style="blue", width=30)
        table.add_column("创建时间", style="yellow", width=20)
        table.add_column("消息数", style="magenta", width=8)

        for i, session in enumerate(matches, 1):
            # 显示前12位ID + ...
            display_id = session["session_id"][:12] + "..." if len(session["session_id"]) > 12 else session["session_id"]
            table.add_row(
                str(i),
                display_id,
                session["title"][:28] + "..." if len(session["title"]) > 28 else session["title"],
                session["created_at"],
                str(session["total_messages"])
            )

        self.console.print(table)

        # 获取用户选择
        while True:
            try:
                choice = Prompt.ask(
                    f"\n请输入序号 (1-{len(matches)}) 或 'c' 取消",
                    default="c"
                ).strip().lower()

                if choice in ['c', 'cancel', '取消']:
                    self.console.print("❌ [yellow]已取消选择[/yellow]")
                    return None

                choice_num = int(choice)
                if 1 <= choice_num <= len(matches):
                    selected = matches[choice_num - 1]
                    self.console.print(f"✅ [green]已选择会话:[/green] {selected['session_id'][:12]}... ({selected['title']})")
                    return selected
                else:
                    self.console.print(f"❌ [red]请输入 1-{len(matches)} 之间的数字[/red]")

            except ValueError:
                self.console.print("❌ [red]请输入有效的数字或 'c' 取消[/red]")
            except KeyboardInterrupt:
                self.console.print("\n❌ [yellow]已取消选择[/yellow]")
                return None

    def _show_sessions(self):
        """显示会话列表"""
        sessions = self.session_manager.list_sessions()

        if not sessions:
            self.console.print("📭 [yellow]暂无会话[/yellow]")
            return

        table = Table(title="📋 会话列表")
        table.add_column("会话ID", style="cyan")
        table.add_column("标题", style="green")
        table.add_column("创建时间", style="blue")
        table.add_column("消息数", style="yellow")
        table.add_column("状态", style="magenta")

        current_id = self.session_manager.current_session_id

        for session in sessions:
            status = "🔸 当前" if session["session_id"] == current_id else ""
            table.add_row(
                session["session_id"][:8] + "...",  # 显示前8位
                session["title"],
                session["created_at"],
                str(session["total_messages"]),  # 使用新的字段名
                status
            )

        self.console.print(table)

    def _show_current_session(self):
        """显示当前会话信息"""
        if not self.session_manager.current_session_id:
            self.console.print("❌ [red]当前无活跃会话[/red]")
            return

        session = self.session_manager.get_current_session()
        if not session:
            self.console.print("❌ [red]无法获取当前会话信息[/red]")
            return

        # 获取统计信息
        stats = self.session_manager.get_session_statistics()

        info_text = f"""
## 📋 当前会话信息

- **会话ID**: {session['session_id'][:8]}...
- **标题**: {session['title']}
- **创建时间**: {session['created_at']}
- **项目阶段**: {session['project_stage']}
- **消息数量**: {session['total_messages']}
- **Token数量**: {session['total_tokens']}
- **工具执行数**: {stats.get('total_executions', 0)}
- **成功执行数**: {stats.get('successful_executions', 0)}
        """

        self.console.print(Panel(
            Markdown(info_text),
            title="当前会话",
            border_style="cyan"
        ))

    def _show_config(self):
        """显示当前配置"""
        config_text = f"""
## ⚙️ 当前配置

- **流式响应**: {'✅ 启用' if self.enable_streaming else '❌ 禁用'}
- **时间戳显示**: {'✅ 启用' if self.show_timestamps else '❌ 禁用'}
- **元数据显示**: {'✅ 启用' if self.show_metadata else '❌ 禁用'}
- **详细模式**: {'✅ 启用' if self.verbose else '❌ 禁用'}

## 🔧 修改配置
- `/streaming on|off` - 开启/关闭流式响应
- `/timestamps on|off` - 开启/关闭时间戳显示
- `/metadata on|off` - 开启/关闭元数据显示
        """

        self.console.print(Panel(
            Markdown(config_text),
            title="配置信息",
            border_style="green"
        ))

    async def run_interactive(self):
        """运行交互式CLI"""
        # 显示ASCII logo
        self.show_ascii_logo()
        # 显示欢迎信息
        self.show_welcome()

        while self.running:
            try:
                # 显示提示符
                current_session = self.session_manager.current_session_id or "无会话"
                prompt_text = f"[bold blue]GTPlanner[/bold blue] ({current_session[:8]}) > "

                user_input = Prompt.ask(prompt_text).strip()

                if not user_input:
                    continue

                # 处理用户输入
                should_continue = await self.process_user_input(user_input)
                if not should_continue:
                    break

            except KeyboardInterrupt:
                self.console.print(self.text_manager.get_text("interrupt_signal"))
                if Confirm.ask(self.text_manager.get_text("confirm_exit")):
                    break
            except EOFError:
                self.console.print(self.text_manager.get_text("goodbye"))
                break
            except Exception as e:
                self.console.print(self.text_manager.get_text("cli_exception", error=str(e)))
                if self.verbose:
                    import traceback
                    self.console.print(traceback.format_exc())

        # 清理资源
        await self._cleanup_streaming_session()

    async def run_single_command(self, requirement: str):
        """运行单个命令（非交互式）"""
        # 显示ASCII logo
        self.show_ascii_logo()
        self.console.print(self.text_manager.get_text("processing_requirement", requirement=requirement))

        # 创建新会话
        session_id = self.session_manager.create_new_session("单次需求")
        self.console.print(self.text_manager.get_text("create_new_session", session_id=session_id))

        # 处理需求
        await self.process_user_input(requirement)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="现代化GTPlanner CLI")
    parser.add_argument("requirement", nargs="?", help="直接处理的需求")
    parser.add_argument("--no-streaming", action="store_true", help="禁用流式响应")
    parser.add_argument("--timestamps", action="store_true", help="显示时间戳")
    parser.add_argument("--metadata", action="store_true", help="显示元数据")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    parser.add_argument("--load", help="加载指定会话ID")
    parser.add_argument("--language", "-l",
                       choices=["zh", "en", "ja", "es", "fr"],
                       default="zh",
                       help="界面语言 (zh=中文, en=英文, ja=日文, es=西班牙文, fr=法文)，默认为中文")

    args = parser.parse_args()

    # 创建现代化CLI实例
    cli = ModernGTPlannerCLI(
        enable_streaming=not args.no_streaming,
        show_timestamps=args.timestamps,
        show_metadata=args.metadata,
        verbose=args.verbose,
        language=args.language
    )

    # 如果指定了加载会话
    if args.load:
        if cli.session_manager.load_session(args.load):
            cli.console.print(cli.text_manager.get_text("session_loaded", session_id=args.load))
        else:
            cli.console.print(cli.text_manager.get_text("session_load_failed", session_id=args.load))
            return 1

    try:
        if args.requirement:
            # 直接处理需求
            await cli.run_single_command(args.requirement)
        else:
            # 交互式模式
            await cli.run_interactive()
    except Exception as e:
        console = Console()
        # 创建临时文本管理器用于错误显示
        temp_text_manager = CLITextManager(args.language)
        console.print(temp_text_manager.get_text("cli_run_exception", error=str(e)))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
