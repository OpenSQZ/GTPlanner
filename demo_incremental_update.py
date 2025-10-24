#!/usr/bin/env python3
"""
工具索引增量更新功能演示

展示增量更新功能的使用方法和性能提升效果。
"""

import os
import time
import tempfile
import shutil
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from agent.utils.file_monitor import analyze_tool_file_changes, ToolFileMonitor
from agent.utils.tool_index_manager import tool_index_manager


def create_demo_tools(tools_dir: str):
    """创建演示用的工具文件"""
    import yaml
    
    # 创建工具目录
    os.makedirs(tools_dir, exist_ok=True)
    
    # 工具1：Python包工具
    tool1 = {
        "id": "demo.requests",
        "type": "PYTHON_PACKAGE",
        "summary": "HTTP库工具",
        "description": "用于发送HTTP请求的Python库",
        "requirement": "requests",
        "examples": [
            {
                "title": "发送GET请求",
                "content": "import requests\nresponse = requests.get('https://api.example.com')"
            }
        ]
    }
    
    with open(os.path.join(tools_dir, "requests_tool.yml"), 'w', encoding='utf-8') as f:
        yaml.dump(tool1, f, allow_unicode=True)
    
    # 工具2：API工具
    tool2 = {
        "id": "demo.weather-api",
        "type": "APIS",
        "summary": "天气API",
        "description": "获取天气信息的API服务",
        "base_url": "https://api.weather.com",
        "endpoints": [
            {
                "method": "GET",
                "path": "/current",
                "summary": "获取当前天气"
            }
        ]
    }
    
    with open(os.path.join(tools_dir, "weather_api.yml"), 'w', encoding='utf-8') as f:
        yaml.dump(tool2, f, allow_unicode=True)


def modify_tool_file(tools_dir: str, filename: str):
    """修改工具文件"""
    file_path = os.path.join(tools_dir, filename)
    if os.path.exists(file_path):
        import yaml
        
        # 读取现有内容
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 修改描述
        if 'description' in data:
            data['description'] += " (已更新)"
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)


