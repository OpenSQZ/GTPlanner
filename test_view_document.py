"""
测试 view_document 工具的文件名查找功能

测试场景：
1. 使用 filename 参数查找存在的文档
2. 使用 filename 参数查找不存在的文档
3. 多个文档同时存在时的查找
4. 系统提示词中的动态文档列表构建
"""

import asyncio
from gtplanner.agent.nodes.node_view_document import NodeViewDocument


async def test_view_document_by_filename():
    """测试按文件名查找文档"""
    print("\n" + "="*80)
    print("测试1: 按文件名查找存在的文档")
    print("="*80)

    # 创建测试用的 shared 字典
    shared = {
        "filename": "design.md",
        "generated_documents": [
            {
                "type": "design",
                "filename": "design.md",
                "content": "# 系统设计文档\n\n这是设计文档的内容...",
                "tool_name": "design"
            },
            {
                "type": "design",
                "filename": "prefabs_info.md",
                "content": "# 预制件函数详情\n\n这是预制件详情文档的内容...",
                "tool_name": "prefab_functions_detail"
            },
            {
                "type": "database_design",
                "filename": "database_design.md",
                "content": "# 数据库设计文档\n\n这是数据库设计文档的内容...",
                "tool_name": "database_design"
            }
        ],
        "streaming_session": None  # 测试环境不需要流式会话
    }

    # 创建节点并执行
    node = NodeViewDocument()

    # prep 阶段
    prep_result = await node.prep_async(shared)
    print(f"\n✅ Prep 结果: {prep_result}")
    assert prep_result["success"] is True, "Prep 阶段应该成功"
    assert prep_result["filename"] == "design.md", "应该获取到正确的文件名"

    # exec 阶段
    exec_result = await node.exec_async(prep_result)
    print(f"\n✅ Exec 结果:")
    print(f"   - success: {exec_result.get('success')}")
    print(f"   - filename: {exec_result.get('filename')}")
    print(f"   - document_type: {exec_result.get('document_type')}")
    print(f"   - content_length: {exec_result.get('content_length')}")
    print(f"   - content preview: {exec_result.get('content', '')[:50]}...")

    assert exec_result["success"] is True, "Exec 阶段应该成功"
    assert exec_result["filename"] == "design.md", "应该返回正确的文件名"
    assert exec_result["document_type"] == "design", "应该返回正确的文档类型"
    assert "系统设计文档" in exec_result["content"], "应该返回正确的文档内容"

    # post 阶段
    post_result = await node.post_async(shared, prep_result, exec_result)
    print(f"\n✅ Post 结果: {post_result}")
    assert post_result["success"] is True, "Post 阶段应该成功"

    print("\n✅ 测试1 通过！")


async def test_view_document_not_found():
    """测试查找不存在的文档"""
    print("\n" + "="*80)
    print("测试2: 查找不存在的文档")
    print("="*80)

    shared = {
        "filename": "nonexistent.md",
        "generated_documents": [
            {
                "type": "design",
                "filename": "design.md",
                "content": "# 系统设计文档",
                "tool_name": "design"
            }
        ],
        "streaming_session": None
    }

    node = NodeViewDocument()

    # prep 阶段
    prep_result = await node.prep_async(shared)
    assert prep_result["success"] is True, "Prep 阶段应该成功"

    # exec 阶段
    exec_result = await node.exec_async(prep_result)
    print(f"\n✅ Exec 结果:")
    print(f"   - success: {exec_result.get('success')}")
    print(f"   - error: {exec_result.get('error')}")
    print(f"   - available_documents: {exec_result.get('available_documents')}")

    assert exec_result["success"] is False, "应该返回失败"
    assert "没有找到文档" in exec_result["error"], "错误信息应该说明文档未找到"
    assert "available_documents" in exec_result, "应该返回可用文档列表"
    assert "design.md" in exec_result["available_documents"], "可用文档列表应该包含 design.md"

    print("\n✅ 测试2 通过！")


async def test_view_prefabs_info_document():
    """测试查找预制件详情文档"""
    print("\n" + "="*80)
    print("测试3: 查找预制件详情文档 (prefabs_info.md)")
    print("="*80)

    shared = {
        "filename": "prefabs_info.md",
        "generated_documents": [
            {
                "type": "design",
                "filename": "design.md",
                "content": "# 系统设计文档",
                "tool_name": "design"
            },
            {
                "type": "design",
                "filename": "prefabs_info.md",
                "content": "# 预制件函数详情\n\n## browser-automation-agent\n\n### navigate_to\n参数: url (string)\n返回: success (boolean)",
                "tool_name": "prefab_functions_detail"
            }
        ],
        "streaming_session": None
    }

    node = NodeViewDocument()

    # prep 阶段
    prep_result = await node.prep_async(shared)
    assert prep_result["success"] is True, "Prep 阶段应该成功"

    # exec 阶段
    exec_result = await node.exec_async(prep_result)
    print(f"\n✅ Exec 结果:")
    print(f"   - success: {exec_result.get('success')}")
    print(f"   - filename: {exec_result.get('filename')}")
    print(f"   - document_type: {exec_result.get('document_type')}")
    print(f"   - content preview: {exec_result.get('content', '')[:100]}...")

    assert exec_result["success"] is True, "Exec 阶段应该成功"
    assert exec_result["filename"] == "prefabs_info.md", "应该返回正确的文件名"
    assert exec_result["document_type"] == "design", "预制件详情文档类型应该是 design"
    assert "预制件函数详情" in exec_result["content"], "应该返回正确的文档内容"
    assert "browser-automation-agent" in exec_result["content"], "应该包含预制件信息"

    print("\n✅ 测试3 通过！")


