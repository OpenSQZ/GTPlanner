"""SSE API 与 AgentContext 校验测试"""

import asyncio
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

import fastapi_main
from agent.api.agent_api import SSEGTPlanner
from agent.context_types import MessageRole


def _build_message(role: MessageRole, content: str) -> dict:
    """构造带时间戳的消息字典"""
    return {
        "role": role.value,
        "content": content,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metadata": {}
    }


def test_validate_agent_context_success():
    """验证合法 AgentContext 能正确解析"""
    planner = SSEGTPlanner(verbose=False)
    context_dict = {
        "session_id": "test-session",
        "dialogue_history": [
            _build_message(MessageRole.USER, "帮我设计一个日程提醒系统"),
            _build_message(MessageRole.ASSISTANT, "好的，我来规划一下")
        ],
        "tool_execution_results": {},
        "session_metadata": {"language": "zh"},
        "last_updated": None,
        "is_compressed": False
    }

    context = planner._validate_and_parse_agent_context(context_dict)

    assert context.session_id == "test-session"
    assert len(context.dialogue_history) == 2
    assert context.dialogue_history[0].role == MessageRole.USER
    assert context.dialogue_history[1].role == MessageRole.ASSISTANT


def test_validate_agent_context_requires_session_id():
    """session_id 为空时应抛出 ValueError"""
    planner = SSEGTPlanner(verbose=False)
    context_dict = {
        "session_id": "",
        "dialogue_history": [
            _build_message(MessageRole.USER, "需求")
        ],
        "tool_execution_results": {},
        "session_metadata": {}
    }

    with pytest.raises(ValueError) as exc:
        planner._validate_and_parse_agent_context(context_dict)

    assert "session_id 必须是非空字符串" in str(exc.value)


def test_validate_agent_context_requires_user_message():
    """对话历史中缺少用户消息时应抛出异常"""
    planner = SSEGTPlanner(verbose=False)
    context_dict = {
        "session_id": "test-session",
        "dialogue_history": [
            _build_message(MessageRole.ASSISTANT, "我来帮你")
        ],
        "tool_execution_results": {},
        "session_metadata": {}
    }

    with pytest.raises(ValueError) as exc:
        planner._validate_and_parse_agent_context(context_dict)

    assert "必须包含至少一条用户消息" in str(exc.value)


@pytest.fixture
def fastapi_client(monkeypatch):
    """提供跳过启动初始化的 FastAPI TestClient"""

    async def fake_initialize_application(*args, **kwargs):
        return {"success": True, "components": {}, "errors": []}

    monkeypatch.setattr(fastapi_main, "initialize_application", fake_initialize_application)

    with TestClient(fastapi_main.app) as client:
        yield client


def test_chat_agent_requires_non_empty_history(fastapi_client):
    """API 在 dialogue_history 为空时返回 400"""
    payload = {
        "session_id": "test-session",
        "dialogue_history": [],
        "tool_execution_results": {},
        "session_metadata": {}
    }

    response = fastapi_client.post("/api/chat/agent", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "dialogue_history cannot be empty"


def test_chat_agent_requires_session_id(fastapi_client):
    """API 在 session_id 为空时返回 400"""
    payload = {
        "session_id": " ",
        "dialogue_history": [
            {
                "role": "user",
                "content": "生成一个部署方案",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "metadata": {}
            }
        ],
        "tool_execution_results": {},
        "session_metadata": {}
    }

    response = fastapi_client.post("/api/chat/agent", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "session_id is required"