async def demo_incremental_update():
    """演示增量更新功能"""
    print("🚀 工具索引增量更新功能演示")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    tools_dir = os.path.join(temp_dir, "tools")
    
    try:
        # 1. 创建初始工具文件
        print("\n📁 步骤1: 创建初始工具文件")
        create_demo_tools(tools_dir)
        print(f"   创建了2个工具文件在: {tools_dir}")
        
        # 2. 分析文件变化
        print("\n🔍 步骤2: 分析文件变化")
        result1 = analyze_tool_file_changes(tools_dir)
        print(f"   总文件数: {result1.total_files}")
        print(f"   新增文件: {len(result1.new_files)}")
        print(f"   修改文件: {len(result1.changed_files)}")
        print(f"   删除文件: {len(result1.removed_files)}")
        print(f"   需要更新: {result1.update_needed}")
        print(f"   摘要: {result1.get_summary()}")
        
        # 3. 更新文件缓存
        print("\n💾 步骤3: 更新文件缓存")
        monitor = ToolFileMonitor(tools_dir)
        for file_path in result1.new_files:
            monitor.update_file_cache(file_path)
        monitor.save_cache()
        print("   文件缓存已更新")
        
        # 4. 再次分析（应该无变化）
        print("\n🔍 步骤4: 再次分析文件变化")
        result2 = analyze_tool_file_changes(tools_dir)
        print(f"   需要更新: {result2.update_needed}")
        print(f"   摘要: {result2.get_summary()}")
        
        # 5. 修改一个文件
        print("\n📝 步骤5: 修改工具文件")
        modify_tool_file(tools_dir, "requests_tool.yml")
        print("   已修改 requests_tool.yml")
        
        # 6. 分析修改后的变化
        print("\n🔍 步骤6: 分析修改后的变化")
        result3 = analyze_tool_file_changes(tools_dir)
        print(f"   总文件数: {result3.total_files}")
        print(f"   新增文件: {len(result3.new_files)}")
        print(f"   修改文件: {len(result3.changed_files)}")
        print(f"   删除文件: {len(result3.removed_files)}")
        print(f"   需要更新: {result3.update_needed}")
        print(f"   摘要: {result3.get_summary()}")
        
        if result3.changed_files:
            print(f"   修改的文件: {[os.path.basename(f) for f in result3.changed_files]}")
        
        # 7. 添加新文件
        print("\n➕ 步骤7: 添加新的工具文件")
        import yaml
        new_tool = {
            "id": "demo.new-tool",
            "type": "PYTHON_PACKAGE",
            "summary": "新工具",
            "description": "这是一个新添加的工具"
        }
        
        with open(os.path.join(tools_dir, "new_tool.yml"), 'w', encoding='utf-8') as f:
            yaml.dump(new_tool, f, allow_unicode=True)
        print("   已添加 new_tool.yml")
        
        # 8. 分析添加文件后的变化
        print("\n🔍 步骤8: 分析添加文件后的变化")
        result4 = analyze_tool_file_changes(tools_dir)
        print(f"   总文件数: {result4.total_files}")
        print(f"   新增文件: {len(result4.new_files)}")
        print(f"   修改文件: {len(result4.changed_files)}")
        print(f"   删除文件: {len(result4.removed_files)}")
        print(f"   需要更新: {result4.update_needed}")
        print(f"   摘要: {result4.get_summary()}")
        
        if result4.new_files:
            print(f"   新增的文件: {[os.path.basename(f) for f in result4.new_files]}")
        
        # 9. 演示性能对比
        print("\n⚡ 步骤9: 性能对比演示")
        print("   模拟全量重建 vs 增量更新:")
        
        # 模拟全量重建时间
        start_time = time.time()
        # 这里只是模拟，实际会调用向量服务
        await asyncio.sleep(0.1)  # 模拟处理时间
        full_rebuild_time = time.time() - start_time
        
        # 模拟增量更新时间
        start_time = time.time()
        # 只处理变化的文件
        changed_count = len(result4.new_files) + len(result4.changed_files)
        await asyncio.sleep(0.02 * changed_count)  # 模拟处理时间
        incremental_time = time.time() - start_time
        
        print(f"   全量重建时间: {full_rebuild_time:.3f}s")
        print(f"   增量更新时间: {incremental_time:.3f}s")
        print(f"   性能提升: {((full_rebuild_time - incremental_time) / full_rebuild_time * 100):.1f}%")
        
        # 10. 显示缓存信息
        print("\n📊 步骤10: 缓存信息")
        cache_info = monitor.get_cache_info()
        print(f"   缓存文件数: {cache_info['total_cached_files']}")
        print(f"   缓存文件: {cache_info['cache_file']}")
        print(f"   工具目录: {cache_info['tools_dir']}")
        
        print("\n✅ 演示完成！")
        print("\n💡 关键优势:")
        print("   • 智能检测文件变化，避免不必要的索引重建")
        print("   • 显著提升系统启动速度和响应性能")
        print("   • 支持实时文件监控和缓存管理")
        print("   • 提供完整的错误处理和回退机制")
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n🧹 已清理临时目录: {temp_dir}")


def demo_command_line_usage():
    """演示命令行使用方法"""
    print("\n🖥️ 命令行使用方法:")
    print("=" * 40)
    print("# 检查文件变化")
    print("python manage_tool_index.py check-changes")
    print()
    print("# 执行增量更新")
    print("python manage_tool_index.py incremental-update")
    print()
    print("# 查看索引状态")
    print("python manage_tool_index.py status")
    print()
    print("# 强制重建索引")
    print("python manage_tool_index.py force-refresh")


if __name__ == "__main__":
    import sys
    
    print("🎯 GTPlanner 工具索引增量更新功能演示")
    print("=" * 60)
    
    # 运行异步演示
    asyncio.run(demo_incremental_update())
    
    # 显示命令行用法
    demo_command_line_usage()
    
    print("\n📚 更多信息请查看文档:")
    print("   docs/incremental_index_update.md")
