"""
高级缓存系统

为GTPlanner提供高性能、智能的缓存机制，支持：
- LRU缓存策略
- TTL过期机制
- 异步缓存操作
- 缓存预热和统计
- 内存使用监控
"""

import asyncio
import time
import json
import hashlib
from typing import Any, Dict, Optional, Callable, Union, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def update_access(self):
        """更新访问信息"""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    
    def update_hit_rate(self):
        """更新命中率"""
        total = self.hits + self.misses
        self.hit_rate = self.hits / total if total > 0 else 0.0


class AdvancedCache:
    """高级缓存系统"""
    
    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: int = 100,
        default_ttl: Optional[float] = None,
        enable_stats: bool = True
    ):
        """
        初始化缓存
        
        Args:
            max_size: 最大条目数
            max_memory_mb: 最大内存使用量（MB）
            default_ttl: 默认TTL（秒）
            enable_stats: 是否启用统计
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.enable_stats = enable_stats
        
        # 使用OrderedDict实现LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # 统计信息
        self.stats = CacheStats() if enable_stats else None
        
        # 缓存键生成器
        self._key_generators: Dict[str, Callable] = {}
        
        logger.info(f"高级缓存系统初始化完成: max_size={max_size}, max_memory={max_memory_mb}MB")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 如果有自定义生成器，使用它
        if prefix in self._key_generators:
            return self._key_generators[prefix](*args, **kwargs)
        
        # 默认生成器：基于参数哈希
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else []
        }
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def register_key_generator(self, prefix: str, generator: Callable):
        """注册自定义键生成器"""
        self._key_generators[prefix] = generator
    
    def _estimate_size(self, value: Any) -> int:
        """估算值的大小（字节）"""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (dict, list)):
                return len(json.dumps(value, ensure_ascii=False).encode('utf-8'))
            elif isinstance(value, bytes):
                return len(value)
            else:
                return len(str(value).encode('utf-8'))
        except Exception:
            return 1024  # 默认大小
    
    def _evict_if_needed(self):
        """如果需要则驱逐条目"""
        with self._lock:
            # 检查条目数量限制
            while len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # 检查内存限制
            while self.stats.total_size_bytes >= self.max_memory_bytes:
                self._evict_lru()
    
    def _evict_lru(self):
        """驱逐最近最少使用的条目"""
        if not self._cache:
            return
        
        # 移除最旧的条目
        key, entry = self._cache.popitem(last=False)
        
        # 更新统计
        if self.stats:
            self.stats.evictions += 1
            self.stats.total_size_bytes -= entry.size_bytes
            self.stats.entry_count -= 1
        
        logger.debug(f"驱逐缓存条目: {key}")
    
    def _cleanup_expired(self):
        """清理过期条目"""
        expired_keys = []
        
        with self._lock:
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
    
    def _remove_entry(self, key: str):
        """移除条目"""
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                if self.stats:
                    self.stats.total_size_bytes -= entry.size_bytes
                    self.stats.entry_count -= 1
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                if self.stats:
                    self.stats.misses += 1
                    self.stats.update_hit_rate()
                return None
            
            entry = self._cache[key]
            
            # 检查是否过期
            if entry.is_expired():
                self._remove_entry(key)
                if self.stats:
                    self.stats.misses += 1
                    self.stats.update_hit_rate()
                return None
            
            # 更新访问信息并移到末尾（LRU）
            entry.update_access()
            self._cache.move_to_end(key)
            
            if self.stats:
                self.stats.hits += 1
                self.stats.update_hit_rate()
            
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        size_bytes: Optional[int] = None
    ):
        """设置缓存值"""
        # 使用提供的TTL或默认TTL
        actual_ttl = ttl if ttl is not None else self.default_ttl
        
        # 估算大小
        actual_size = size_bytes if size_bytes is not None else self._estimate_size(value)
        
        # 创建缓存条目
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            last_accessed=time.time(),
            ttl=actual_ttl,
            size_bytes=actual_size
        )
        
        with self._lock:
            # 如果键已存在，先移除旧条目
            if key in self._cache:
                old_entry = self._cache[key]
                self.stats.total_size_bytes -= old_entry.size_bytes
                self.stats.entry_count -= 1
            
            # 添加新条目
            self._cache[key] = entry
            
            if self.stats:
                self.stats.total_size_bytes += actual_size
                self.stats.entry_count += 1
        
        # 检查是否需要驱逐
        self._evict_if_needed()
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            if self.stats:
                self.stats.total_size_bytes = 0
                self.stats.entry_count = 0
    
    def get_stats(self) -> Optional[CacheStats]:
        """获取缓存统计信息"""
        if not self.stats:
            return None
        
        # 清理过期条目
        self._cleanup_expired()
        
        return CacheStats(
            hits=self.stats.hits,
            misses=self.stats.misses,
            evictions=self.stats.evictions,
            total_size_bytes=self.stats.total_size_bytes,
            entry_count=self.stats.entry_count,
            hit_rate=self.stats.hit_rate
        )
    
    def warm_up(self, warm_up_data: Dict[str, Any]):
        """缓存预热"""
        logger.info(f"开始缓存预热，数据量: {len(warm_up_data)}")
        
        for key, value in warm_up_data.items():
            self.set(key, value)
        
        logger.info("缓存预热完成")
    
    def get_memory_usage_mb(self) -> float:
        """获取内存使用量（MB）"""
        if self.stats:
            return self.stats.total_size_bytes / (1024 * 1024)
        return 0.0


class AsyncCacheWrapper:
    """异步缓存包装器"""
    
    def __init__(self, cache: AdvancedCache):
        self.cache = cache
        self._executor = None
    
    def _get_executor(self):
        """获取线程池执行器"""
        if self._executor is None:
            self._executor = asyncio.get_event_loop().run_in_executor
        return self._executor
    
    async def get(self, key: str) -> Optional[Any]:
        """异步获取缓存值"""
        executor = self._get_executor()
        return await executor(None, self.cache.get, key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        size_bytes: Optional[int] = None
    ):
        """异步设置缓存值"""
        executor = self._get_executor()
        await executor(None, self.cache.set, key, value, ttl, size_bytes)
    
    async def delete(self, key: str) -> bool:
        """异步删除缓存条目"""
        executor = self._get_executor()
        return await executor(None, self.cache.delete, key)
    
    async def clear(self):
        """异步清空缓存"""
        executor = self._get_executor()
        await executor(None, self.cache.clear)
    
    async def get_stats(self) -> Optional[CacheStats]:
        """异步获取统计信息"""
        executor = self._get_executor()
        return await executor(None, self.cache.get_stats)


# 全局缓存实例
_global_cache: Optional[AdvancedCache] = None
_async_cache: Optional[AsyncCacheWrapper] = None


def get_global_cache() -> AdvancedCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = AdvancedCache(
            max_size=2000,
            max_memory_mb=200,
            default_ttl=3600,  # 1小时
            enable_stats=True
        )
    return _global_cache


def get_async_cache() -> AsyncCacheWrapper:
    """获取异步缓存实例"""
    global _async_cache
    if _async_cache is None:
        cache = get_global_cache()
        _async_cache = AsyncCacheWrapper(cache)
    return _async_cache


def cache_key(prefix: str, *args, **kwargs) -> str:
    """生成缓存键的便捷函数"""
    cache = get_global_cache()
    return cache._generate_key(prefix, *args, **kwargs)


# 装饰器支持
def cached(
    ttl: Optional[float] = None,
    key_prefix: str = "func",
    cache_instance: Optional[AdvancedCache] = None
):
    """缓存装饰器"""
    def decorator(func: Callable):
        cache = cache_instance or get_global_cache()
        
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = cache._generate_key(key_prefix, func.__name__, *args, **kwargs)
            
            # 尝试从缓存获取
            result = cache.get(key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


def async_cached(
    ttl: Optional[float] = None,
    key_prefix: str = "async_func",
    cache_instance: Optional[AdvancedCache] = None
):
    """异步缓存装饰器"""
    def decorator(func: Callable):
        cache = cache_instance or get_global_cache()
        async_cache = AsyncCacheWrapper(cache)
        
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            key = cache._generate_key(key_prefix, func.__name__, *args, **kwargs)
            
            # 尝试从缓存获取
            result = await async_cache.get(key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await async_cache.set(key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator
