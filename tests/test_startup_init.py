"""应用启动初始化流程测试"""

import pytest

from agent.utils import startup_init


@pytest.mark.asyncio
async def test_initialize_application_success(monkeypatch):
    """向量服务可用时，初始化应成功并返回索引信息"""

    class DummyResponse:
        status_code = 200

    async def fake_ensure_tool_index(*args, **kwargs):
        return "document_gtplanner_tools"

    def fake_get_index_info():
        return {"index_created": True}

    def fake_vector_config():
        return {
            "base_url": "http://vector-service",
            "tools_index_name": "document_gtplanner_tools",
            "vector_field": "combined_text",
            "timeout": 5
        }

    class DummyRequests:
        @staticmethod
        def get(url, timeout):
            return DummyResponse()

    monkeypatch.setattr(startup_init, "ensure_tool_index", fake_ensure_tool_index)
    monkeypatch.setattr(startup_init.tool_index_manager, "get_index_info", fake_get_index_info)
    monkeypatch.setattr(startup_init, "get_vector_service_config", fake_vector_config)
    monkeypatch.setattr(startup_init, "requests", DummyRequests)

    result = await startup_init.initialize_application(tools_dir="tools", preload_index=True)

    assert result["success"] is True
    assert result["components"]["vector_service"]["available"] is True
    assert result["components"]["tool_index"]["success"] is True


@pytest.mark.asyncio
async def test_initialize_application_handles_vector_service_failure(monkeypatch):
    """向量服务不可用时，初始化应返回失败状态"""

    def fake_vector_config():
        return {
            "base_url": "http://vector-service",
            "tools_index_name": "document_gtplanner_tools",
            "vector_field": "combined_text",
            "timeout": 5
        }

    class DummyRequests:
        @staticmethod
        def get(url, timeout):
            raise RuntimeError("connection refused")

    monkeypatch.setattr(startup_init, "get_vector_service_config", fake_vector_config)
    monkeypatch.setattr(startup_init, "requests", DummyRequests)

    result = await startup_init.initialize_application(tools_dir="tools", preload_index=True)

    assert result["success"] is False
    assert any("向量服务不可用" in err for err in result["errors"])
    vector_component = result["components"].get("vector_service", {})
    assert vector_component.get("available") is False