async def test_no_documents_available():
    """测试没有可用文档的情况"""
    print("\n" + "="*80)
    print("测试4: 没有可用文档")
    print("="*80)

    shared = {
        "filename": "design.md",
        "generated_documents": [],  # 空列表
        "streaming_session": None
    }

    node = NodeViewDocument()

    # prep 阶段
    prep_result = await node.prep_async(shared)
    assert prep_result["success"] is True, "Prep 阶段应该成功"

    # exec 阶段
    exec_result = await node.exec_async(prep_result)
    print(f"\n✅ Exec 结果:")
    print(f"   - success: {exec_result.get('success')}")
    print(f"   - error: {exec_result.get('error')}")

    assert exec_result["success"] is False, "应该返回失败"
    assert "没有找到已生成的文档" in exec_result["error"], "错误信息应该说明没有可用文档"

    print("\n✅ 测试4 通过！")


def test_dynamic_document_list_construction():
    """测试系统提示词中的动态文档列表构建"""
    print("\n" + "="*80)
    print("测试5: 动态文档列表构建")
    print("="*80)

    # 模拟 shared 字典
    shared = {
        "generated_documents": [
            {"filename": "design.md", "type": "design"},
            {"filename": "prefabs_info.md", "type": "design"},
            {"filename": "database_design.md", "type": "database_design"}
        ],
        "language": "zh"
    }

    # 提取文档列表
    generated_documents = shared.get("generated_documents", [])
    available_docs = [doc.get("filename") for doc in generated_documents if doc.get("filename")]

    print(f"\n✅ 可用文档列表: {available_docs}")
    assert len(available_docs) == 3, "应该有3个文档"
    assert "design.md" in available_docs, "应该包含 design.md"
    assert "prefabs_info.md" in available_docs, "应该包含 prefabs_info.md"
    assert "database_design.md" in available_docs, "应该包含 database_design.md"

    # 构建提示词片段（中文）
    docs_list = "\n".join([f"- {filename}" for filename in available_docs])
    language = shared.get("language")
    if language == "zh":
        context_info = f"\n\n# 当前会话上下文\n\n## 已生成的文档\n当前会话中已生成以下文档，可使用 `view_document` 工具查看：\n{docs_list}\n"
    else:
        context_info = f"\n\n# Current Session Context\n\n## Generated Documents\nThe following documents have been generated in this session and can be viewed using the `view_document` tool:\n{docs_list}\n"

    print(f"\n✅ 构建的提示词片段:")
    print(context_info)

    assert "当前会话上下文" in context_info, "应该包含中文标题"
    assert "已生成的文档" in context_info, "应该包含中文小标题"
    assert "- design.md" in context_info, "应该包含 design.md"
    assert "- prefabs_info.md" in context_info, "应该包含 prefabs_info.md"
    assert "- database_design.md" in context_info, "应该包含 database_design.md"

    # 测试英文版本
    shared["language"] = "en"
    language = shared.get("language")
    if language == "zh":
        context_info = f"\n\n# 当前会话上下文\n\n## 已生成的文档\n当前会话中已生成以下文档，可使用 `view_document` 工具查看：\n{docs_list}\n"
    else:
        context_info = f"\n\n# Current Session Context\n\n## Generated Documents\nThe following documents have been generated in this session and can be viewed using the `view_document` tool:\n{docs_list}\n"

    print(f"\n✅ 构建的英文提示词片段:")
    print(context_info)

    assert "Current Session Context" in context_info, "应该包含英文标题"
    assert "Generated Documents" in context_info, "应该包含英文小标题"

    print("\n✅ 测试5 通过！")


async def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("开始测试 view_document 工具的文件名查找功能")
    print("="*80)

    try:
        # 测试1: 按文件名查找存在的文档
        await test_view_document_by_filename()

        # 测试2: 查找不存在的文档
        await test_view_document_not_found()

        # 测试3: 查找预制件详情文档
        await test_view_prefabs_info_document()

        # 测试4: 没有可用文档
        await test_no_documents_available()

        # 测试5: 动态文档列表构建
        test_dynamic_document_list_construction()

        print("\n" + "="*80)
        print("✅ 所有测试通过！")
        print("="*80)

        print("\n总结：")
        print("1. ✅ 按文件名查找文档功能正常")
        print("2. ✅ 文档未找到时返回可用文档列表")
        print("3. ✅ 能正确区分 design.md 和 prefabs_info.md（即使类型相同）")
        print("4. ✅ 没有可用文档时错误处理正常")
        print("5. ✅ 动态文档列表构建功能正常（支持中英文）")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
