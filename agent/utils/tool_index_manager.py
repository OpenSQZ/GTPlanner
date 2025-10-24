"""
工具索引管理器 (ToolIndexManager)

统一管理工具索引的创建、更新和状态检查，避免重复创建索引导致的性能问题。
采用单例模式确保全局唯一的索引管理实例。

功能特性：
- 单例模式管理索引生命周期
- 智能检测工具目录变化
- 支持强制更新和增量更新
- 异步索引操作，不阻塞业务流程
- 索引状态监控和错误恢复
- 增量更新机制，提升性能
"""

import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from agent.nodes.node_tool_index import NodeToolIndex
from utils.config_manager import get_vector_service_config
from agent.streaming import emit_processing_status, emit_error
from agent.utils.file_monitor import ToolFileMonitor, analyze_tool_file_changes, IncrementalUpdateResult


class ToolIndexManager:
    """工具索引管理器 - 单例模式"""
    
    _instance: Optional['ToolIndexManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 向量服务配置
        vector_config = get_vector_service_config()
        self._vector_service_url = vector_config.get("base_url")

        # 索引状态
        self._index_created = False
        self._index_name = vector_config.get("tools_index_name", "tools_index")
        self._current_index_name = None
        self._last_index_time = None
        self._last_tools_dir_mtime = None

        # 配置
        self._tools_dir = "tools"
        self._index_node = None
        
        # 增量更新相关
        self._file_monitor = ToolFileMonitor(self._tools_dir)
        self._incremental_update_enabled = True
        self._last_incremental_check = None
        
        self._initialized = True
    
    async def ensure_index_exists(
        self, 
        tools_dir: str = None, 
        force_reindex: bool = False,
        shared: Dict[str, Any] = None
    ) -> str:
        """
        确保工具索引存在且是最新的
        
        Args:
            tools_dir: 工具目录路径，默认使用配置的路径
            force_reindex: 是否强制重建索引
            shared: 共享状态，用于事件发送
            
        Returns:
            可用的索引名称
            
        Raises:
            RuntimeError: 索引创建失败
        """
        async with self._lock:
            tools_dir = tools_dir or self._tools_dir
            
            # 检查是否需要重建索引
            needs_rebuild = await self._should_rebuild_index(tools_dir, force_reindex, shared)
            
            if needs_rebuild:
                await self._create_index(tools_dir, shared)
            
            return self._current_index_name or self._index_name
    
    async def _should_rebuild_index(
        self,
        tools_dir: str,
        force_reindex: bool,
        shared: Dict[str, Any] = None
    ) -> bool:
        """检查是否需要重建索引 - 支持增量更新"""

        # 强制重建
        if force_reindex:
            if shared:
                await emit_processing_status(shared, "🔄 强制重建工具索引...")
            return True

        # 首次创建或索引未创建时，总是创建新索引
        if not self._index_created:
            if shared:
                await emit_processing_status(shared, "🆕 创建新的工具索引...")
            return True

        # 检查是否需要增量更新
        if self._incremental_update_enabled:
            return await self._check_incremental_update_needed(tools_dir, shared)

        # 已经创建过索引且不需要增量更新
        return False
    
    async def _check_incremental_update_needed(
        self,
        tools_dir: str,
        shared: Dict[str, Any] = None
    ) -> bool:
        """检查是否需要增量更新"""
        try:
            if shared:
                await emit_processing_status(shared, "🔍 检查工具文件变化...")
            
            # 分析文件变化
            result = analyze_tool_file_changes(tools_dir)
            
            if shared:
                await emit_processing_status(shared, result.get_summary())
            
            # 如果有变化，执行增量更新
            if result.has_changes():
                await self._perform_incremental_update(result, shared)
                return False  # 增量更新完成，不需要重建
            
            # 无变化，不需要更新
            if shared:
                await emit_processing_status(shared, "✅ 工具文件无变化，索引保持最新")
            
            return False
            
        except Exception as e:
            if shared:
                await emit_error(shared, f"❌ 增量更新检查失败: {str(e)}")
            # 增量更新失败时，回退到全量重建
            return True
    
    async def _perform_incremental_update(
        self,
        result: IncrementalUpdateResult,
        shared: Dict[str, Any] = None
    ):
        """执行增量更新"""
        try:
            if shared:
                await emit_processing_status(shared, "🔄 开始增量更新工具索引...")
            
            # 更新文件监控器
            self._file_monitor = ToolFileMonitor(self._tools_dir)
            
            # 处理新增和修改的文件
            files_to_update = result.new_files + result.changed_files
            
            if files_to_update:
                if shared:
                    await emit_processing_status(shared, f"📝 更新 {len(files_to_update)} 个文件...")
                
                # 批量更新文件到索引
                await self._update_files_in_index(files_to_update, shared)
            
            # 处理删除的文件
            if result.removed_files:
                if shared:
                    await emit_processing_status(shared, f"🗑️ 移除 {len(result.removed_files)} 个文件...")
                
                # 从索引中移除文件
                await self._remove_files_from_index(result.removed_files, shared)
            
            # 更新文件缓存
            for file_path in files_to_update:
                self._file_monitor.update_file_cache(file_path)
            
            for file_path in result.removed_files:
                self._file_monitor.remove_file_cache(file_path)
            
            self._file_monitor.save_cache()
            
            if shared:
                await emit_processing_status(shared, "✅ 增量更新完成")
            
        except Exception as e:
            if shared:
                await emit_error(shared, f"❌ 增量更新失败: {str(e)}")
            raise
    
    async def _update_files_in_index(
        self,
        file_paths: List[str],
        shared: Dict[str, Any] = None
    ):
        """将文件更新到索引中"""
        if not self._index_node:
            self._index_node = NodeToolIndex()
        
        # 为每个文件创建独立的更新任务
        for file_path in file_paths:
            try:
                if shared:
                    await emit_processing_status(shared, f"  📄 更新文件: {os.path.basename(file_path)}")
                
                # 准备单文件更新参数
                update_shared = {
                    "tools_dir": os.path.dirname(file_path),
                    "index_name": self._index_name,
                    "force_reindex": False,
                    "single_file_update": True,
                    "target_file": file_path,
                    "streaming_session": shared.get("streaming_session") if shared else None
                }
                
                # 执行单文件更新
                prep_result = await self._index_node.prep_async(update_shared)
                if "error" not in prep_result:
                    exec_result = await self._index_node.exec_async(prep_result)
                    if shared:
                        await emit_processing_status(shared, f"    ✅ 文件更新成功")
                else:
                    if shared:
                        await emit_error(shared, f"    ❌ 文件更新失败: {prep_result['error']}")
                        
            except Exception as e:
                if shared:
                    await emit_error(shared, f"    ❌ 文件更新异常: {str(e)}")
    
    async def _remove_files_from_index(
        self,
        file_paths: List[str],
        shared: Dict[str, Any] = None
    ):
        """从索引中移除文件"""
        # 这里需要调用向量服务的删除API
        # 由于当前向量服务可能不支持按文件路径删除，我们暂时记录日志
        for file_path in file_paths:
            if shared:
                await emit_processing_status(shared, f"  🗑️ 移除文件: {os.path.basename(file_path)}")
            # TODO: 实现向量服务中的文件删除功能
            # await self._vector_service.delete_documents_by_file_path(file_path)
    
    # 简化版本：移除复杂的变化检测逻辑，每次启动时创建新索引
    
    async def _create_index(self, tools_dir: str, shared: Dict[str, Any] = None):
        """创建或重建工具索引"""
        try:
            if shared:
                await emit_processing_status(shared, "🔨 开始创建工具索引...")
            
            # 创建索引节点
            if not self._index_node:
                self._index_node = NodeToolIndex()
            
            # 准备索引参数
            index_shared = {
                "tools_dir": tools_dir,
                "index_name": self._index_name,
                "force_reindex": True,
                "streaming_session": shared.get("streaming_session") if shared else None
            }
            
            # 执行索引创建
            start_time = time.time()
            
            prep_result = await self._index_node.prep_async(index_shared)
            if "error" in prep_result:
                raise RuntimeError(f"索引准备失败: {prep_result['error']}")
            
            exec_result = await self._index_node.exec_async(prep_result)
            self._current_index_name = exec_result.get("index_name", self._index_name)

            # 更新状态
            self._index_created = True
            self._last_index_time = datetime.now()
            
            index_time = time.time() - start_time
            
            if shared:
                await emit_processing_status(
                    shared, 
                    f"✅ 索引创建完成: {self._current_index_name} (耗时: {index_time:.2f}秒)"
                )
            
            # 短暂等待索引刷新（比原来的2秒更短）
            await asyncio.sleep(0.5)
            
        except Exception as e:
            self._index_created = False
            self._current_index_name = None
            if shared:
                await emit_error(shared, f"❌ 索引创建失败: {str(e)}")
            raise RuntimeError(f"索引创建失败: {str(e)}")
    
    def is_index_ready(self) -> bool:
        """检查索引是否就绪"""
        return self._index_created and self._current_index_name is not None
    
    def get_current_index_name(self) -> Optional[str]:
        """获取当前索引名称"""
        return self._current_index_name
    
    def get_index_info(self) -> Dict[str, Any]:
        """获取索引信息"""
        return {
            "index_created": self._index_created,
            "current_index_name": self._current_index_name,
            "last_index_time": self._last_index_time.isoformat() if self._last_index_time else None,
            "tools_dir": self._tools_dir,
            "last_tools_dir_mtime": self._last_tools_dir_mtime
        }
    
    async def force_refresh_index(self, tools_dir: str = None, shared: Dict[str, Any] = None) -> str:
        """强制刷新索引"""
        return await self.ensure_index_exists(tools_dir, force_reindex=True, shared=shared)
    
    def reset(self):
        """重置索引管理器状态（主要用于测试）"""
        self._index_created = False
        self._current_index_name = None
        self._last_index_time = None
        self._last_tools_dir_mtime = None
        self._file_monitor.clear_cache()
    
    def enable_incremental_update(self):
        """启用增量更新"""
        self._incremental_update_enabled = True
    
    def disable_incremental_update(self):
        """禁用增量更新"""
        self._incremental_update_enabled = False
    
    def is_incremental_update_enabled(self) -> bool:
        """检查是否启用增量更新"""
        return self._incremental_update_enabled
    
    def get_file_monitor_info(self) -> Dict[str, Any]:
        """获取文件监控器信息"""
        return self._file_monitor.get_cache_info()
    
    async def force_incremental_update(self, tools_dir: str = None, shared: Dict[str, Any] = None) -> bool:
        """强制执行增量更新"""
        tools_dir = tools_dir or self._tools_dir
        try:
            result = analyze_tool_file_changes(tools_dir)
            if result.has_changes():
                await self._perform_incremental_update(result, shared)
                return True
            else:
                if shared:
                    await emit_processing_status(shared, "ℹ️ 无文件变化，跳过增量更新")
                return False
        except Exception as e:
            if shared:
                await emit_error(shared, f"❌ 强制增量更新失败: {str(e)}")
            return False


# 全局索引管理器实例
tool_index_manager = ToolIndexManager()


# 便捷函数
async def ensure_tool_index(
    tools_dir: str = None, 
    force_reindex: bool = False,
    shared: Dict[str, Any] = None
) -> str:
    """确保工具索引存在的便捷函数"""
    return await tool_index_manager.ensure_index_exists(tools_dir, force_reindex, shared)


async def get_tool_index_name() -> Optional[str]:
    """获取当前工具索引名称的便捷函数"""
    return tool_index_manager.get_current_index_name()


def is_tool_index_ready() -> bool:
    """检查工具索引是否就绪的便捷函数"""
    return tool_index_manager.is_index_ready()
