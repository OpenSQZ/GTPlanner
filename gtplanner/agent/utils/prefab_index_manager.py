"""
预制件索引管理器

负责预制件索引的生命周期管理：
- 启动时预加载索引
- 检测 community-prefabs.json 变化并自动重建
- 提供索引就绪状态查询
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path


class PrefabIndexManager:
    """预制件索引管理器（单例模式）"""
    
    def __init__(self):
        """初始化索引管理器"""
        self._index_name: Optional[str] = None
        self._index_ready: bool = False
        self._last_prefabs_json_mtime: Optional[float] = None
        self._prefabs_json_path: Optional[Path] = None
        
        # 自动定位 community-prefabs.json
        current_dir = Path(__file__).parent
        self._prefabs_json_path = current_dir.parent.parent.parent / "prefabs" / "releases" / "community-prefabs.json"
    
    async def ensure_index_exists(
        self, 
        prefabs_json_path: str = None,
        force_reindex: bool = False,
        shared: Dict[str, Any] = None
    ) -> str:
        """
        确保预制件索引存在且最新
        
        智能检测逻辑：
        1. 如果索引未初始化，创建索引
        2. 如果 community-prefabs.json 被修改，重建索引
        3. 如果 force_reindex=True，强制重建
        4. 否则，返回现有索引名
        
        Args:
            prefabs_json_path: community-prefabs.json 路径
            force_reindex: 是否强制重建索引
            shared: 共享状态（用于事件发送）
            
        Returns:
            索引名称
        """
        if prefabs_json_path:
            self._prefabs_json_path = Path(prefabs_json_path)
        
        # 检查是否需要重建索引
        needs_rebuild = await self._should_rebuild_index(force_reindex, shared)
        
        if needs_rebuild:
            await self._create_index(shared)
        
        return self._index_name
    
    async def _should_rebuild_index(
        self, 
        force_reindex: bool,
        shared: Dict[str, Any] = None
    ) -> bool:
        """
        判断是否需要重建索引
        
        Returns:
            True: 需要重建, False: 不需要
        """
        # 1. 强制重建
        if force_reindex:
            if shared:
                from gtplanner.agent.streaming import emit_processing_status
                await emit_processing_status(shared, "🔄 强制重建预制件索引...")
            return True
        
        # 2. 索引未初始化
        if not self._index_ready or not self._index_name:
            if shared:
                from gtplanner.agent.streaming import emit_processing_status
                await emit_processing_status(shared, "📦 初始化预制件索引...")
            return True
        
        # 3. 检查 JSON 文件是否被修改
        if not self._prefabs_json_path.exists():
            return False
        
        current_mtime = self._prefabs_json_path.stat().st_mtime
        if self._last_prefabs_json_mtime is None or current_mtime > self._last_prefabs_json_mtime:
            if shared:
                from gtplanner.agent.streaming import emit_processing_status
                await emit_processing_status(shared, "🔄 检测到预制件更新，重建索引...")
            return True
        
        # 4. 索引已存在且最新
        return False
    
    async def _create_index(self, shared: Dict[str, Any] = None):
        """
        创建预制件索引
        
        Args:
            shared: 共享状态（用于事件发送）
        """
        try:
            from gtplanner.agent.utils.prefab_indexer import build_prefab_index
            
            if shared:
                from gtplanner.agent.streaming import emit_processing_status
                await emit_processing_status(shared, "🔨 开始构建预制件索引...")
            
            # 构建索引
            result = build_prefab_index(
                json_path=str(self._prefabs_json_path),
                force_reindex=True
            )
            
            if result.get("success"):
                self._index_name = result["index_name"]
                self._index_ready = True
                self._last_prefabs_json_mtime = self._prefabs_json_path.stat().st_mtime
                
                if shared:
                    from gtplanner.agent.streaming import emit_processing_status
                    await emit_processing_status(
                        shared, 
                        f"✅ 索引构建完成: {self._index_name} ({result['indexed_count']} 个预制件)"
                    )
            else:
                error_msg = result.get("error", "Unknown error")
                self._index_ready = False
                
                if shared:
                    from gtplanner.agent.streaming import emit_error
                    await emit_error(shared, f"❌ 索引构建失败: {error_msg}")
                
                raise RuntimeError(f"Failed to build prefab index: {error_msg}")
                
        except Exception as e:
            self._index_ready = False
            if shared:
                from gtplanner.agent.streaming import emit_error
                await emit_error(shared, f"❌ 索引构建异常: {str(e)}")
            raise
    
    def get_current_index_name(self) -> Optional[str]:
        """获取当前索引名称"""
        return self._index_name if self._index_ready else None
    
    def is_index_ready(self) -> bool:
        """检查索引是否就绪"""
        return self._index_ready
    
    def get_index_info(self) -> Dict[str, Any]:
        """获取索引信息"""
        return {
            "index_name": self._index_name,
            "ready": self._index_ready,
            "prefabs_json_path": str(self._prefabs_json_path),
            "last_modified": self._last_prefabs_json_mtime
        }
    
    async def force_refresh_index(
        self, 
        prefabs_json_path: str = None,
        shared: Dict[str, Any] = None
    ) -> str:
        """
        强制刷新索引
        
        Args:
            prefabs_json_path: community-prefabs.json 路径
            shared: 共享状态
            
        Returns:
            索引名称
        """
        return await self.ensure_index_exists(
            prefabs_json_path, 
            force_reindex=True, 
            shared=shared
        )
    
    def reset(self):
        """重置管理器状态"""
        self._index_name = None
        self._index_ready = False
        self._last_prefabs_json_mtime = None


# 全局单例
prefab_index_manager = PrefabIndexManager()


# 便捷函数
async def ensure_prefab_index(
    prefabs_json_path: str = None,
    force_reindex: bool = False,
    shared: Dict[str, Any] = None
) -> str:
    """
    确保预制件索引存在（便捷函数）
    
    Args:
        prefabs_json_path: community-prefabs.json 路径
        force_reindex: 是否强制重建
        shared: 共享状态
        
    Returns:
        索引名称
    """
    return await prefab_index_manager.ensure_index_exists(
        prefabs_json_path, 
        force_reindex, 
        shared
    )


async def get_prefab_index_name() -> Optional[str]:
    """获取当前预制件索引名称"""
    return prefab_index_manager.get_current_index_name()


def is_prefab_index_ready() -> bool:
    """检查预制件索引是否就绪"""
    return prefab_index_manager.is_index_ready()

