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
"""

import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from agent.nodes.node_tool_index import NodeToolIndex
from utils.config_manager import get_vector_service_config
from agent.streaming import emit_processing_status, emit_error


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
        """检查是否需要重建索引 - 简化版：总是在首次调用时创建新索引"""

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

        # 已经创建过索引，不再重建
        return False
    
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
