"""
测试 NodeExportDocument 的文档格式转换功能

测试内容：
1. Markdown 转 HTML
2. Markdown 转 TXT
3. 完整节点执行流程
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 直接导入转换方法，避免导入整个节点（可能有依赖问题）
def create_test_node():
    """创建测试用的节点实例"""
    try:
        from gtplanner.agent.nodes.node_export import NodeExportDocument
        return NodeExportDocument()
    except ImportError as e:
        pytest.skip(f"无法导入 NodeExportDocument: {e}")


def read_test_markdown():
    """读取测试用的 Markdown 文件"""
    test_file = Path(__file__).parent.parent / "output" / "design.md"
    if not test_file.exists():
        pytest.skip(f"测试文件不存在: {test_file}")
    return test_file.read_text(encoding='utf-8')


def test_markdown_to_html():
    """测试 Markdown 转 HTML 功能"""
    print("\n" + "="*80)
    print("测试场景 1: Markdown 转 HTML")
    print("="*80)
    
    node = create_test_node()
    markdown_content = read_test_markdown()
    
    # 执行转换（同步方法）
    html_content = node._markdown_to_html(markdown_content)
    
    # 验证结果
    assert html_content is not None, "HTML 内容不应为空"
    assert "<!DOCTYPE html>" in html_content, "应包含 HTML 文档声明"
    assert "<html" in html_content, "应包含 HTML 标签"
    assert "<head>" in html_content, "应包含 head 标签"
    assert "<body>" in html_content, "应包含 body 标签"
    
    # 验证基本 Markdown 元素转换
    assert "<h1>" in html_content or "<h2>" in html_content, "应包含标题标签"
    assert "<ul>" in html_content or "<ol>" in html_content, "应包含列表标签"
    
    # 验证代码块
    if "```" in markdown_content:
        assert "<pre>" in html_content or "<code>" in html_content, "应包含代码块标签"
    
    print(f"✅ HTML 转换成功")
    print(f"📏 HTML 长度: {len(html_content)} 字符")
    print(f"📝 原始 Markdown 长度: {len(markdown_content)} 字符")
    
    # 保存 HTML 文件用于人工检查
    output_dir = Path(__file__).parent.parent / "output"
    html_file = output_dir / "design_test.html"
    html_file.write_text(html_content, encoding='utf-8')
    print(f"💾 HTML 文件已保存到: {html_file}")
    
    assert True


def test_markdown_to_txt():
    """测试 Markdown 转 TXT 功能"""
    print("\n" + "="*80)
    print("测试场景 2: Markdown 转 TXT")
    print("="*80)
    
    node = create_test_node()
    markdown_content = read_test_markdown()
    
    # 执行转换（同步方法）
    txt_content = node._markdown_to_txt(markdown_content)
    
    # 验证结果
    assert txt_content is not None, "TXT 内容不应为空"
    assert len(txt_content) > 0, "TXT 内容不应为空字符串"
    
    # 验证 Markdown 语法已被移除
    assert "```" not in txt_content, "不应包含代码块标记"
    assert "**" not in txt_content or txt_content.count("**") == 0, "不应包含粗体标记"
    assert not any(line.startswith("#") for line in txt_content.split("\n") if line.strip()), "不应包含标题标记"
    
    print(f"✅ TXT 转换成功")
    print(f"📏 TXT 长度: {len(txt_content)} 字符")
    print(f"📝 原始 Markdown 长度: {len(markdown_content)} 字符")
    
    # 显示前几行内容
    print("\n📄 TXT 内容预览（前10行）:")
    for i, line in enumerate(txt_content.split("\n")[:10], 1):
        print(f"   {i:2d}. {line}")
    
    # 保存 TXT 文件用于人工检查
    output_dir = Path(__file__).parent.parent / "output"
    txt_file = output_dir / "design_test.txt"
    txt_file.write_text(txt_content, encoding='utf-8')
    print(f"\n💾 TXT 文件已保存到: {txt_file}")
    
    assert True


def test_convert_format():
    """测试格式转换方法"""
    print("\n" + "="*80)
    print("测试场景 3: 格式转换方法")
    print("="*80)
    
    node = create_test_node()
    markdown_content = read_test_markdown()
    
    # 测试 MD 格式（应直接返回）
    md_result = node._convert_format(markdown_content, "md")
    assert md_result == markdown_content, "MD 格式应直接返回原内容"
    print("✅ MD 格式转换通过")
    
    # 测试 HTML 格式
    html_result = node._convert_format(markdown_content, "html")
    assert html_result != markdown_content, "HTML 格式应转换内容"
    assert "<html" in html_result, "应包含 HTML 标签"
    print("✅ HTML 格式转换通过")
    
    # 测试 TXT 格式
    txt_result = node._convert_format(markdown_content, "txt")
    assert txt_result != markdown_content, "TXT 格式应转换内容"
    assert "```" not in txt_result, "不应包含代码块标记"
    print("✅ TXT 格式转换通过")
    
    # 测试不支持的格式
    with pytest.raises(NotImplementedError):
        node._convert_format(markdown_content, "pdf")
    print("✅ PDF 格式正确抛出 NotImplementedError")
    
    with pytest.raises(NotImplementedError):
        node._convert_format(markdown_content, "docx")
    print("✅ DOCX 格式正确抛出 NotImplementedError")
    
    # 测试无效格式
    with pytest.raises(ValueError):
        node._convert_format(markdown_content, "invalid")
    print("✅ 无效格式正确抛出 ValueError")


@pytest.mark.asyncio
async def test_node_export_full_flow():
    """测试完整的节点导出流程"""
    print("\n" + "="*80)
    print("测试场景 4: 完整节点导出流程")
    print("="*80)
    
    node = create_test_node()
    markdown_content = read_test_markdown()
    
    # 准备 shared 数据
    shared = {
        "document_type": "design",
        "export_formats": ["html", "txt"],
        "output_dir": "output",
        "generated_documents": [
            {
                "type": "design",
                "filename": "design.md",
                "content": markdown_content
            }
        ],
        "streaming_session": None  # 不使用流式会话
    }
    
    # Mock 流式事件函数（避免实际发送事件）
    with patch('gtplanner.agent.nodes.node_export.emit_processing_status', new_callable=AsyncMock) as mock_status, \
         patch('gtplanner.agent.nodes.node_export.emit_error', new_callable=AsyncMock) as mock_error:
        
        # 执行节点
        result = await node.run_async(shared)
        
        # 验证结果
        assert result is not None, "结果不应为空"
        assert result.get("success") == True, "导出应成功"
        assert "saved_files" in result, "应包含保存的文件列表"
        assert len(result.get("saved_files", [])) > 0, "应至少保存一个文件"
        
        print(f"✅ 节点执行成功")
        print(f"📊 导出文件数量: {result.get('total_exported', 0)}")
        print(f"❌ 失败数量: {result.get('total_failed', 0)}")
        
        # 显示保存的文件
        print("\n📁 保存的文件:")
        for file_info in result.get("saved_files", []):
            print(f"   - {file_info.get('filename')} ({file_info.get('format')})")
            print(f"     路径: {file_info.get('path')}")
            print(f"     大小: {file_info.get('size')} 字节")
        
        # 验证文件确实存在
        output_dir = Path(__file__).parent.parent / "output"
        for file_info in result.get("saved_files", []):
            file_path = output_dir / file_info.get("filename")
            assert file_path.exists(), f"文件应存在: {file_path}"
            print(f"   ✅ 文件存在: {file_path}")


@pytest.mark.asyncio
async def test_node_export_multiple_formats():
    """测试导出多种格式"""
    print("\n" + "="*80)
    print("测试场景 5: 导出多种格式")
    print("="*80)
    
    node = create_test_node()
    markdown_content = read_test_markdown()
    
    # 准备 shared 数据 - 导出所有支持的文本格式
    shared = {
        "document_type": "design",
        "export_formats": ["md", "html", "txt"],
        "output_dir": "output",
        "generated_documents": [
            {
                "type": "design",
                "filename": "design.md",
                "content": markdown_content
            }
        ],
        "streaming_session": None
    }
    
    with patch('gtplanner.agent.nodes.node_export.emit_processing_status', new_callable=AsyncMock), \
         patch('gtplanner.agent.nodes.node_export.emit_error', new_callable=AsyncMock):
        
        result = await node.run_async(shared)
        
        assert result.get("success") == True, "导出应成功"
        assert result.get("total_exported") == 3, "应导出 3 个文件（md, html, txt）"
        
        print(f"✅ 成功导出 {result.get('total_exported')} 个文件")
        
        # 验证每种格式都已保存
        saved_formats = {f.get("format") for f in result.get("saved_files", [])}
        assert "md" in saved_formats, "应包含 MD 格式"
        assert "html" in saved_formats, "应包含 HTML 格式"
        assert "txt" in saved_formats, "应包含 TXT 格式"
        
        print("✅ 所有格式都已成功导出")


@pytest.mark.asyncio
async def test_node_export_error_handling():
    """测试错误处理"""
    print("\n" + "="*80)
    print("测试场景 6: 错误处理")
    print("="*80)
    
    node = create_test_node()
    
    # 测试1: 缺少 document_type
    shared1 = {
        "export_formats": ["html"],
        "generated_documents": []
    }
    
    with patch('gtplanner.agent.nodes.node_export.emit_error', new_callable=AsyncMock) as mock_error:
        result1 = await node.run_async(shared1)
        assert result1.get("success") == False, "应返回失败"
        assert "document_type" in result1.get("error", "").lower(), "错误信息应提及 document_type"
        print("✅ 缺少 document_type 的错误处理正确")
    
    # 测试2: 缺少 export_formats
    shared2 = {
        "document_type": "design",
        "generated_documents": []
    }
    
    with patch('gtplanner.agent.nodes.node_export.emit_error', new_callable=AsyncMock):
        result2 = await node.run_async(shared2)
        assert result2.get("success") == False, "应返回失败"
        print("✅ 缺少 export_formats 的错误处理正确")
    
    # 测试3: 没有文档
    shared3 = {
        "document_type": "design",
        "export_formats": ["html"],
        "generated_documents": []
    }
    
    with patch('gtplanner.agent.nodes.node_export.emit_error', new_callable=AsyncMock):
        result3 = await node.run_async(shared3)
        assert result3.get("success") == False, "应返回失败"
        print("✅ 没有文档的错误处理正确")
    
    # 测试4: 无效格式
    markdown_content = read_test_markdown()
    shared4 = {
        "document_type": "design",
        "export_formats": ["invalid_format"],
        "generated_documents": [
            {
                "type": "design",
                "filename": "design.md",
                "content": markdown_content
            }
        ]
    }
    
    with patch('gtplanner.agent.nodes.node_export.emit_error', new_callable=AsyncMock):
        result4 = await node.run_async(shared4)
        assert result4.get("success") == False, "应返回失败"
        print("✅ 无效格式的错误处理正确")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])

