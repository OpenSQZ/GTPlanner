"""
流式事件发送辅助函数

提供简洁的API来发送各种类型的流式事件，避免重复代码。
"""

from typing import Dict, Any, Optional, List
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
    发送设计文档生成事件，并同时将文档存储到 shared 中供同一轮对话的其他工具使用

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
    
    # 🆕 将文档信息存储到 shared["generated_documents"] 中
    # 这样同一轮对话中的其他工具（如 edit_document）可以立即访问
    
    # 🔥 从 tool_execution_results 恢复历史文档（跨工具调用）
    if "generated_documents" not in shared:
        historical_docs = shared.get("tool_execution_results", {}).get("designs", {}).get("generated_documents", [])
        shared["generated_documents"] = list(historical_docs) if historical_docs else []
    
    # 判断文档类型
    document_type = "database_design" if "database" in filename.lower() else "design"
    
    shared["generated_documents"].append({
        "type": document_type,
        "filename": filename,
        "content": content,
        "timestamp": __import__('time').time()
    })


async def emit_database_design(
    shared: Dict[str, Any],
    filename: str,
    content: str
) -> None:
    """
    发送数据库设计文档生成事件，并同时将文档存储到 shared 中供同一轮对话的其他工具使用

    Args:
        shared: 共享状态字典（包含 streaming_session）
        filename: 文件名（如 "database_design.md"）
        content: 数据库设计文档内容
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
    
    # 🆕 将文档信息存储到 shared["generated_documents"] 中
    # 这样同一轮对话中的其他工具（如 edit_document）可以立即访问
    
    # 🔥 从 tool_execution_results 恢复历史文档（跨工具调用）
    if "generated_documents" not in shared:
        historical_docs = shared.get("tool_execution_results", {}).get("designs", {}).get("generated_documents", [])
        shared["generated_documents"] = list(historical_docs) if historical_docs else []
    
    shared["generated_documents"].append({
        "type": "database_design",
        "filename": filename,
        "content": content,
        "timestamp": __import__('time').time()
    })


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


async def emit_document_edit_proposal(
    shared: Dict[str, Any],
    proposal_id: str,
    document_type: str,
    document_filename: str,
    edits: List[Dict[str, str]],
    summary: str,
    preview_content: Optional[str] = None
) -> None:
    """
    发送文档编辑提案事件
    
    Args:
        shared: 共享状态字典（包含 streaming_session）
        proposal_id: 提案唯一ID
        document_type: 文档类型（"design" 或 "database_design"）
        document_filename: 文档文件名
        edits: 编辑操作列表，每个元素包含 search, replace, reason
        summary: 编辑摘要
        preview_content: 应用所有编辑后的预览内容（可选）
    """
    streaming_session = shared.get("streaming_session")
    
    print(f"🔍 [emit_document_edit_proposal] 开始发送文档编辑提案")
    print(f"🔍 [emit_document_edit_proposal] streaming_session 存在: {streaming_session is not None}")
    print(f"🔍 [emit_document_edit_proposal] proposal_id: {proposal_id}")
    print(f"🔍 [emit_document_edit_proposal] document_type: {document_type}")
    print(f"🔍 [emit_document_edit_proposal] edits 数量: {len(edits)}")
    print(f"🔍 [emit_document_edit_proposal] summary: {summary}")
    
    if streaming_session:
        from .stream_types import DocumentEditProposal, DocumentEdit
        
        # 转换edits为DocumentEdit对象列表
        edit_objects = [
            DocumentEdit(
                search=edit["search"],
                replace=edit["replace"],
                reason=edit["reason"]
            )
            for edit in edits
        ]
        
        print(f"✅ [emit_document_edit_proposal] 已创建 {len(edit_objects)} 个 DocumentEdit 对象")
        
        # 创建提案对象
        proposal = DocumentEditProposal(
            proposal_id=proposal_id,
            document_type=document_type,
            document_filename=document_filename,
            edits=edit_objects,
            summary=summary,
            preview_content=preview_content
        )
        
        print(f"✅ [emit_document_edit_proposal] 已创建 DocumentEditProposal 对象")
        
        # 发送事件
        event = StreamEventBuilder.document_edit_proposal(
            streaming_session.session_id,
            proposal
        )
        
        print(f"📨 [emit_document_edit_proposal] 准备发送事件: type={event.event_type}, session_id={event.session_id}")
        print(f"📨 [emit_document_edit_proposal] 事件数据预览: {str(event.data)[:200]}...")
        
        await streaming_session.emit_event(event)
        
        print(f"✅ [emit_document_edit_proposal] document_edit_proposal 事件已发送!")
    else:
        print(f"⚠️ [emit_document_edit_proposal] streaming_session 为 None，无法发送事件")
