"""
测试 document_edit_proposal 事件的完整发送流程
"""

import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gtplanner.agent.subflows.document_edit.nodes.document_edit_node import DocumentEditNode
from gtplanner.agent.streaming.event_helpers import emit_document_edit_proposal
from gtplanner.agent.streaming.stream_types import StreamEventType
import pytest


class MockStreamingSession:
    """模拟的 StreamingSession"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.emitted_events = []  # 存储所有发送的事件
    
    async def emit_event(self, event):
        """模拟发送事件"""
        print(f"📤 [MockStreamingSession] 收到事件: type={event.event_type}, session_id={event.session_id}")
        print(f"📤 [MockStreamingSession] 事件数据: {json.dumps(event.data, ensure_ascii=False, indent=2)[:500]}...")
        self.emitted_events.append(event)


def create_mock_response_with_edits():
    """创建模拟的 LLM 响应（包含编辑操作）"""
    response_json = {
        "edits": [
            {
                "search": "## 3.2 数据存储\n\n使用 PostgreSQL 作为主数据库。",
                "replace": "## 3.2 数据存储\n\n使用 PostgreSQL 作为主数据库，配合 Redis 作为缓存层。",
                "reason": "根据用户需求添加 Redis 缓存层说明"
            },
            {
                "search": "**性能优化**：\n- 待补充",
                "replace": "**性能优化**：\n- 热点数据使用 Redis 缓存\n- 缓存 TTL 设置为 1 小时\n- 使用 LRU 淘汰策略",
                "reason": "补充性能优化细节"
            }
        ],
        "summary": "在数据存储章节添加了 Redis 缓存层设计，并补充了性能优化策略"
    }
    
    mock_choice = Mock()
    mock_choice.message.content = json.dumps(response_json, ensure_ascii=False)
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    
    return mock_response


@pytest.mark.asyncio
async def test_emit_document_edit_proposal_direct():
    """测试场景1: 直接测试 emit_document_edit_proposal 函数"""
    print("\n" + "="*80)
    print("测试场景 1: 直接测试 emit_document_edit_proposal 函数")
    print("="*80)
    
    # 创建模拟的 streaming_session
    mock_session = MockStreamingSession("test_session_123")
    
    # 准备测试数据
    shared = {
        "streaming_session": mock_session
    }
    
    proposal_id = "edit_test_001"
    document_type = "design"
    document_filename = "design.md"
    edits = [
        {
            "search": "原始文本1",
            "replace": "修改后文本1",
            "reason": "修改原因1"
        },
        {
            "search": "原始文本2",
            "replace": "修改后文本2",
            "reason": "修改原因2"
        }
    ]
    summary = "测试文档编辑提案"
    preview_content = "修改后的完整文档内容..."
    
    # 调用函数
    await emit_document_edit_proposal(
        shared=shared,
        proposal_id=proposal_id,
        document_type=document_type,
        document_filename=document_filename,
        edits=edits,
        summary=summary,
        preview_content=preview_content
    )
    
    # 验证结果
    print(f"\n✅ 验证结果:")
    print(f"📊 发送的事件数量: {len(mock_session.emitted_events)}")
    
    assert len(mock_session.emitted_events) == 1, "应该发送1个事件"
    
    event = mock_session.emitted_events[0]
    print(f"📝 事件类型: {event.event_type}")
    print(f"🆔 会话ID: {event.session_id}")
    print(f"📋 提案ID: {event.data.get('proposal_id')}")
    print(f"📄 文档类型: {event.data.get('document_type')}")
    print(f"📝 编辑数量: {len(event.data.get('edits', []))}")
    print(f"📋 摘要: {event.data.get('summary')}")
    
    # 断言验证
    assert event.event_type == StreamEventType.DOCUMENT_EDIT_PROPOSAL
    assert event.session_id == "test_session_123"
    assert event.data["proposal_id"] == proposal_id
    assert event.data["document_type"] == document_type
    assert event.data["document_filename"] == document_filename
    assert len(event.data["edits"]) == 2
    assert event.data["summary"] == summary
    assert event.data["preview_content"] == preview_content
    
    # 验证每个 edit 的结构
    for i, edit in enumerate(event.data["edits"]):
        print(f"\n编辑 #{i+1}:")
        print(f"  - search: {edit['search'][:50]}...")
        print(f"  - replace: {edit['replace'][:50]}...")
        print(f"  - reason: {edit['reason']}")
        assert "search" in edit
        assert "replace" in edit
        assert "reason" in edit
    
    print("\n✅ 测试场景 1 通过！emit_document_edit_proposal 函数工作正常")


@pytest.mark.asyncio
async def test_emit_document_edit_proposal_without_session():
    """测试场景2: streaming_session 为 None 的情况"""
    print("\n" + "="*80)
    print("测试场景 2: streaming_session 为 None")
    print("="*80)
    
    # shared 中没有 streaming_session
    shared = {}
    
    edits = [
        {
            "search": "测试",
            "replace": "修改",
            "reason": "原因"
        }
    ]
    
    # 调用函数（应该不会抛出异常，只是不发送事件）
    await emit_document_edit_proposal(
        shared=shared,
        proposal_id="edit_test_002",
        document_type="design",
        document_filename="design.md",
        edits=edits,
        summary="测试"
    )
    
    print("✅ 测试场景 2 通过！正确处理了 streaming_session 为 None 的情况")


@pytest.mark.asyncio
async def test_document_edit_node_full_flow():
    """测试场景3: DocumentEditNode 完整流程（包括事件发送）"""
    print("\n" + "="*80)
    print("测试场景 3: DocumentEditNode 完整流程（包括 post_async 事件发送）")
    print("="*80)
    
    node = DocumentEditNode()
    
    # 创建模拟的 streaming_session
    mock_session = MockStreamingSession("test_session_456")
    
    # 准备文档内容
    document_content = """# 系统设计文档

