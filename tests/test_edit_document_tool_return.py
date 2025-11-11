"""
测试 edit_document 工具的返回值格式
"""

import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gtplanner.agent.function_calling.agent_tools import _execute_edit_document


class MockStreamingSession:
    """模拟的 StreamingSession"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.emitted_events = []
    
    async def emit_event(self, event):
        """模拟发送事件"""
        self.emitted_events.append(event)


async def test_tool_return_value():
    """测试 edit_document 工具的返回值格式"""
    print("\n" + "="*80)
    print("测试 edit_document 工具返回值格式")
    print("="*80)
    
    # 创建模拟的 streaming_session
    mock_session = MockStreamingSession("test_session_123")
    
    # 准备 shared 状态
    shared = {
        "streaming_session": mock_session,
        "generated_documents": [
            {
                "type": "database_design",
                "content": """# 数据库表结构设计

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
""",
                "filename": "database_design.md"
            }
        ],
        "language": "zh"
    }
    
    # 准备工具参数
    arguments = {
        "document_type": "database_design",
        "edit_instructions": "在 overdue_acceptors 表中添加 pdf_s3_path 字段，类型 VARCHAR(500)，位于 pdf_source_url 之后"
    }
    
    # Mock DocumentEditFlow
    from gtplanner.agent.subflows.document_edit.flows.document_edit_flow import DocumentEditFlow
    
    with patch.object(DocumentEditFlow, 'run_async', new_callable=AsyncMock) as mock_run:
        # 模拟 flow 执行成功，并设置 flow_shared
        async def mock_flow_execution(flow_shared):
            # 模拟 node 生成的编辑提案
            proposal_id = "edit_abc123"
            flow_shared["edit_proposal_id"] = proposal_id
            flow_shared["pending_document_edits"] = {
                proposal_id: {
                    "document_type": "database_design",
                    "document_filename": "database_design.md",
                    "edits": [
                        {
                            "search": "  `pdf_source_url` VARCHAR(500) DEFAULT NULL COMMENT '数据来源PDF文件URL',\n  `data_date` DATE DEFAULT NULL COMMENT '数据发布日期',",
                            "replace": "  `pdf_source_url` VARCHAR(500) DEFAULT NULL COMMENT '数据来源PDF文件URL',\n  `pdf_s3_path` VARCHAR(500) DEFAULT NULL COMMENT 'PDF文件在S3中的路径',\n  `data_date` DATE DEFAULT NULL COMMENT '数据发布日期',",
                            "reason": "在 pdf_source_url 字段后添加 pdf_s3_path 字段"
                        },
                        {
                            "search": "## overdue_acceptors 表",
                            "replace": "## overdue_acceptors 表\n\n**字段说明**：\n- `pdf_s3_path`: 存储PDF文件在S3中的路径，用于快速访问",
                            "reason": "添加新增字段的说明文档"
                        }
                    ],
                    "summary": "在 overdue_acceptors 表结构中添加 pdf_s3_path 字段，用于存储PDF文件在S3中的路径",
                    "status": "pending",
                    "created_at": "test_timestamp"
                }
            }
            return "edit_proposal_generated"
        
        mock_run.side_effect = mock_flow_execution
        
        # 执行工具
        result = await _execute_edit_document(arguments, shared)
    
    # 验证返回值
    print(f"\n✅ 工具执行结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 基本验证
    assert result["success"] == True, "工具应该执行成功"
    assert "proposal_id" in result, "应该包含 proposal_id"
    assert "edits" in result, "应该包含 edits 列表"
    assert "summary" in result, "应该包含 summary"
    assert "document_type" in result, "应该包含 document_type"
    assert "document_filename" in result, "应该包含 document_filename"
    
    # 详细验证
    print(f"\n📋 详细验证:")
    print(f"  ✅ success: {result['success']}")
    print(f"  ✅ proposal_id: {result['proposal_id']}")
    print(f"  ✅ document_type: {result['document_type']}")
    print(f"  ✅ document_filename: {result['document_filename']}")
    print(f"  ✅ edits 数量: {len(result['edits'])}")
    print(f"  ✅ summary: {result['summary'][:100]}...")
    
    # 验证编辑内容
    print(f"\n📝 编辑内容:")
    for i, edit in enumerate(result['edits']):
        print(f"\n  编辑 #{i+1}:")
        print(f"    - search (前50字符): {edit['search'][:50]}...")
        print(f"    - replace (前50字符): {edit['replace'][:50]}...")
        print(f"    - reason: {edit['reason']}")
        
        assert "search" in edit, f"编辑 #{i+1} 应该包含 search 字段"
        assert "replace" in edit, f"编辑 #{i+1} 应该包含 replace 字段"
        assert "reason" in edit, f"编辑 #{i+1} 应该包含 reason 字段"
    
    # 验证 LLM 能够理解返回的内容
    print(f"\n🤖 LLM 可见信息验证:")
    print(f"  ✅ LLM 可以看到 {len(result['edits'])} 个具体的编辑操作")
    print(f"  ✅ LLM 可以看到每个编辑的原文 (search)")
    print(f"  ✅ LLM 可以看到每个编辑的新文 (replace)")
    print(f"  ✅ LLM 可以看到每个编辑的原因 (reason)")
    print(f"  ✅ LLM 可以向用户解释具体做了什么修改")
    
    print("\n✅ 测试通过！edit_document 工具返回完整的编辑内容")
    return result


async def test_tool_return_value_comparison():
    """对比修改前后的返回值"""
    print("\n" + "="*80)
    print("对比修改前后的工具返回值")
    print("="*80)
    
    print("\n❌ 修改前的返回值（信息不足）:")
    old_return = {
        "success": True,
        "message": "✅ 文档编辑提案已生成，等待用户确认",
        "proposal_id": "edit_93d952f3",
        "tool_name": "edit_document"
    }
    print(json.dumps(old_return, ensure_ascii=False, indent=2))
    
    print("\n  问题:")
    print("  ❌ LLM 看不到具体做了什么修改")
    print("  ❌ LLM 无法向用户解释编辑内容")
    print("  ❌ 只有一个 proposal_id，没有实际信息")
    
    print("\n" + "-"*80)
    
    print("\n✅ 修改后的返回值（信息完整）:")
    new_return = {
        "success": True,
        "message": "✅ 文档编辑提案已生成，等待用户确认",
        "proposal_id": "edit_93d952f3",
        "document_type": "database_design",
        "document_filename": "database_design.md",
        "edits": [
            {
                "search": "  `pdf_source_url` VARCHAR(500) DEFAULT NULL COMMENT '数据来源PDF文件URL',\n  `data_date` DATE DEFAULT NULL COMMENT '数据发布日期',",
                "replace": "  `pdf_source_url` VARCHAR(500) DEFAULT NULL COMMENT '数据来源PDF文件URL',\n  `pdf_s3_path` VARCHAR(500) DEFAULT NULL COMMENT 'PDF文件在S3中的路径',\n  `data_date` DATE DEFAULT NULL COMMENT '数据发布日期',",
                "reason": "在 pdf_source_url 字段后添加 pdf_s3_path 字段"
            },
            {
                "search": "## overdue_acceptors 表",
                "replace": "## overdue_acceptors 表\n\n**字段说明**：\n- `pdf_s3_path`: 存储PDF文件在S3中的路径",
                "reason": "添加新增字段的说明文档"
            }
        ],
        "summary": "在 overdue_acceptors 表结构中添加 pdf_s3_path 字段，用于存储PDF文件在S3中的路径",
        "tool_name": "edit_document"
    }
    print(json.dumps(new_return, ensure_ascii=False, indent=2))
    
    print("\n  优势:")
    print("  ✅ LLM 可以看到具体的编辑操作")
    print("  ✅ LLM 可以向用户解释每个修改")
    print("  ✅ LLM 可以总结编辑内容")
    print("  ✅ 类似 search_replace 工具的使用方式")
    
    print("\n✅ 对比完成！新的返回值格式更加完整和有用")


async def main():
    """运行所有测试"""
    print("\n" + "🧪" * 40)
    print("测试 edit_document 工具返回值")
    print("🧪" * 40)
    
    try:
        # 测试 1: 实际工具返回值
        result = await test_tool_return_value()
        
        # 测试 2: 对比说明
        await test_tool_return_value_comparison()
        
        print("\n" + "="*80)
        print("✅ 所有测试通过！edit_document 工具现在返回完整的编辑内容")
        print("="*80)
        
        print("\n🎯 总结:")
        print("  1. 工具返回值包含完整的 edits 列表")
        print("  2. 每个 edit 包含 search、replace、reason")
        print("  3. 还包含 summary、document_type、document_filename")
        print("  4. LLM 可以向用户详细解释做了什么修改")
        print("  5. 用户体验：LLM 会说 '我对数据库设计文档做了以下修改：...'")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

