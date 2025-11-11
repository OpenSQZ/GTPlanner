"""
集成测试：完整测试 edit_document 工具从调用到事件发送的整个流程
"""

import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gtplanner.agent.function_calling.agent_tools import _execute_edit_document
from gtplanner.agent.streaming.stream_types import StreamEventType


class MockStreamingSession:
    """模拟的 StreamingSession"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.emitted_events = []
    
    async def emit_event(self, event):
        """模拟发送事件"""
        print(f"📤 [MockStreamingSession.emit_event] 收到事件: type={event.event_type.value if hasattr(event.event_type, 'value') else event.event_type}")
        self.emitted_events.append(event)


def create_mock_llm_response():
    """创建模拟的 LLM 响应"""
    response_json = {
        "edits": [
            {
                "search": "  `pdf_source_url` VARCHAR(500) DEFAULT NULL COMMENT '数据来源PDF文件URL',\n  `data_date` DATE DEFAULT NULL COMMENT '数据发布日期',",
                "replace": "  `pdf_source_url` VARCHAR(500) DEFAULT NULL COMMENT '数据来源PDF文件URL',\n  `pdf_s3_path` VARCHAR(500) DEFAULT NULL COMMENT 'PDF文件在S3中的路径',\n  `data_date` DATE DEFAULT NULL COMMENT '数据发布日期',",
                "reason": "在 pdf_source_url 字段后添加 pdf_s3_path 字段"
            }
        ],
        "summary": "在 overdue_acceptors 表结构中添加 pdf_s3_path 字段"
    }
    
    mock_choice = Mock()
    mock_choice.message.content = json.dumps(response_json, ensure_ascii=False)
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    
    return mock_response


async def test_complete_integration():
    """完整的集成测试"""
    print("\n" + "="*80)
    print("集成测试：edit_document 工具完整流程")
    print("="*80)
    
    # 1. 创建模拟的 streaming_session
    mock_session = MockStreamingSession("test_session_integration")
    print(f"\n✅ 步骤 1: 创建 MockStreamingSession (session_id={mock_session.session_id})")
    
    # 2. 准备文档内容
    document_content = """# 数据库表结构设计

## overdue_acceptors 表

```sql
CREATE TABLE `overdue_acceptors` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `acceptor_name` VARCHAR(255) NOT NULL COMMENT '承兑人名称',
  `pdf_source_url` VARCHAR(500) DEFAULT NULL COMMENT '数据来源PDF文件URL',
  `data_date` DATE DEFAULT NULL COMMENT '数据发布日期',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
"""
    
    # 3. 准备 shared 状态（模拟真实的运行环境）
    shared = {
        "streaming_session": mock_session,  # 关键：传入 streaming_session
        "generated_documents": [
            {
                "type": "database_design",
                "content": document_content,
                "filename": "database_design.md"
            }
        ],
        "language": "zh"
    }
    print(f"✅ 步骤 2: 准备 shared 状态 (streaming_session={shared.get('streaming_session') is not None})")
    
    # 4. 准备工具参数
    arguments = {
        "document_type": "database_design",
        "edit_instructions": "在 overdue_acceptors 表中添加 pdf_s3_path 字段"
    }
    print(f"✅ 步骤 3: 准备工具参数")
    
    # 5. Mock OpenAI 客户端
    from gtplanner.utils.openai_client import get_openai_client
    mock_llm_response = create_mock_llm_response()
    
    print(f"\n✅ 步骤 4: 准备 Mock LLM 响应")
    
    # 6. 执行工具（模拟 LLM 调用）
    print(f"\n🚀 步骤 5: 执行 _execute_edit_document...")
    
    with patch('gtplanner.agent.subflows.document_edit.nodes.document_edit_node.get_openai_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.chat_completion = AsyncMock(return_value=mock_llm_response)
        mock_get_client.return_value = mock_client
        
        result = await _execute_edit_document(arguments, shared)
    
    # 7. 验证工具返回值
    print(f"\n✅ 步骤 6: 验证工具返回值")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:500] + "...")
    
    assert result["success"] == True, "工具应该执行成功"
    assert "proposal_id" in result
    assert "edits" in result
    assert len(result["edits"]) > 0
    
    # 8. 验证事件是否被发送
    print(f"\n✅ 步骤 7: 验证事件发送")
    print(f"📊 总共发送的事件数: {len(mock_session.emitted_events)}")
    
    # 打印所有事件类型
    for i, event in enumerate(mock_session.emitted_events):
        event_type = event.event_type.value if hasattr(event.event_type, 'value') else event.event_type
        print(f"  事件 #{i+1}: {event_type}")
    
    # 查找 document_edit_proposal 事件
    proposal_events = [
        e for e in mock_session.emitted_events 
        if (hasattr(e.event_type, 'value') and e.event_type.value == "document_edit_proposal") or
           (e.event_type == StreamEventType.DOCUMENT_EDIT_PROPOSAL)
    ]
    
    print(f"\n🔍 查找 document_edit_proposal 事件:")
    print(f"  找到的数量: {len(proposal_events)}")
    
    if len(proposal_events) == 0:
        print("\n❌ 问题诊断:")
        print("  - document_edit_proposal 事件没有被发送！")
        print("  - 可能原因：")
        print("    1. DocumentEditNode.post_async 没有被执行")
        print("    2. emit_document_edit_proposal 没有被调用")
        print("    3. streaming_session 在某个环节丢失了")
        
        # 检查 shared 中是否还有 streaming_session
        print(f"\n  检查 shared 状态:")
        print(f"    - streaming_session 还存在: {shared.get('streaming_session') is not None}")
        print(f"    - pending_document_edits: {list(shared.get('pending_document_edits', {}).keys())}")
        
        raise AssertionError("document_edit_proposal 事件没有被发送！")
    
    # 验证事件内容
    proposal_event = proposal_events[0]
    print(f"\n✅ 找到 document_edit_proposal 事件！")
    print(f"  - session_id: {proposal_event.session_id}")
    print(f"  - proposal_id: {proposal_event.data.get('proposal_id')}")
    print(f"  - document_type: {proposal_event.data.get('document_type')}")
    print(f"  - edits 数量: {len(proposal_event.data.get('edits', []))}")
    
    assert proposal_event.session_id == "test_session_integration"
    assert "proposal_id" in proposal_event.data
    assert "edits" in proposal_event.data
    assert len(proposal_event.data["edits"]) > 0
    
    print(f"\n✅ 所有验证通过！")
    print(f"\n🎯 结论:")
    print(f"  1. edit_document 工具成功执行")
    print(f"  2. document_edit_proposal 事件成功发送")
    print(f"  3. 事件内容正确")
    print(f"  4. 如果实际运行时前端没收到，问题可能在：")
    print(f"     - SSE 传输层（Next.js API route）")
    print(f"     - 前端事件解析")
    print(f"     - 或者实际运行时 streaming_session 为 None")


async def main():
    """运行测试"""
    print("\n" + "🧪" * 40)
    print("edit_document 工具集成测试")
    print("🧪" * 40)
    
    try:
        await test_complete_integration()
        
        print("\n" + "="*80)
        print("✅ 集成测试通过！")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

