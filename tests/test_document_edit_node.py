"""
测试 DocumentEditNode 的 LLM 调用和 JSON 解析
"""

import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import sys
import os
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gtplanner.agent.subflows.document_edit.nodes.document_edit_node import DocumentEditNode


def create_mock_response(content: str):
    """创建模拟的 OpenAI 响应"""
    mock_choice = Mock()
    mock_choice.message.content = content
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    
    return mock_response


@pytest.mark.asyncio
async def test_normal_json():
    """测试场景1: 正常的 JSON 响应"""
    print("\n" + "="*80)
    print("测试场景 1: 正常的 JSON 响应")
    print("="*80)
    
    node = DocumentEditNode()
    
    # 模拟 LLM 返回正常的 JSON
    normal_json = {
        "edits": [
            {
                "search": "### 3.2 数据存储\n\n使用 PostgreSQL 作为主数据库。",
                "replace": "### 3.2 数据存储\n\n使用 PostgreSQL 作为主数据库，配合 Redis 作为缓存层。",
                "reason": "添加 Redis 缓存层"
            }
        ],
        "summary": "在数据存储章节添加了 Redis 缓存层"
    }
    
    mock_response = create_mock_response(json.dumps(normal_json, ensure_ascii=False))
    
    # 准备测试数据
    prep_result = {
        "success": True,
        "document_type": "design",
        "document_content": "### 3.2 数据存储\n\n使用 PostgreSQL 作为主数据库。\n\n其他内容...",
        "document_filename": "design.md",
        "edit_instructions": "添加 Redis 缓存层说明",
        "streaming_session": None,
        "language": "zh"
    }
    
    # Mock OpenAI client
    with patch.object(node.openai_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        
        result = await node.exec_async(prep_result)
        
        print(f"✅ 测试结果: {result.get('success')}")
        print(f"📝 生成的编辑数量: {len(result.get('edits', []))}")
        print(f"📋 摘要: {result.get('summary')}")
        
        assert result["success"] == True
        assert len(result["edits"]) == 1
        print("\n✅ 测试场景 1 通过！")


@pytest.mark.asyncio
async def test_markdown_wrapped_json():
    """测试场景2: Markdown 代码块包裹的 JSON"""
    print("\n" + "="*80)
    print("测试场景 2: Markdown 代码块包裹的 JSON (```json)")
    print("="*80)
    
    node = DocumentEditNode()
    
    # 模拟 LLM 返回 Markdown 包裹的 JSON
    normal_json = {
        "edits": [
            {
                "search": "### 测试",
                "replace": "### 测试修改",
                "reason": "测试修改"
            }
        ],
        "summary": "测试修改"
    }
    
    # 用 ```json 包裹
    wrapped_content = f"```json\n{json.dumps(normal_json, ensure_ascii=False, indent=2)}\n```"
    mock_response = create_mock_response(wrapped_content)
    
    prep_result = {
        "success": True,
        "document_type": "design",
        "document_content": "### 测试\n\n内容...",
        "document_filename": "design.md",
        "edit_instructions": "修改标题",
        "streaming_session": None,
        "language": "zh"
    }
    
    with patch.object(node.openai_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        
        result = await node.exec_async(prep_result)
        
        print(f"✅ 测试结果: {result.get('success')}")
        print(f"📝 生成的编辑数量: {len(result.get('edits', []))}")
        
        assert result["success"] == True
        assert len(result["edits"]) == 1
        print("\n✅ 测试场景 2 通过！")


@pytest.mark.asyncio
async def test_plain_markdown_wrapped():
    """测试场景3: 普通 Markdown 代码块包裹 (```)"""
    print("\n" + "="*80)
    print("测试场景 3: 普通 Markdown 代码块包裹 (```)")
    print("="*80)
    
    node = DocumentEditNode()
    
    normal_json = {
        "edits": [
            {
                "search": "测试内容",
                "replace": "修改后的内容",
                "reason": "测试"
            }
        ],
        "summary": "测试摘要"
    }
    
    # 用普通 ``` 包裹
    wrapped_content = f"```\n{json.dumps(normal_json, ensure_ascii=False)}\n```"
    mock_response = create_mock_response(wrapped_content)
    
    prep_result = {
        "success": True,
        "document_type": "design",
        "document_content": "测试内容\n\n更多内容...",
        "document_filename": "design.md",
        "edit_instructions": "修改内容",
        "streaming_session": None,
        "language": "zh"
    }
    
    with patch.object(node.openai_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        
        result = await node.exec_async(prep_result)
        
        print(f"✅ 测试结果: {result.get('success')}")
        print(f"📝 生成的编辑数量: {len(result.get('edits', []))}")
        
        assert result["success"] == True
        assert len(result["edits"]) == 1
        print("\n✅ 测试场景 3 通过！")


@pytest.mark.asyncio
async def test_empty_edits():
    """测试场景4: 空的编辑列表"""
    print("\n" + "="*80)
    print("测试场景 4: LLM 返回空的编辑列表")
    print("="*80)
    
    node = DocumentEditNode()
    
    empty_json = {
        "edits": [],
        "summary": "没有需要修改的内容"
    }
    
    mock_response = create_mock_response(json.dumps(empty_json))
    
    prep_result = {
        "success": True,
        "document_type": "design",
        "document_content": "测试内容",
        "document_filename": "design.md",
        "edit_instructions": "修改",
        "streaming_session": None,
        "language": "zh"
    }
    
    with patch.object(node.openai_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        
        result = await node.exec_async(prep_result)
        
        print(f"✅ 测试结果: {result.get('success')}")
        print(f"❌ 错误信息: {result.get('error')}")
        
        assert result["success"] == False
        assert "did not generate any edits" in result["error"]
        print("\n✅ 测试场景 4 通过（正确处理空结果）！")


@pytest.mark.asyncio
async def test_invalid_json():
    """测试场景5: 无效的 JSON"""
    print("\n" + "="*80)
    print("测试场景 5: LLM 返回无效的 JSON")
    print("="*80)
    
    node = DocumentEditNode()
    
    # 返回无效的 JSON
    invalid_content = "这不是一个有效的 JSON 字符串"
    mock_response = create_mock_response(invalid_content)
    
    prep_result = {
        "success": True,
        "document_type": "design",
        "document_content": "测试内容",
        "document_filename": "design.md",
        "edit_instructions": "修改",
        "streaming_session": None,
        "language": "zh"
    }
    
    with patch.object(node.openai_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        
        result = await node.exec_async(prep_result)
        
        print(f"✅ 测试结果: {result.get('success')}")
        print(f"❌ 错误信息: {result.get('error')}")
        print(f"📄 原始响应: {result.get('raw_response', 'N/A')[:100]}")
        
        assert result["success"] == False
        assert "Failed to parse LLM response" in result["error"]
        assert "raw_response" in result  # 应该包含原始响应
        print("\n✅ 测试场景 5 通过（正确处理解析错误）！")


@pytest.mark.asyncio
async def test_validation_failure():
    """测试场景6: 编辑验证失败（search 文本不存在）"""
    print("\n" + "="*80)
    print("测试场景 6: 编辑验证失败（search 文本在文档中不存在）")
    print("="*80)
    
    node = DocumentEditNode()
    
    # LLM 返回的 search 文本不在原文档中
    invalid_edit_json = {
        "edits": [
            {
                "search": "这段文本不存在于文档中",
                "replace": "替换内容",
                "reason": "测试"
            }
        ],
        "summary": "测试编辑"
    }
    
    mock_response = create_mock_response(json.dumps(invalid_edit_json, ensure_ascii=False))
    
    prep_result = {
        "success": True,
        "document_type": "design",
        "document_content": "### 实际的文档内容\n\n这里是真实的内容。",
        "document_filename": "design.md",
        "edit_instructions": "修改",
        "streaming_session": None,
        "language": "zh"
    }
    
    with patch.object(node.openai_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        
        result = await node.exec_async(prep_result)
        
        print(f"✅ 测试结果: {result.get('success')}")
        print(f"❌ 错误信息: {result.get('error')}")
        print(f"📋 验证错误: {result.get('validation_errors', [])}")
        
        assert result["success"] == False
        assert "Edit validation failed" in result["error"]
        assert len(result.get("validation_errors", [])) > 0
        print("\n✅ 测试场景 6 通过（正确处理验证错误）！")


async def main():
    """运行所有测试"""
    print("\n" + "🧪" * 40)
    print("开始测试 DocumentEditNode 的 LLM 调用和 JSON 解析")
    print("🧪" * 40)
    
    tests = [
        ("正常 JSON", test_normal_json),
        ("Markdown ```json 包裹", test_markdown_wrapped_json),
        ("Markdown ``` 包裹", test_plain_markdown_wrapped),
        ("空编辑列表", test_empty_edits),
        ("无效 JSON", test_invalid_json),
        ("验证失败", test_validation_failure),
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
        print("✅ 所有测试通过！edit_document 工具已修复成功！")
    else:
        print(f"❌ 有 {failed} 个测试失败，需要进一步修复。")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

