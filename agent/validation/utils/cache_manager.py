"""
高级缓存管理器

基于多种缓存策略的高级缓存管理，提供：
- 内存缓存实现
- 缓存键生成策略
- TTL过期管理
- 缓存命中率统计
- Redis缓存预留接口
- 缓存分层和分区
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Union, Callable
from threading import Lock, RLock
from collections import OrderedDict
from ..core.interfaces import IValidationCache
from ..core.validation_result import ValidationResult


class CacheStats:
    """缓存统计信息"""
    
    def __init__(self):
        self.hit_count = 0
        self.miss_count = 0
        self.set_count = 0
        self.delete_count = 0
        self.expired_count = 0
        self.evicted_count = 0
        self.start_time = time.time()
        self._lock = Lock()
    
    def record_hit(self) -> None:
        """记录缓存命中"""
        with self._lock:
            self.hit_count += 1
    
    def record_miss(self) -> None:
        """记录缓存未命中"""
        with self._lock:
            self.miss_count += 1
    
    def record_set(self) -> None:
        """记录缓存设置"""
        with self._lock:
            self.set_count += 1
    
    def record_delete(self) -> None:
        """记录缓存删除"""
        with self._lock:
            self.delete_count += 1
    
    def record_expired(self) -> None:
        """记录缓存过期"""
        with self._lock:
            self.expired_count += 1
    
    def record_evicted(self) -> None:
        """记录缓存淘汰"""
        with self._lock:
            self.evicted_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
            uptime = time.time() - self.start_time
            
            return {
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "set_count": self.set_count,
                "delete_count": self.delete_count,
                "expired_count": self.expired_count,
                "evicted_count": self.evicted_count,
                "total_requests": total_requests,
                "hit_rate": hit_rate,
                "miss_rate": 1 - hit_rate,
                "uptime_seconds": uptime
            }
    
    def reset(self) -> None:
        """重置统计信息"""
        with self._lock:
            self.hit_count = 0
            self.miss_count = 0
            self.set_count = 0
            self.delete_count = 0
            self.expired_count = 0
            self.evicted_count = 0
            self.start_time = time.time()


class LRUCache:
    """LRU (Least Recently Used) 缓存实现"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()  # (value, expiry_time)
        self._lock = RLock()
        self.stats = CacheStats()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        with self._lock:
            if key not in self._cache:
                self.stats.record_miss()
                return None
            
            value, expiry_time = self._cache[key]
            current_time = time.time()
            
            if current_time > expiry_time:
                # 缓存过期
                del self._cache[key]
                self.stats.record_expired()
                self.stats.record_miss()
                return None
            
            # 移动到末尾（最近使用）
            self._cache.move_to_end(key)
            self.stats.record_hit()
            
            return value
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒）
        """
        with self._lock:
            current_time = time.time()
            expiry_time = current_time + ttl
            
            # 如果键已存在，更新值
            if key in self._cache:
                self._cache[key] = (value, expiry_time)
                self._cache.move_to_end(key)
            else:
                # 检查缓存大小限制
                if len(self._cache) >= self.max_size:
                    # 移除最久未使用的条目
                    oldest_key, _ = self._cache.popitem(last=False)
                    self.stats.record_evicted()
                
                # 添加新条目
                self._cache[key] = (value, expiry_time)
            
            self.stats.record_set()
    
    def delete(self, key: str) -> bool:
        """删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            True表示删除成功，False表示键不存在
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.stats.record_delete()
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            self.stats.evicted_count += cleared_count
    
    def cleanup_expired(self) -> int:
        """清理过期的缓存项
        
        Returns:
            清理的缓存项数量
        """
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, (value, expiry_time) in self._cache.items():
                if current_time > expiry_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self.stats.record_expired()
            
            return len(expired_keys)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息
        
        Returns:
            缓存信息字典
        """
        with self._lock:
            return {
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "stats": self.stats.get_stats()
            }


class PartitionedCache:
    """分区缓存 - 将缓存分为多个分区以提高并发性能"""
    
    def __init__(self, partition_count: int = 16, max_size_per_partition: int = 100):
        self.partition_count = partition_count
        self.partitions: List[LRUCache] = [
            LRUCache(max_size_per_partition) for _ in range(partition_count)
        ]
    
    def _get_partition(self, key: str) -> LRUCache:
        """获取键对应的分区
        
        Args:
            key: 缓存键
            
        Returns:
            对应的LRU缓存分区
        """
        partition_index = hash(key) % self.partition_count
        return self.partitions[partition_index]
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值
        """
        partition = self._get_partition(key)
        return partition.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间
        """
        partition = self._get_partition(key)
        partition.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        partition = self._get_partition(key)
        return partition.delete(key)
    
    def clear(self) -> None:
        """清空所有缓存"""
        for partition in self.partitions:
            partition.clear()
    
    def cleanup_expired(self) -> int:
        """清理所有分区的过期项
        
        Returns:
            清理的总数量
        """
        total_cleaned = 0
        for partition in self.partitions:
            total_cleaned += partition.cleanup_expired()
        return total_cleaned
    
    def get_total_stats(self) -> Dict[str, Any]:
        """获取所有分区的统计信息
        
        Returns:
            总体统计信息
        """
        total_stats = {
            "partition_count": self.partition_count,
            "total_cache_size": 0,
            "total_max_size": 0,
            "aggregated_stats": {
                "hit_count": 0,
                "miss_count": 0,
                "set_count": 0,
                "delete_count": 0,
                "expired_count": 0,
                "evicted_count": 0
            }
        }
        
        for partition in self.partitions:
            cache_info = partition.get_cache_info()
            total_stats["total_cache_size"] += cache_info["cache_size"]
            total_stats["total_max_size"] += cache_info["max_size"]
            
            # 聚合统计信息
            for key, value in cache_info["stats"].items():
                if key in total_stats["aggregated_stats"]:
                    total_stats["aggregated_stats"][key] += value
        
        # 计算总体命中率
        total_requests = (total_stats["aggregated_stats"]["hit_count"] + 
                         total_stats["aggregated_stats"]["miss_count"])
        if total_requests > 0:
            total_stats["aggregated_stats"]["hit_rate"] = (
                total_stats["aggregated_stats"]["hit_count"] / total_requests
            )
        
        return total_stats


class ValidationCacheManager(IValidationCache):
    """验证缓存管理器 - 实现IValidationCache接口的高级缓存管理"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 缓存配置
        self.enabled = self.config.get("enabled", True)
        self.backend = self.config.get("backend", "memory")
        self.default_ttl = self.config.get("default_ttl", 300)
        self.max_size = self.config.get("max_size", 1000)
        self.cleanup_interval = self.config.get("cleanup_interval", 60)
        self.use_partitioned_cache = self.config.get("use_partitioned_cache", True)
        
        # 初始化缓存后端
        if self.use_partitioned_cache:
            partition_count = self.config.get("partition_count", 16)
            max_size_per_partition = max(1, self.max_size // partition_count)
            self.cache = PartitionedCache(partition_count, max_size_per_partition)
        else:
            self.cache = LRUCache(self.max_size)
        
        # 最后清理时间
        self.last_cleanup_time = time.time()
        
        print(f"ValidationCacheManager initialized: backend={self.backend}, max_size={self.max_size}")
    
    async def get(self, key: str) -> Optional[ValidationResult]:
        """获取缓存的验证结果
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的验证结果
        """
        if not self.enabled:
            return None
        
        # 自动清理过期缓存
        await self._auto_cleanup()
        
        cached_value = self.cache.get(key)
        if cached_value and isinstance(cached_value, dict):
            try:
                # 反序列化验证结果
                return self._deserialize_validation_result(cached_value)
            except Exception:
                # 反序列化失败，删除缓存项
                self.cache.delete(key)
                return None
        
        return None
    
    async def set(self, key: str, result: ValidationResult, ttl: int = 300) -> None:
        """设置缓存的验证结果
        
        Args:
            key: 缓存键
            result: 验证结果
            ttl: 生存时间（秒）
        """
        if not self.enabled:
            return
        
        try:
            # 序列化验证结果
            serialized_result = self._serialize_validation_result(result)
            self.cache.set(key, serialized_result, ttl)
        except Exception as e:
            print(f"Warning: Failed to cache validation result: {e}")
    
    async def invalidate(self, pattern: str) -> None:
        """失效匹配模式的缓存
        
        Args:
            pattern: 匹配模式，支持通配符
        """
        if not self.enabled:
            return
        
        # 对于分区缓存，需要遍历所有分区
        if isinstance(self.cache, PartitionedCache):
            for partition in self.cache.partitions:
                await self._invalidate_partition(partition, pattern)
        else:
            await self._invalidate_partition(self.cache, pattern)
    
    async def _invalidate_partition(self, partition: LRUCache, pattern: str) -> None:
        """失效分区中匹配模式的缓存
        
        Args:
            partition: LRU缓存分区
            pattern: 匹配模式
        """
        import re
        
        with partition._lock:
            # 将通配符模式转换为正则表达式
            regex_pattern = pattern.replace("*", ".*").replace("?", ".")
            compiled_pattern = re.compile(f"^{regex_pattern}$")
            
            keys_to_delete = []
            for key in partition._cache.keys():
                if compiled_pattern.match(key):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del partition._cache[key]
                partition.stats.record_delete()
    
    async def clear(self) -> None:
        """清空所有缓存"""
        if self.enabled:
            self.cache.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息字典
        """
        if isinstance(self.cache, PartitionedCache):
            return self.cache.get_total_stats()
        else:
            return self.cache.get_cache_info()
    
    async def _auto_cleanup(self) -> None:
        """自动清理过期缓存"""
        current_time = time.time()
        if current_time - self.last_cleanup_time >= self.cleanup_interval:
            cleaned_count = self.cache.cleanup_expired()
            self.last_cleanup_time = current_time
            
            if cleaned_count > 0:
                print(f"Cache cleanup: removed {cleaned_count} expired items")
    
    def _serialize_validation_result(self, result: ValidationResult) -> Dict[str, Any]:
        """序列化验证结果
        
        Args:
            result: 验证结果
            
        Returns:
            序列化的字典
        """
        return {
            "status": result.status.value,
            "errors": [error.to_dict() for error in result.errors],
            "warnings": [warning.to_dict() for warning in result.warnings],
            "metadata": result.metadata,
            "metrics": result.metrics.to_dict(),
            "request_id": result.request_id,
            "validator_results": {k: v.value for k, v in result.validator_results.items()},
            "execution_order": result.execution_order,
            "cached_at": time.time()
        }
    
    def _deserialize_validation_result(self, data: Dict[str, Any]) -> ValidationResult:
        """反序列化验证结果
        
        Args:
            data: 序列化的数据
            
        Returns:
            ValidationResult实例
        """
        from ..core.validation_result import ValidationStatus, ValidationError, ValidationSeverity, ValidationMetrics
        
        # 重建ValidationResult
        status = ValidationStatus(data["status"])
        
        # 重建错误列表
        errors = []
        for error_data in data.get("errors", []):
            error = ValidationError(
                code=error_data["code"],
                message=error_data["message"],
                field=error_data.get("field"),
                value=error_data.get("value"),
                validator=error_data.get("validator"),
                severity=ValidationSeverity[error_data["severity"]],
                suggestion=error_data.get("suggestion"),
                metadata=error_data.get("metadata", {})
            )
            errors.append(error)
        
        # 重建警告列表
        warnings = []
        for warning_data in data.get("warnings", []):
            warning = ValidationError(
                code=warning_data["code"],
                message=warning_data["message"],
                field=warning_data.get("field"),
                value=warning_data.get("value"),
                validator=warning_data.get("validator"),
                severity=ValidationSeverity[warning_data["severity"]],
                suggestion=warning_data.get("suggestion"),
                metadata=warning_data.get("metadata", {})
            )
            warnings.append(warning)
        
        # 重建指标
        metrics_data = data.get("metrics", {})
        metrics = ValidationMetrics()
        metrics.total_validators = metrics_data.get("total_validators", 0)
        metrics.executed_validators = metrics_data.get("executed_validators", 0)
        metrics.skipped_validators = metrics_data.get("skipped_validators", 0)
        metrics.failed_validators = metrics_data.get("failed_validators", 0)
        metrics.execution_time = metrics_data.get("execution_time", 0.0)
        metrics.cache_hits = metrics_data.get("cache_hits", 0)
        metrics.cache_misses = metrics_data.get("cache_misses", 0)
        
        # 创建ValidationResult
        result = ValidationResult(
            status=status,
            errors=errors,
            warnings=warnings,
            metadata=data.get("metadata", {}),
            metrics=metrics,
            request_id=data.get("request_id")
        )
        
        # 设置其他属性
        result.validator_results = {
            k: ValidationStatus(v) for k, v in data.get("validator_results", {}).items()
        }
        result.execution_order = data.get("execution_order", [])
        
        return result


class CacheKeyGenerator:
    """缓存键生成器 - 生成高质量的缓存键"""
    
    @staticmethod
    def generate_validator_key(validator_name: str, data: Any, config: Dict[str, Any]) -> str:
        """生成验证器缓存键
        
        Args:
            validator_name: 验证器名称
            data: 验证数据
            config: 验证器配置
            
        Returns:
            缓存键字符串
        """
        # 生成数据哈希
        data_hash = CacheKeyGenerator._hash_data(data)
        
        # 生成配置哈希
        config_hash = CacheKeyGenerator._hash_data(config)
        
        # 组合缓存键
        key_string = f"validator:{validator_name}:data:{data_hash}:config:{config_hash}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_chain_key(chain_name: str, context_summary: Dict[str, Any]) -> str:
        """生成验证链缓存键
        
        Args:
            chain_name: 验证链名称
            context_summary: 上下文摘要
            
        Returns:
            缓存键字符串
        """
        context_hash = CacheKeyGenerator._hash_data(context_summary)
        key_string = f"chain:{chain_name}:context:{context_hash}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _hash_data(data: Any) -> str:
        """生成数据哈希
        
        Args:
            data: 待哈希的数据
            
        Returns:
            哈希字符串
        """
        try:
            if isinstance(data, (dict, list)):
                json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
                return hashlib.md5(json_str.encode('utf-8')).hexdigest()[:16]
            else:
                return hashlib.md5(str(data).encode('utf-8')).hexdigest()[:16]
        except Exception:
            return hashlib.md5(str(hash(str(data))).encode('utf-8')).hexdigest()[:16]


def create_cache_manager(config: Optional[Dict[str, Any]] = None) -> ValidationCacheManager:
    """创建缓存管理器的便捷函数
    
    Args:
        config: 缓存配置
        
    Returns:
        缓存管理器实例
    """
    return ValidationCacheManager(config)


def create_partitioned_cache(partition_count: int = 16, max_size_per_partition: int = 100) -> PartitionedCache:
    """创建分区缓存的便捷函数
    
    Args:
        partition_count: 分区数量
        max_size_per_partition: 每个分区的最大大小
        
    Returns:
        分区缓存实例
    """
    return PartitionedCache(partition_count, max_size_per_partition)
