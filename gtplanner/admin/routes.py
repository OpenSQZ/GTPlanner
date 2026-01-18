"""
GTPlanner Admin Routes
后台管理界面路由
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 初始化模板引擎
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# 初始化MySQL数据库
from gtplanner.admin.database import (
    get_db_session, get_session_by_id, list_sessions, create_session as db_create_session,
    update_session as db_update_session, delete_session as db_delete_session,
    get_messages, session_to_dict, message_to_dict, init_db
)

# 初始化数据库表
try:
    init_db()
    logger.info("✅ MySQL数据库初始化成功")
except Exception as e:
    logger.error(f"❌ MySQL数据库初始化失败: {e}")


# ==================== 数据模型 ====================

class CreateSessionRequest(BaseModel):
    """创建会话请求模型"""
    title: str
    project_stage: str = "requirements"
    metadata: Optional[Dict[str, Any]] = None


class UpdateSessionRequest(BaseModel):
    """更新会话请求模型"""
    title: Optional[str] = None
    project_stage: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


async def get_system_stats() -> Dict[str, Any]:
    """
    获取系统统计信息
    """
    try:
        # 获取数据库文件大小
        db_path = BASE_DIR / "gtplanner_conversations.db"
        db_size = db_path.stat().st_size if db_path.exists() else 0

        # 获取日志文件信息
        logs_dir = BASE_DIR / "logs"
        log_files = list(logs_dir.glob("*.log")) if logs_dir.exists() else []
        log_count = len(log_files)

        # 获取最近的日志文件
        latest_log = None
        if log_files:
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_log = log_files[0].name

        return {
            "db_size_mb": round(db_size / 1024 / 1024, 2),
            "log_file_count": log_count,
            "latest_log_file": latest_log,
            "uptime_hours": "N/A",  # TODO: 实现运行时间统计
            "python_version": "3.11+",
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {}


async def get_log_files(limit: int = 10) -> List[Dict[str, Any]]:
    """
    获取日志文件列表
    """
    try:
        logs_dir = BASE_DIR / "logs"
        if not logs_dir.exists():
            return []

        log_files = []
        for log_file in logs_dir.glob("*.log"):
            stat = log_file.stat()
            log_files.append({
                "name": log_file.name,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })

        # 按修改时间排序，最新的在前
        log_files.sort(key=lambda x: x["modified"], reverse=True)
        return log_files[:limit]
    except Exception as e:
        logger.error(f"Error getting log files: {e}")
        return []


async def read_log_file(filename: str, lines: int = 100) -> str:
    """
    读取日志文件内容
    """
    try:
        log_path = BASE_DIR / "logs" / filename
        if not log_path.exists() or not log_path.is_file():
            raise HTTPException(status_code=404, detail="Log file not found")

        # 读取最后N行
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            selected_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return ''.join(selected_lines)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading log file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """
    后台管理首页 - 仪表盘
    """
    stats = await get_system_stats()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "page_title": "仪表盘",
            "stats": stats,
            "current_path": "/admin/",
        }
    )


@router.get("/sessions", response_class=HTMLResponse)
async def admin_sessions(request: Request):
    """
    会话管理页面
    """
    return templates.TemplateResponse(
        "sessions.html",
        {
            "request": request,
            "page_title": "会话管理",
            "current_path": "/admin/sessions",
        }
    )


@router.get("/chat", response_class=HTMLResponse)
async def admin_chat(request: Request):
    """
    聊天界面
    """
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "page_title": "GTPlanner 聊天",
            "current_path": "/admin/chat",
        }
    )


@router.get("/logs", response_class=HTMLResponse)
async def admin_logs(request: Request):
    """
    日志查看页面
    """
    log_files = await get_log_files()
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "page_title": "日志查看",
            "current_path": "/admin/logs",
            "log_files": log_files,
        }
    )


@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(request: Request):
    """
    配置管理页面
    """
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "page_title": "配置管理",
            "current_path": "/admin/settings",
        }
    )


# API端点

@router.get("/api/stats")
async def api_stats():
    """
    API: 获取系统统计信息
    """
    return await get_system_stats()


@router.get("/api/logs")
async def api_logs():
    """
    API: 获取日志文件列表
    """
    return {"files": await get_log_files()}


@router.get("/api/logs/{filename}")
async def api_log_content(filename: str, lines: int = 100):
    """
    API: 获取日志文件内容
    """
    try:
        content = await read_log_file(filename, lines)
        return {"filename": filename, "content": content}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/logs/delete")
async def api_delete_log(filename: str):
    """
    API: 删除日志文件
    """
    try:
        log_path = BASE_DIR / "logs" / filename
        if not log_path.exists():
            raise HTTPException(status_code=404, detail="Log file not found")

        os.remove(log_path)
        logger.info(f"Deleted log file: {filename}")
        return {"success": True, "message": f"Log file {filename} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting log file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 会话管理 API ====================

@router.get("/api/sessions")
async def api_list_sessions(limit: int = 50, offset: int = 0, status: str = "active"):
    """
    API: 获取会话列表
    """
    try:
        with get_db_session() as db:
            sessions = list_sessions(db, limit=limit, offset=offset, status=status)
            sessions_dict = [session_to_dict(s) for s in sessions]
            return {
                "success": True,
                "sessions": sessions_dict,
                "count": len(sessions_dict)
            }
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/sessions/{session_id}")
async def api_get_session(session_id: str):
    """
    API: 获取单个会话详情
    """
    try:
        with get_db_session() as db:
            session = get_session_by_id(db, session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # 获取会话的消息
            messages = get_messages(db, session_id, limit=100)
            messages_dict = [message_to_dict(m) for m in messages]

            return {
                "success": True,
                "session": session_to_dict(session),
                "messages": messages_dict,
                "message_count": len(messages_dict)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/sessions")
async def api_create_session(request: CreateSessionRequest):
    """
    API: 创建新会话
    """
    try:
        with get_db_session() as db:
            session = db_create_session(
                db,
                title=request.title,
                project_stage=request.project_stage,
                metadata=request.metadata
            )

            logger.info(f"Created new session: {session.session_id} - {request.title}")
            return {
                "success": True,
                "session_id": session.session_id,
                "session": session_to_dict(session)
            }
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/sessions/{session_id}")
async def api_update_session(session_id: str, request: UpdateSessionRequest):
    """
    API: 更新会话信息
    """
    try:
        with get_db_session() as db:
            # 检查会话是否存在
            existing_session = get_session_by_id(db, session_id)
            if not existing_session:
                raise HTTPException(status_code=404, detail="Session not found")

            # 构建更新参数
            update_data = {}
            if request.title is not None:
                update_data["title"] = request.title
            if request.project_stage is not None:
                update_data["project_stage"] = request.project_stage
            if request.status is not None:
                update_data["status"] = request.status
            if request.metadata is not None:
                update_data["metadata"] = request.metadata

            # 执行更新
            success = db_update_session(db, session_id, **update_data)

            if success:
                # 获取更新后的会话信息
                session = get_session_by_id(db, session_id)
                logger.info(f"Updated session: {session_id}")
                return {
                    "success": True,
                    "session": session_to_dict(session)
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to update session")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/sessions/{session_id}")
async def api_delete_session(session_id: str):
    """
    API: 删除会话（软删除）
    """
    try:
        with get_db_session() as db:
            # 检查会话是否存在
            existing_session = get_session_by_id(db, session_id)
            if not existing_session:
                raise HTTPException(status_code=404, detail="Session not found")

            # 执行软删除
            success = db_delete_session(db, session_id)

            if success:
                logger.info(f"Deleted session: {session_id}")
                return {
                    "success": True,
                    "message": f"Session {session_id} deleted successfully"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to delete session")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/sessions/{session_id}/messages")
async def api_get_session_messages(session_id: str, limit: int = 100):
    """
    API: 获取会话的消息列表
    """
    try:
        with get_db_session() as db:
            # 检查会话是否存在
            session = get_session_by_id(db, session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # 获取消息
            messages = get_messages(db, session_id, limit=limit)
            messages_dict = [message_to_dict(m) for m in messages]

            return {
                "success": True,
                "session_id": session_id,
                "messages": messages_dict,
                "message_count": len(messages_dict)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
