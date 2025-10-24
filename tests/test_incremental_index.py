"""
工具索引增量更新功能测试

测试文件监控、校验和计算、增量更新等核心功能。
"""

import os
import tempfile
import shutil
import asyncio
import json
import time
from pathlib import Path
import pytest

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.utils.file_monitor import (
    FileChecksumManager, 
    ToolFileMonitor, 
    analyze_tool_file_changes,
    IncrementalUpdateResult
)
from agent.utils.tool_index_manager import ToolIndexManager


class TestFileChecksumManager:
    """测试文件校验和管理器"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, "test_checksums.json")
        self.manager = FileChecksumManager(self.cache_file)
    
    def teardown_method(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_calculate_checksum(self):
        """测试校验和计算"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        
        # 创建测试文件
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Hello, World!")
        
        checksum1 = self.manager.calculate_checksum(test_file)
        assert checksum1 != ""
        assert len(checksum1) == 32  # MD5长度
        
        # 修改文件内容
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Hello, Python!")
        
        checksum2 = self.manager.calculate_checksum(test_file)
        assert checksum2 != checksum1
    
    def test_file_change_detection(self):
        """测试文件变化检测"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        
        # 初始状态，文件不存在
        assert self.manager.is_file_changed(test_file) == True
        
        # 创建文件
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Initial content")
        
        # 第一次检查，应该检测到变化
        assert self.manager.is_file_changed(test_file) == True
        
        # 更新文件信息
        self.manager.update_file_info(test_file)
        
        # 再次检查，应该没有变化
        assert self.manager.is_file_changed(test_file) == False
        
        # 修改文件内容
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Modified content")
        
        # 应该检测到变化
        assert self.manager.is_file_changed(test_file) == True
    
    def test_cache_persistence(self):
        """测试缓存持久化"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        
        # 创建文件并更新信息
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Test content")
        
        self.manager.update_file_info(test_file)
        self.manager.save_changes()
        
        # 创建新的管理器实例
        new_manager = FileChecksumManager(self.cache_file)
        
        # 应该能检测到文件没有变化
        assert new_manager.is_file_changed(test_file) == False


