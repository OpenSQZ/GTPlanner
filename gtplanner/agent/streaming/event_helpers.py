"""
流式事件发送辅助函数

提供简洁的API来发送各种类型的流式事件，避免重复代码。
"""

from typing import Dict, Any, Optional
from .stream_types import StreamEventBuilder, ToolCallStatus, DesignDocument


async def emit_processing_status(shared: Dict[str, Any], message: str) -> None:
    """
    发送处理状态事件
    
    Args:
        shared: 共享状态字典（包含 streaming_session）
        message: 状态消息
    """
    streaming_session = shared.get("streaming_session")
    if streaming_session:
        event = StreamEventBuilder.processing_status(
            streaming_session.session_id, 
            message
        )
        await streaming_session.emit_event(event)


async def emit_error(shared: Dict[str, Any], error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
    """
    发送错误事件
    
    Args:
        shared: 共享状态字典（包含 streaming_session）
        error_message: 错误消息
        error_details: 错误详细信息（可选）
    """
    streaming_session = shared.get("streaming_session")
    if streaming_session:
        event = StreamEventBuilder.error(
            streaming_session.session_id,
            error_message,
            error_details
        )
        await streaming_session.emit_event(event)


async def emit_tool_start(shared: Dict[str, Any], tool_name: str, message: str, arguments: Optional[Dict[str, Any]] = None, call_id: Optional[str] = None) -> None:
    """
    发送工具开始事件

    Args:
        shared: 共享状态字典（包含 streaming_session）
        tool_name: 工具名称
        message: 进度消息
        arguments: 工具参数（可选）
        call_id: 工具调用ID（可选）
    """
    streaming_session = shared.get("streaming_session")
    if streaming_session:
        tool_status = ToolCallStatus(
            tool_name=tool_name,
            status="starting",
            call_id=call_id,
            progress_message=message,
            arguments=arguments
        )
        event = StreamEventBuilder.tool_call_start(
            streaming_session.session_id,
            tool_status
        )
        await streaming_session.emit_event(event)


async def emit_tool_progress(shared: Dict[str, Any], tool_name: str, message: str) -> None:
    """
    发送工具进度事件

    Args:
        shared: 共享状态字典（包含 streaming_session）
        tool_name: 工具名称
        message: 进度消息
    """
    streaming_session = shared.get("streaming_session")
    if streaming_session:
        # 从shared中获取对应的call_id
        call_id = None
        if "tool_call_ids" in shared and tool_name in shared["tool_call_ids"]:
            call_id = shared["tool_call_ids"][tool_name]

        tool_status = ToolCallStatus(
            tool_name=tool_name,
            status="running",
            call_id=call_id,
            progress_message=message
        )
        event = StreamEventBuilder.tool_call_progress(
            streaming_session.session_id,
            tool_status
        )
        await streaming_session.emit_event(event)


async def emit_tool_end(shared: Dict[str, Any], tool_name: str, success: bool, message: str,
                       execution_time: float = 0.0, error_message: Optional[str] = None,
                       result: Optional[Dict[str, Any]] = None, call_id: Optional[str] = None) -> None:
    """
    发送工具结束事件

    Args:
        shared: 共享状态字典（包含 streaming_session）
        tool_name: 工具名称
        success: 是否成功
        message: 结束消息
        execution_time: 执行时间
        error_message: 错误消息（如果失败）
        result: 工具执行结果（可选）
        call_id: 工具调用ID（可选）
    """
    streaming_session = shared.get("streaming_session")
    if streaming_session:
        # 如果没有提供call_id，尝试从shared中获取
        if call_id is None and "tool_call_ids" in shared and tool_name in shared["tool_call_ids"]:
            call_id = shared["tool_call_ids"][tool_name]

        tool_status = ToolCallStatus(
            tool_name=tool_name,
            status="completed" if success else "failed",
            call_id=call_id,
            progress_message=message,
            execution_time=execution_time,
            error_message=error_message,
            result=result
        )
        event = StreamEventBuilder.tool_call_end(
            streaming_session.session_id, 
            tool_status
        )
        await streaming_session.emit_event(event)


# 便捷函数：从 prep_res 中获取 streaming_session
async def emit_processing_status_from_prep(prep_res: Dict[str, Any], message: str) -> None:
    """
    从 prep_res 中获取 streaming_session 并发送处理状态事件
    
    Args:
        prep_res: prep_async 返回的结果字典（包含 streaming_session）
        message: 状态消息
    """
    streaming_session = prep_res.get("streaming_session")
    if streaming_session:
        event = StreamEventBuilder.processing_status(
            streaming_session.session_id, 
            message
        )
        await streaming_session.emit_event(event)


async def emit_error_from_prep(prep_res: Dict[str, Any], error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
    """
    从 prep_res 中获取 streaming_session 并发送错误事件
    
    Args:
        prep_res: prep_async 返回的结果字典（包含 streaming_session）
        error_message: 错误消息
        error_details: 错误详细信息（可选）
    """
    streaming_session = prep_res.get("streaming_session")
    if streaming_session:
        event = StreamEventBuilder.error(
            streaming_session.session_id,
            error_message,
            error_details
        )
        await streaming_session.emit_event(event)


# 通用函数：自动检测 streaming_session 来源
async def emit_event_auto(context: Dict[str, Any], event_type: str, message: str, **kwargs) -> None:
    """
    自动检测 streaming_session 来源并发送事件
    
    Args:
        context: 可能包含 streaming_session 的字典（shared 或 prep_res）
        event_type: 事件类型 ('status', 'error', 'tool_start', 'tool_progress', 'tool_end')
        message: 消息内容
        **kwargs: 其他参数
    """
    streaming_session = context.get("streaming_session")
    if not streaming_session:
        return
    
    if event_type == "status":
        event = StreamEventBuilder.processing_status(streaming_session.session_id, message)
    elif event_type == "error":
        event = StreamEventBuilder.error(streaming_session.session_id, message, kwargs.get("error_details"))
    elif event_type == "tool_start":
        tool_status = ToolCallStatus(
            tool_name=kwargs.get("tool_name", "unknown"),
            status="starting",
            progress_message=message,
            arguments=kwargs.get("arguments")
        )
        event = StreamEventBuilder.tool_call_start(streaming_session.session_id, tool_status)
    elif event_type == "tool_progress":
        tool_status = ToolCallStatus(
            tool_name=kwargs.get("tool_name", "unknown"),
            status="running",
            progress_message=message
        )
        event = StreamEventBuilder.tool_call_progress(streaming_session.session_id, tool_status)
    elif event_type == "tool_end":
        tool_status = ToolCallStatus(
            tool_name=kwargs.get("tool_name", "unknown"),
            status="completed" if kwargs.get("success", True) else "failed",
            progress_message=message,
            execution_time=kwargs.get("execution_time", 0.0),
            error_message=kwargs.get("error_message"),
            result=kwargs.get("result")
        )
        event = StreamEventBuilder.tool_call_end(streaming_session.session_id, tool_status)
    else:
        return  # 未知事件类型
    
    await streaming_session.emit_event(event)


async def emit_design_document(
    shared: Dict[str, Any],
    filename: str,
    content: str
) -> None:
    """
    发送设计文档生成事件

    Args:
        shared: 共享状态字典（包含 streaming_session）
        filename: 文件名（如 "01_agent_analysis.md"）
        content: 文档内容
    """
    streaming_session = shared.get("streaming_session")
    if streaming_session:
        document = DesignDocument(
            filename=filename,
            content=content
        )

        event = StreamEventBuilder.design_document_generated(
            streaming_session.session_id,
            document
        )
        await streaming_session.emit_event(event)


async def emit_prefabs_info(
    shared: Dict[str, Any],
    prefabs: list
) -> None:
    """
    发送预制件信息事件（轻量级）
    
    Args:
        shared: 共享状态字典（包含 streaming_session）
        prefabs: 预制件列表，每个元素包含 id 和 version
            例如: [{"id": "video-processing-prefab", "version": "0.3.1"}]
    
    Note:
        前端收到此事件后，会使用 id 和 version 调用 prefab-gateway 接口
        获取完整的 prefab-manifest.json
    """
    streaming_session = shared.get("streaming_session")
    print(f"🔍 [emit_prefabs_info] streaming_session 存在: {streaming_session is not None}")
    print(f"🔍 [emit_prefabs_info] prefabs 数据: {prefabs}")
    
    if streaming_session:
        event = StreamEventBuilder.prefabs_info(
            streaming_session.session_id,
            prefabs
        )
        print(f"📨 [emit_prefabs_info] 创建事件: type={event.event_type}, session_id={event.session_id}")
        await streaming_session.emit_event(event)
        print(f"✅ [emit_prefabs_info] 事件已发送到 streaming_session")
    else:
        print(f"⚠️ [emit_prefabs_info] streaming_session 为 None，无法发送事件")
