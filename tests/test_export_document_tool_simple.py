"""
简化的 export_document 工具测试（避免依赖问题）

直接测试核心功能，不依赖完整的模块导入
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def read_test_markdown():
    """读取测试用的 Markdown 文件"""
    test_file = Path(__file__).parent.parent / "output" / "design.md"
    if not test_file.exists():
        print(f"[SKIP] 测试文件不存在: {test_file}")
        return None
    return test_file.read_text(encoding='utf-8')


async def test_export_document_node_direct():
    """直接测试 NodeExportDocument 节点"""
    print("\n" + "="*80)
    print("测试: 直接测试 NodeExportDocument 节点")
    print("="*80)
    
    try:
        from gtplanner.agent.nodes.node_export import NodeExportDocument
    except ImportError as e:
        print(f"[SKIP] 无法导入 NodeExportDocument: {e}")
        return
    
    markdown_content = read_test_markdown()
    if not markdown_content:
        return
    
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
        "streaming_session": None
    }
    
    # Mock 流式事件函数
    from unittest.mock import AsyncMock, patch
    
    with patch('gtplanner.agent.nodes.node_export.emit_processing_status', new_callable=AsyncMock) as mock_status, \
         patch('gtplanner.agent.nodes.node_export.emit_error', new_callable=AsyncMock) as mock_error:
        
        # 创建节点并执行
        node = NodeExportDocument()
        result = await node.run_async(shared)
        
        # 验证结果
        print(f"\n[RESULT] 节点执行结果:")
        print(f"  success: {result.get('success')}")
        
        if result.get("success"):
            saved_files = result.get("saved_files", [])
            total_exported = result.get("total_exported", 0)
            total_failed = result.get("total_failed", 0)
            
            print(f"  total_exported: {total_exported}")
            print(f"  total_failed: {total_failed}")
            print(f"  saved_files: {len(saved_files)} 个文件")
            
            # 验证文件列表
            for file_info in saved_files:
                filename = file_info.get("filename")
                format_type = file_info.get("format")
                file_path = file_info.get("path")
                print(f"    - {filename} ({format_type})")
                print(f"      路径: {file_path}")
                
                # 验证文件存在
                if file_path:
                    path_obj = Path(file_path)
                    if path_obj.exists():
                        print(f"      [OK] 文件存在，大小: {path_obj.stat().st_size} 字节")
                    else:
                        print(f"      [WARN] 文件不存在: {path_path}")
            
            print("\n[OK] 节点测试通过")
            return True
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"  error: {error_msg}")
            print("\n[FAIL] 节点测试失败")
            return False


async def test_export_document_function_direct():
    """直接测试 _execute_export_document 函数"""
    print("\n" + "="*80)
    print("测试: 直接测试 _execute_export_document 函数")
    print("="*80)
    
    try:
        from gtplanner.agent.function_calling.agent_tools import _execute_export_document
    except ImportError as e:
        print(f"[SKIP] 无法导入 _execute_export_document: {e}")
        print("  这通常是因为缺少依赖（如 pocketflow）")
        return
    
    markdown_content = read_test_markdown()
    if not markdown_content:
        return
    
    # 准备参数
    arguments = {
        "document_type": "design",
        "export_formats": ["html", "txt"],
        "output_dir": "output"
    }
    
    # 准备 shared 数据
    shared = {
        "generated_documents": [
            {
                "type": "design",
                "filename": "design.md",
                "content": markdown_content
            }
        ],
        "streaming_session": None
    }
    
    # Mock 流式事件函数
    from unittest.mock import AsyncMock, patch
    
    with patch('gtplanner.agent.nodes.node_export.emit_processing_status', new_callable=AsyncMock), \
         patch('gtplanner.agent.nodes.node_export.emit_error', new_callable=AsyncMock):
        
        # 执行函数
        result = await _execute_export_document(arguments, shared)
        
        # 验证结果
        print(f"\n[RESULT] 函数执行结果:")
        print(f"  success: {result.get('success')}")
        print(f"  tool_name: {result.get('tool_name')}")
        
        if result.get("success"):
            saved_files = result.get("saved_files", [])
            total_exported = result.get("total_exported", 0)
            
            print(f"  total_exported: {total_exported}")
            print(f"  saved_files: {len(saved_files)} 个文件")
            
            for file_info in saved_files:
                print(f"    - {file_info.get('filename')} ({file_info.get('format')})")
            
            print("\n[OK] 函数测试通过")
            return True
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"  error: {error_msg}")
            print("\n[FAIL] 函数测试失败")
            return False


async def test_format_conversion():
    """测试格式转换功能"""
    print("\n" + "="*80)
    print("测试: 格式转换功能")
    print("="*80)
    
    try:
        from gtplanner.agent.nodes.node_export import NodeExportDocument
    except ImportError as e:
        print(f"[SKIP] 无法导入 NodeExportDocument: {e}")
        return
    
    markdown_content = read_test_markdown()
    if not markdown_content:
        return
    
    node = NodeExportDocument()
    
    # 测试 HTML 转换
    try:
        html_content = node._markdown_to_html(markdown_content)
        assert html_content is not None, "HTML 内容不应为空"
        assert "<!DOCTYPE html>" in html_content, "应包含 HTML 文档声明"
        print("[OK] HTML 转换成功")
    except Exception as e:
        print(f"[FAIL] HTML 转换失败: {e}")
        return False
    
    # 测试 TXT 转换
    try:
        txt_content = node._markdown_to_txt(markdown_content)
        assert txt_content is not None, "TXT 内容不应为空"
        assert len(txt_content) > 0, "TXT 内容不应为空"
        print("[OK] TXT 转换成功")
    except Exception as e:
        print(f"[FAIL] TXT 转换失败: {e}")
        return False
    
    # 测试格式转换方法
    try:
        md_result = node._convert_format(markdown_content, "md")
        assert md_result == markdown_content, "MD 格式应直接返回"
        
        html_result = node._convert_format(markdown_content, "html")
        assert html_result != markdown_content, "HTML 格式应转换"
        
        txt_result = node._convert_format(markdown_content, "txt")
        assert txt_result != markdown_content, "TXT 格式应转换"
        
        print("[OK] 格式转换方法测试通过")
    except Exception as e:
        print(f"[FAIL] 格式转换方法测试失败: {e}")
        return False
    
    return True


async def main():
    """运行所有测试"""
    print("="*80)
    print("export_document 工具测试")
    print("="*80)
    
    results = []
    
    # 测试1: 格式转换
    result1 = await test_format_conversion()
    results.append(("格式转换", result1))
    
    # 测试2: 节点直接测试
    result2 = await test_export_document_node_direct()
    results.append(("节点直接测试", result2))
    
    # 测试3: 函数直接测试
    result3 = await test_export_document_function_direct()
    results.append(("函数直接测试", result3))
    
    # 汇总结果
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result is True:
            print(f"[PASS] {test_name}")
            passed += 1
        elif result is False:
            print(f"[FAIL] {test_name}")
            failed += 1
        else:
            print(f"[SKIP] {test_name}")
            skipped += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