class TestToolFileMonitor:
    """测试工具文件监控器"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = ToolFileMonitor(self.temp_dir)
        
        # 创建测试工具文件
        self.create_test_tools()
    
    def teardown_method(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_tools(self):
        """创建测试工具文件"""
        # 创建工具目录结构
        tools_dir = os.path.join(self.temp_dir, "tools")
        os.makedirs(tools_dir, exist_ok=True)
        
        # 创建Python包工具
        python_tool = {
            "id": "test.python-tool",
            "type": "PYTHON_PACKAGE",
            "summary": "测试Python工具",
            "description": "这是一个测试用的Python工具",
            "requirement": "test-package",
            "examples": [
                {
                    "title": "基础使用",
                    "content": "import test_package\nprint('Hello')"
                }
            ]
        }
        
        with open(os.path.join(tools_dir, "python_tool.yml"), 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(python_tool, f, allow_unicode=True)
        
        # 创建API工具
        api_tool = {
            "id": "test.api-tool",
            "type": "APIS",
            "summary": "测试API工具",
            "description": "这是一个测试用的API工具",
            "base_url": "https://api.test.com",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/test",
                    "summary": "测试端点"
                }
            ]
        }
        
        with open(os.path.join(tools_dir, "api_tool.yml"), 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(api_tool, f, allow_unicode=True)
    
    def test_scan_tool_files(self):
        """测试工具文件扫描"""
        files = self.monitor.scan_tool_files()
        assert len(files) == 2
        assert any("python_tool.yml" in f for f in files)
        assert any("api_tool.yml" in f for f in files)
    
    def test_file_change_analysis(self):
        """测试文件变化分析"""
        # 初始状态，所有文件都是新的
        result = analyze_tool_file_changes(self.temp_dir)
        assert result.total_files == 2
        assert len(result.new_files) == 2
        assert len(result.changed_files) == 0
        assert len(result.removed_files) == 0
        assert result.update_needed == True
        
        # 更新文件缓存
        for file_path in result.new_files:
            self.monitor.update_file_cache(file_path)
        self.monitor.save_cache()
        
        # 再次分析，应该没有变化
        result2 = analyze_tool_file_changes(self.temp_dir)
        assert result2.total_files == 2
        assert len(result2.new_files) == 0
        assert len(result2.changed_files) == 0
        assert len(result2.removed_files) == 0
        assert result2.update_needed == False
    
    def test_file_modification_detection(self):
        """测试文件修改检测"""
        # 先更新缓存
        files = self.monitor.scan_tool_files()
        for file_path in files:
            self.monitor.update_file_cache(file_path)
        self.monitor.save_cache()
        
        # 修改一个文件
        python_tool_file = os.path.join(self.temp_dir, "python_tool.yml")
        with open(python_tool_file, 'a', encoding='utf-8') as f:
            f.write("\n# 新增注释")
        
        # 分析变化
        result = analyze_tool_file_changes(self.temp_dir)
        assert len(result.changed_files) == 1
        assert python_tool_file in result.changed_files
        assert result.update_needed == True
    
    def test_file_deletion_detection(self):
        """测试文件删除检测"""
        # 先更新缓存
        files = self.monitor.scan_tool_files()
        for file_path in files:
            self.monitor.update_file_cache(file_path)
        self.monitor.save_cache()
        
        # 删除一个文件
        python_tool_file = os.path.join(self.temp_dir, "python_tool.yml")
        os.remove(python_tool_file)
        
        # 分析变化
        result = analyze_tool_file_changes(self.temp_dir)
        assert len(result.removed_files) == 1
        assert python_tool_file in result.removed_files
        assert result.total_files == 1  # 只剩一个文件
        assert result.update_needed == True


class TestIncrementalUpdateResult:
    """测试增量更新结果"""
    
    def test_empty_result(self):
        """测试空结果"""
        result = IncrementalUpdateResult()
        assert result.has_changes() == False
        assert result.get_summary() == "无文件变化，索引无需更新"
    
    def test_with_changes(self):
        """测试有变化的结果"""
        result = IncrementalUpdateResult()
        result.new_files = ["file1.yml", "file2.yml"]
        result.changed_files = ["file3.yml"]
        result.removed_files = ["file4.yml"]
        result.total_files = 3
        
        assert result.has_changes() == True
        summary = result.get_summary()
        assert "新增 2 个文件" in summary
        assert "修改 1 个文件" in summary
        assert "删除 1 个文件" in summary
    
    def test_to_dict(self):
        """测试转换为字典"""
        result = IncrementalUpdateResult()
        result.new_files = ["file1.yml"]
        result.changed_files = ["file2.yml"]
        result.total_files = 2
        
        data = result.to_dict()
        assert data["new_files"] == ["file1.yml"]
        assert data["changed_files"] == ["file2.yml"]
        assert data["total_files"] == 2
        assert data["update_needed"] == True
        assert "summary" in data


class TestToolIndexManager:
    """测试工具索引管理器"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        # 注意：这里不实际测试向量服务，只测试文件监控部分
    
    def teardown_method(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_incremental_update_enabled_by_default(self):
        """测试默认启用增量更新"""
        manager = ToolIndexManager()
        assert manager.is_incremental_update_enabled() == True
    
    def test_enable_disable_incremental_update(self):
        """测试启用/禁用增量更新"""
        manager = ToolIndexManager()
        
        # 禁用增量更新
        manager.disable_incremental_update()
        assert manager.is_incremental_update_enabled() == False
        
        # 启用增量更新
        manager.enable_incremental_update()
        assert manager.is_incremental_update_enabled() == True
    
    def test_file_monitor_info(self):
        """测试文件监控器信息"""
        manager = ToolIndexManager()
        info = manager.get_file_monitor_info()
        
        assert "total_cached_files" in info
        assert "cache_file" in info
        assert "tools_dir" in info


# 集成测试
class TestIncrementalIndexIntegration:
    """增量索引集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.tools_dir = os.path.join(self.temp_dir, "tools")
        os.makedirs(self.tools_dir, exist_ok=True)
    
    def teardown_method(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_tool(self, filename: str, content: dict):
        """创建测试工具文件"""
        file_path = os.path.join(self.tools_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(content, f, allow_unicode=True)
        return file_path
    
    def test_complete_workflow(self):
        """测试完整工作流程"""
        # 1. 创建初始工具文件
        tool1 = {
            "id": "test.tool1",
            "type": "PYTHON_PACKAGE",
            "summary": "工具1",
            "description": "第一个测试工具"
        }
        self.create_test_tool("tool1.yml", tool1)
        
        # 2. 分析变化（应该是新增）
        result1 = analyze_tool_file_changes(self.tools_dir)
        assert len(result1.new_files) == 1
        assert result1.update_needed == True
        
        # 3. 更新缓存
        monitor = ToolFileMonitor(self.tools_dir)
        for file_path in result1.new_files:
            monitor.update_file_cache(file_path)
        monitor.save_cache()
        
        # 4. 再次分析（应该无变化）
        result2 = analyze_tool_file_changes(self.tools_dir)
        assert result2.update_needed == False
        
        # 5. 添加新工具
        tool2 = {
            "id": "test.tool2",
            "type": "APIS",
            "summary": "工具2",
            "description": "第二个测试工具"
        }
        self.create_test_tool("tool2.yml", tool2)
        
        # 6. 分析变化（应该有新增）
        result3 = analyze_tool_file_changes(self.tools_dir)
        assert len(result3.new_files) == 1
        assert "tool2.yml" in result3.new_files[0]
        assert result3.update_needed == True
        
        # 7. 修改现有工具
        tool1["description"] = "修改后的第一个测试工具"
        self.create_test_tool("tool1.yml", tool1)
        
        # 8. 分析变化（应该有修改）
        result4 = analyze_tool_file_changes(self.tools_dir)
        assert len(result4.changed_files) == 1
        assert "tool1.yml" in result4.changed_files[0]
        assert result4.update_needed == True


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
