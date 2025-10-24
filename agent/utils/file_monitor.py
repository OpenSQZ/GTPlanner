"""
文件监控和校验和计算模块

为工具索引增量更新提供文件变化检测和校验和计算功能。
支持高效的文件变化监控，避免不必要的索引重建。
"""

import os
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime


class FileChecksumManager:
    """文件校验和管理器"""
    
    def __init__(self, cache_file: str = "tool_checksums.json"):
        self.cache_file = cache_file
        self.checksums: Dict[str, str] = {}
        self.file_timestamps: Dict[str, float] = {}
        self._load_cache()
    
    def _load_cache(self):
        """从缓存文件加载校验和"""
        if os.path.exists(self.cache_file):
            try:
                import json
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.checksums = data.get('checksums', {})
                    self.file_timestamps = data.get('timestamps', {})
            except Exception as e:
                print(f"⚠️ 加载校验和缓存失败: {e}")
                self.checksums = {}
                self.file_timestamps = {}
    
    def _save_cache(self):
        """保存校验和到缓存文件"""
        try:
            import json
            data = {
                'checksums': self.checksums,
                'timestamps': self.file_timestamps,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存校验和缓存失败: {e}")
    
    def calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            print(f"⚠️ 计算文件校验和失败 {file_path}: {e}")
            return ""
    
    def get_file_timestamp(self, file_path: str) -> float:
        """获取文件修改时间"""
        try:
            return os.path.getmtime(file_path)
        except Exception:
            return 0.0
    
    def is_file_changed(self, file_path: str) -> bool:
        """检查文件是否发生变化"""
        if not os.path.exists(file_path):
            return True
        
        current_checksum = self.calculate_checksum(file_path)
        current_timestamp = self.get_file_timestamp(file_path)
        
        cached_checksum = self.checksums.get(file_path)
        cached_timestamp = self.file_timestamps.get(file_path, 0.0)
        
        # 如果校验和不同，文件已变化
        if current_checksum != cached_checksum:
            return True
        
        # 如果时间戳不同但校验和相同，可能是文件被快速重写
        if current_timestamp != cached_timestamp:
            return True
        
        return False
    
    def update_file_info(self, file_path: str):
        """更新文件信息到缓存"""
        if os.path.exists(file_path):
            self.checksums[file_path] = self.calculate_checksum(file_path)
            self.file_timestamps[file_path] = self.get_file_timestamp(file_path)
    
    def remove_file_info(self, file_path: str):
        """从缓存中移除文件信息"""
        self.checksums.pop(file_path, None)
        self.file_timestamps.pop(file_path, None)
    
    def save_changes(self):
        """保存所有更改到缓存文件"""
        self._save_cache()


class ToolFileMonitor:
    """工具文件监控器"""
    
    def __init__(self, tools_dir: str = "tools"):
        self.tools_dir = tools_dir
        self.checksum_manager = FileChecksumManager()
        self.supported_extensions = {'.yml', '.yaml'}
    
    def scan_tool_files(self) -> List[str]:
        """扫描所有工具文件"""
        if not os.path.exists(self.tools_dir):
            return []
        
        tool_files = []
        for root, dirs, files in os.walk(self.tools_dir):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    file_path = os.path.join(root, file)
                    tool_files.append(file_path)
        
        return sorted(tool_files)
    
    def get_changed_files(self) -> List[str]:
        """获取发生变化的文件列表"""
        all_files = self.scan_tool_files()
        changed_files = []
        
        for file_path in all_files:
            if self.checksum_manager.is_file_changed(file_path):
                changed_files.append(file_path)
        
        return changed_files
    
    def get_removed_files(self) -> List[str]:
        """获取被删除的文件列表"""
        cached_files = set(self.checksum_manager.checksums.keys())
        current_files = set(self.scan_tool_files())
        
        removed_files = list(cached_files - current_files)
        return removed_files
    
    def get_new_files(self) -> List[str]:
        """获取新增的文件列表"""
        cached_files = set(self.checksum_manager.checksums.keys())
        current_files = set(self.scan_tool_files())
        
        new_files = list(current_files - cached_files)
        return new_files
    
    def update_file_cache(self, file_path: str):
        """更新单个文件的缓存信息"""
        self.checksum_manager.update_file_info(file_path)
    
    def remove_file_cache(self, file_path: str):
        """从缓存中移除文件信息"""
        self.checksum_manager.remove_file_info(file_path)
    
    def save_cache(self):
        """保存缓存到文件"""
        self.checksum_manager.save_changes()
    
    def get_cache_info(self) -> Dict[str, any]:
        """获取缓存信息"""
        return {
            'total_cached_files': len(self.checksum_manager.checksums),
            'cache_file': self.checksum_manager.cache_file,
            'tools_dir': self.tools_dir,
            'last_scan_time': max(self.checksum_manager.file_timestamps.values()) if self.checksum_manager.file_timestamps else 0
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.checksum_manager.checksums.clear()
        self.checksum_manager.file_timestamps.clear()
        self.checksum_manager.save_changes()


class IncrementalUpdateResult:
    """增量更新结果"""
    
    def __init__(self):
        self.new_files: List[str] = []
        self.changed_files: List[str] = []
        self.removed_files: List[str] = []
        self.unchanged_files: List[str] = []
        self.total_files: int = 0
        self.update_needed: bool = False
    
    def has_changes(self) -> bool:
        """是否有变化需要更新"""
        return len(self.new_files) > 0 or len(self.changed_files) > 0 or len(self.removed_files) > 0
    
    def get_summary(self) -> str:
        """获取更新摘要"""
        if not self.has_changes():
            return "无文件变化，索引无需更新"
        
        parts = []
        if self.new_files:
            parts.append(f"新增 {len(self.new_files)} 个文件")
        if self.changed_files:
            parts.append(f"修改 {len(self.changed_files)} 个文件")
        if self.removed_files:
            parts.append(f"删除 {len(self.removed_files)} 个文件")
        
        return f"检测到变化: {', '.join(parts)}"
    
    def to_dict(self) -> Dict[str, any]:
        """转换为字典"""
        return {
            'new_files': self.new_files,
            'changed_files': self.changed_files,
            'removed_files': self.removed_files,
            'unchanged_files': self.unchanged_files,
            'total_files': self.total_files,
            'update_needed': self.update_needed,
            'summary': self.get_summary()
        }


def analyze_tool_file_changes(tools_dir: str = "tools") -> IncrementalUpdateResult:
    """分析工具文件变化"""
    monitor = ToolFileMonitor(tools_dir)
    result = IncrementalUpdateResult()
    
    # 获取所有当前文件
    all_files = monitor.scan_tool_files()
    result.total_files = len(all_files)
    
    # 检查新增文件
    result.new_files = monitor.get_new_files()
    
    # 检查修改文件
    result.changed_files = monitor.get_changed_files()
    
    # 检查删除文件
    result.removed_files = monitor.get_removed_files()
    
    # 计算未变化文件
    changed_set = set(result.new_files + result.changed_files + result.removed_files)
    result.unchanged_files = [f for f in all_files if f not in changed_set]
    
    # 判断是否需要更新
    result.update_needed = result.has_changes()
    
    return result


if __name__ == "__main__":
    # 测试文件监控功能
    print("🧪 测试工具文件监控功能")
    print("=" * 50)
    
    result = analyze_tool_file_changes()
    print(f"📊 分析结果:")
    print(f"  总文件数: {result.total_files}")
    print(f"  新增文件: {len(result.new_files)}")
    print(f"  修改文件: {len(result.changed_files)}")
    print(f"  删除文件: {len(result.removed_files)}")
    print(f"  未变化文件: {len(result.unchanged_files)}")
    print(f"  需要更新: {result.update_needed}")
    print(f"  摘要: {result.get_summary()}")
    
    if result.new_files:
        print(f"\n📁 新增文件:")
        for file in result.new_files:
            print(f"  + {file}")
    
    if result.changed_files:
        print(f"\n📝 修改文件:")
        for file in result.changed_files:
            print(f"  ~ {file}")
    
    if result.removed_files:
        print(f"\n🗑️ 删除文件:")
        for file in result.removed_files:
            print(f"  - {file}")
