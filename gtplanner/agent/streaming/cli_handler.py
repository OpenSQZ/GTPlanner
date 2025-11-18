"""
CLI流式处理器

为CLI客户端提供流式响应处理，支持实时显示LLM回复和工具调用状态。
"""


from typing import Optional, Dict, Any
from datetime import datetime

from .stream_types import StreamEvent, StreamEventType
from .stream_interface import StreamHandler

try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class CLIStreamHandler(StreamHandler):
    """
    CLI流式事件处理器
    负责将流式事件转换为CLI友好的显示格式，包括：
    - 实时显示LLM回复内容
    - 显示工具调用状态和进度
    - 优雅处理错误和中断
    """

    def __init__(self, show_timestamps: bool = False, show_metadata: bool = False):
        self.show_timestamps = show_timestamps
        self.show_metadata = show_metadata
        self.current_message = ""
        self.is_message_active = False
        self.active_tools: Dict[str, Dict[str, Any]] = {}
        self._closed = False
        
        # ⭐ 进度条相关属性
        if RICH_AVAILABLE:
            self.progress: Optional[Progress] = None
            self.console = Console()
        else:
            self.progress = None
            self.console = None
        self.progress_task = None
        self.is_long_running_task = False
        self.chunk_count = 0

    async def handle_event(self, event: StreamEvent) -> None:
        """处理单个流式事件"""
        if self._closed:
            return

        try:
            if event.event_type == StreamEventType.CONVERSATION_START:
                await self._handle_conversation_start(event)

            elif event.event_type == StreamEventType.ASSISTANT_MESSAGE_START:
                await self._handle_message_start(event)

            elif event.event_type == StreamEventType.ASSISTANT_MESSAGE_CHUNK:
                await self._handle_message_chunk(event)

            elif event.event_type == StreamEventType.ASSISTANT_MESSAGE_END:
                await self._handle_message_end(event)

            elif event.event_type == StreamEventType.TOOL_CALL_START:
                await self._handle_tool_start(event)

            elif event.event_type == StreamEventType.TOOL_CALL_PROGRESS:
                await self._handle_tool_progress(event)

            elif event.event_type == StreamEventType.TOOL_CALL_END:
                await self._handle_tool_end(event)

            elif event.event_type == StreamEventType.PROCESSING_STATUS:
                await self._handle_processing_status(event)

            elif event.event_type == StreamEventType.ERROR:
                await self._handle_error_event(event)

            elif event.event_type == StreamEventType.DESIGN_DOCUMENT_GENERATED:
                await self._handle_design_document(event)

            elif event.event_type == StreamEventType.CONVERSATION_END:
                await self._handle_conversation_end(event)

        except Exception as e:
            await self.handle_error(e, event.session_id)

    async def _handle_conversation_start(self, event: StreamEvent) -> None:
        """处理对话开始事件"""
        user_input = event.data.get("user_input", "")

        if self.show_timestamps:
            timestamp = self._format_timestamp(event.timestamp)
            print(f"\n[{timestamp}] 🚀 开始处理: {user_input}")
        else:
            print(f"\n🚀 开始处理: {user_input}")

        print("=" * 50)

    async def _handle_message_start(self, event: StreamEvent) -> None:
        """处理助手消息开始事件"""
        if not self.is_message_active:
            # ⭐ 检查元数据，判断是否是长时间任务（文档生成）
            metadata = event.metadata or {}
            message_type = metadata.get("message_type", "")
            
            if message_type == "document_generation" and RICH_AVAILABLE and self.console:
                # ⭐ 长时间任务：显示进度条
                self.is_long_running_task = True
                self.chunk_count = 0
                self.progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                    console=self.console,
                    transient=False
                )
                self.progress.start()
                # 使用较大的 total 值，通过字符数估算进度
                self.progress_task = self.progress.add_task(
                    "🤖 AI 正在生成设计文档...",
                    total=100
                )
            else:
                # 普通消息：显示流式内容
                self.is_long_running_task = False
                print("\n🤖 GTPlanner: ", end="", flush=True)
            
            self.is_message_active = True
            self.current_message = ""

    async def _handle_message_chunk(self, event: StreamEvent) -> None:
        """处理助手消息片段事件"""
        chunk_content = event.data.get("content", "")

        if chunk_content:
            if self.is_long_running_task and self.progress and self.progress_task is not None:
                # ⭐ 长时间任务：更新进度条而不是显示内容
                self.chunk_count += len(chunk_content)
                # 根据字符数估算进度（假设平均文档长度约 5000 字符）
                # 可以根据实际情况调整这个估算值
                estimated_total_chars = 5000
                progress_value = min(self.chunk_count / estimated_total_chars * 100, 99)  # 最多99%，留1%给完成
                self.progress.update(self.progress_task, completed=progress_value)
            else:
                # 普通消息：显示流式内容
                print(chunk_content, end="", flush=True)
            
            self.current_message += chunk_content

    async def _handle_message_end(self, event: StreamEvent) -> None:
        """处理助手消息结束事件"""
        if self.is_message_active:
            if self.is_long_running_task and self.progress and self.progress_task is not None:
                # ⭐ 完成进度条
                self.progress.update(self.progress_task, completed=100)
                self.progress.stop()
                self.progress = None
                self.progress_task = None
                self.is_long_running_task = False
            else:
                # 普通消息：换行
                print()
            
            self.is_message_active = False

            # 如果有完整消息且与当前累积的不同，使用完整消息
            complete_message = event.data.get("complete_message", "")
            if complete_message and complete_message != self.current_message:
                print(f"📝 完整回复: {complete_message}")

            self.current_message = ""
            self.chunk_count = 0

    async def _handle_tool_start(self, event: StreamEvent) -> None:
        """处理工具调用开始事件"""
        tool_name = event.data.get("tool_name", "unknown")
        progress_message = event.data.get("progress_message", f"正在调用{tool_name}工具...")

        # 如果正在显示消息，先换行
        if self.is_message_active:
            print()

        print(f"\n🔧 {progress_message}")

        # 记录活跃工具
        self.active_tools[tool_name] = {
            "start_time": datetime.now(),
            "status": "running"
        }

    async def _handle_tool_progress(self, event: StreamEvent) -> None:
        """处理工具调用进度事件"""
        tool_name = event.data.get("tool_name", "unknown")
        progress_message = event.data.get("progress_message", "")

        if progress_message:
            print(f"   ⏳ {progress_message}")

    async def _handle_tool_end(self, event: StreamEvent) -> None:
        """处理工具调用结束事件"""
        tool_name = event.data.get("tool_name", "unknown")
        status = event.data.get("status", "completed")
        execution_time = event.data.get("execution_time", 0)
        error_message = event.data.get("error_message")

        if status == "completed":
            print(f"   ✅ {tool_name}工具执行完成 (耗时: {execution_time:.2f}s)")
        elif status == "failed":
            print(f"   ❌ {tool_name}工具执行失败: {error_message}")

        # 移除活跃工具记录
        if tool_name in self.active_tools:
            del self.active_tools[tool_name]

    async def _handle_processing_status(self, event: StreamEvent) -> None:
        """处理处理状态事件"""
        status_message = event.data.get("status_message", "")

        if status_message:
            # 如果正在显示消息，先换行
            if self.is_message_active:
                print()

            print(f"ℹ️  {status_message}")

    async def _handle_error_event(self, event: StreamEvent) -> None:
        """处理错误事件"""
        error_message = event.data.get("error_message", "未知错误")
        error_details = event.data.get("error_details", {})

        # 如果正在显示消息，先换行
        if self.is_message_active:
            print()

        print(f"\n❌ 错误: {error_message}")

        if self.show_metadata and error_details:
            print(f"   详细信息: {error_details}")

    async def _handle_design_document(self, event: StreamEvent) -> None:
        """
        处理设计文档生成事件（包括设计文档和数据库设计文档）
        
        为文件名添加时间戳，避免文件覆盖，保留历史版本。
        """
        from pathlib import Path
        
        original_filename = event.data.get("filename", "unknown.md")
        content = event.data.get("content", "")

        # 如果正在显示消息，先换行
        if self.is_message_active:
            print()

        # 生成带时间戳的文件名（格式：base_name_YYYYMMDD_HHMMSS.ext）
        base_name = Path(original_filename).stem
        extension = Path(original_filename).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}{extension}"

        # 根据文件名判断文档类型
        doc_type = "数据库设计文档" if "database" in original_filename.lower() else "设计文档"
        print(f"\n📄 {doc_type}已生成: {filename}")

        # 使用文件生成器保存文档
        try:
            from gtplanner.utils.file_generator import write_file
            file_info = write_file(filename, content)

            print(f"   📁 保存路径: {file_info['path']}")
            print(f"   📏 文件大小: {file_info['size']} 字节")

            if self.show_metadata:
                print(f"   🕒 创建时间: {datetime.fromtimestamp(file_info['created_at']).strftime('%H:%M:%S')}")
                print(f"   📝 编码格式: {file_info['encoding']}")

        except Exception as e:
            print(f"   ❌ 保存失败: {str(e)}")
            # 如果保存失败，至少显示文档内容的前几行
            lines = content.split('\n')[:3]
            print(f"   📝 文档预览:")
            for line in lines:
                print(f"      {line}")
            total_lines = len(content.split('\n'))
            if total_lines > 3:
                print(f"      ... (共 {total_lines} 行)")

    async def _handle_conversation_end(self, event: StreamEvent) -> None:
        """处理对话结束事件"""
        success = event.data.get("success", False)
        execution_time = event.data.get("execution_time", 0)

        print("\n" + "=" * 50)

        if success:
            print(f"✅ 处理完成 (总耗时: {execution_time:.2f}s)")
        else:
            print(f"❌ 处理失败 (总耗时: {execution_time:.2f}s)")

        if self.show_metadata:
            new_messages_count = event.data.get("new_messages_count", 0)
            print(f"📊 统计: {new_messages_count}条新消息")

    async def handle_error(self, error: Exception, session_id: Optional[str] = None) -> None:
        """处理错误"""
        if self._closed:
            return

        # 如果正在显示消息，先换行
        if self.is_message_active:
            print()

        print(f"\n💥 处理器错误: {str(error)}")

        if self.show_metadata:
            print(f"   错误类型: {type(error).__name__}")
            if session_id:
                print(f"   会话ID: {session_id}")

    async def close(self) -> None:
        """关闭处理器"""
        if self._closed:
            return

        self._closed = True

        # ⭐ 关闭进度条（如果存在）
        if self.progress:
            self.progress.stop()
            self.progress = None
            self.progress_task = None

        # 如果还有活跃的工具调用，显示中断信息
        if self.active_tools:
            print(f"\n⚠️  中断了{len(self.active_tools)}个正在执行的工具调用")

        # 如果正在显示消息，换行
        if self.is_message_active:
            print("\n⚠️  消息显示被中断")

        self.active_tools.clear()
        self.current_message = ""
        self.is_message_active = False
        self.is_long_running_task = False
        self.chunk_count = 0

    def _format_timestamp(self, timestamp_str: str) -> str:
        """格式化时间戳"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S")
        except:
            return timestamp_str[:8]  # 简单截取

    # 便捷方法
    def enable_timestamps(self) -> None:
        """启用时间戳显示"""
        self.show_timestamps = True

    def disable_timestamps(self) -> None:
        """禁用时间戳显示"""
        self.show_timestamps = False

    def enable_metadata(self) -> None:
        """启用元数据显示"""
        self.show_metadata = True

    def disable_metadata(self) -> None:
        """禁用元数据显示"""
        self.show_metadata = False