## 3.2 数据存储

使用 PostgreSQL 作为主数据库。

**性能优化**：
- 待补充

## 其他章节
...
"""
    
    # 准备 shared（包含 streaming_session）
    shared = {
        "streaming_session": mock_session,
        "document_type": "design",
        "edit_instructions": "在数据存储章节添加 Redis 缓存层说明，并补充性能优化细节",
        "generated_documents": [
            {
                "type": "design",
                "content": document_content,
                "filename": "design.md"
            }
        ],
        "language": "zh"
    }
    
    # 执行 prep_async
    prep_result = await node.prep_async(shared)
    
    print(f"\n📝 prep_async 结果:")
    print(f"  - success: {prep_result.get('success')}")
    print(f"  - document_type: {prep_result.get('document_type')}")
    print(f"  - document_filename: {prep_result.get('document_filename')}")
    
    assert prep_result.get("success") == True
    
    # Mock OpenAI client 并执行 exec_async
    mock_response = create_mock_response_with_edits()
    
    with patch.object(node.openai_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        
        exec_result = await node.exec_async(prep_result)
        
        print(f"\n🤖 exec_async 结果:")
        print(f"  - success: {exec_result.get('success')}")
        print(f"  - proposal_id: {exec_result.get('proposal_id')}")
        print(f"  - edits 数量: {len(exec_result.get('edits', []))}")
        print(f"  - summary: {exec_result.get('summary')}")
        
        assert exec_result.get("success") == True
        assert exec_result.get("proposal_id") is not None
        assert len(exec_result.get("edits", [])) == 2
    
    # 执行 post_async（这里应该发送事件）
    print(f"\n📤 执行 post_async，应该发送 document_edit_proposal 事件...")
    
    post_result = await node.post_async(shared, prep_result, exec_result)
    
    print(f"\n✅ post_async 结果: {post_result}")
    assert post_result == "edit_proposal_generated"
    
    # 验证事件是否被发送
    print(f"\n📊 验证发送的事件:")
    print(f"  - 事件总数: {len(mock_session.emitted_events)}")
    
    # 找到 document_edit_proposal 事件
    proposal_events = [
        e for e in mock_session.emitted_events 
        if e.event_type == StreamEventType.DOCUMENT_EDIT_PROPOSAL
    ]
    
    print(f"  - document_edit_proposal 事件数: {len(proposal_events)}")
    
    assert len(proposal_events) >= 1, "应该至少发送1个 document_edit_proposal 事件"
    
    proposal_event = proposal_events[0]
    print(f"\n📝 提案事件详情:")
    print(f"  - event_type: {proposal_event.event_type}")
    print(f"  - session_id: {proposal_event.session_id}")
    print(f"  - proposal_id: {proposal_event.data.get('proposal_id')}")
    print(f"  - document_type: {proposal_event.data.get('document_type')}")
    print(f"  - edits 数量: {len(proposal_event.data.get('edits', []))}")
    print(f"  - summary: {proposal_event.data.get('summary')[:100]}...")
    
    # 验证事件数据结构
    assert proposal_event.event_type == StreamEventType.DOCUMENT_EDIT_PROPOSAL
    assert proposal_event.session_id == "test_session_456"
    assert proposal_event.data["proposal_id"] == exec_result["proposal_id"]
    assert proposal_event.data["document_type"] == "design"
    assert proposal_event.data["document_filename"] == "design.md"
    assert len(proposal_event.data["edits"]) == 2
    
    # 验证编辑内容
    edit1 = proposal_event.data["edits"][0]
    assert "search" in edit1
    assert "replace" in edit1
    assert "reason" in edit1
    assert "Redis" in edit1["replace"]  # 应该包含 Redis 相关内容
    
    print("\n✅ 测试场景 3 通过！DocumentEditNode 完整流程（包括事件发送）正常工作")


@pytest.mark.asyncio
async def test_event_serialization():
    """测试场景4: 验证事件可以正确序列化为 SSE 格式"""
    print("\n" + "="*80)
    print("测试场景 4: 验证事件序列化为 SSE 格式")
    print("="*80)
    
    # 创建模拟的 streaming_session
    mock_session = MockStreamingSession("test_session_789")
    
    shared = {
        "streaming_session": mock_session
    }
    
    edits = [
        {
            "search": "原文",
            "replace": "新文",
            "reason": "测试"
        }
    ]
    
    await emit_document_edit_proposal(
        shared=shared,
        proposal_id="edit_test_003",
        document_type="database_design",
        document_filename="database_design.md",
        edits=edits,
        summary="测试序列化"
    )
    
    # 获取事件
    event = mock_session.emitted_events[0]
    
    # 测试序列化方法
    print(f"\n🔄 测试序列化:")
    
    # to_dict
    event_dict = event.to_dict()
    print(f"✅ to_dict() 成功")
    assert "event_type" in event_dict
    assert "data" in event_dict
    assert event_dict["event_type"] == "document_edit_proposal"
    
    # to_json
    event_json = event.to_json()
    print(f"✅ to_json() 成功")
    parsed = json.loads(event_json)
    assert parsed["event_type"] == "document_edit_proposal"
    
    # to_sse_format
    sse_format = event.to_sse_format()
    print(f"✅ to_sse_format() 成功")
    print(f"\nSSE 格式预览:")
    print(sse_format[:300] + "...")
    
    assert sse_format.startswith("event: document_edit_proposal\n")
    assert "data: {" in sse_format
    assert sse_format.endswith("\n\n")
    
    print("\n✅ 测试场景 4 通过！事件序列化正常工作")


async def main():
    """运行所有测试"""
    print("\n" + "🧪" * 40)
    print("开始测试 document_edit_proposal 事件发送流程")
    print("🧪" * 40)
    
    tests = [
        ("直接测试 emit_document_edit_proposal", test_emit_document_edit_proposal_direct),
        ("streaming_session 为 None", test_emit_document_edit_proposal_without_session),
        ("DocumentEditNode 完整流程", test_document_edit_node_full_flow),
        ("事件序列化", test_event_serialization),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ 测试失败: {test_name}")
            print(f"错误: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n❌ 测试出错: {test_name}")
            print(f"异常: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print(f"测试完成！通过: {passed}/{len(tests)}, 失败: {failed}/{len(tests)}")
    print("="*80)
    
    if failed == 0:
        print("\n✅ 所有测试通过！document_edit_proposal 事件发送流程正常工作！")
        print("\n🎯 结论:")
        print("  1. emit_document_edit_proposal 函数工作正常")
        print("  2. DocumentEditNode 的 post_async 正确发送事件")
        print("  3. 事件数据结构正确")
        print("  4. 事件序列化为 SSE 格式正常")
        print("\n如果前端没有收到事件，问题可能在于:")
        print("  ❓ Next.js API route 没有正确转发 SSE 事件")
        print("  ❓ 前端 SSE 客户端事件解析有问题")
        print("  ❓ 事件类型名称不匹配")
    else:
        print(f"\n❌ 有 {failed} 个测试失败，需要修复后端事件发送逻辑。")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

