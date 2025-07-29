"""
缓存管理器
提供内存缓存和文件缓存功能，提高系统性能
"""

import json
import pickle
import hashlib
import time
import logging
from typing import Any, Optional, Dict, List
from pathlib import Path
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache", max_memory_size: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_memory_size = max_memory_size
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        if key in self.memory_cache:
            cache_item = self.memory_cache[key]
            if cache_item['expires_at'] > time.time():
                self.cache_stats['hits'] += 1
                return cache_item['value']
            else:
                # 过期，删除
                del self.memory_cache[key]
        
        # 尝试从文件缓存获取
        file_path = self.cache_dir / f"{key}.pkl"
        if file_path.exists():
            try:
                with open(file_path, 'rb') as f:
                    cache_item = pickle.load(f)
                if cache_item['expires_at'] > time.time():
                    # 加载到内存缓存
                    self._set_memory_cache(key, cache_item['value'], cache_item['expires_at'])
                    self.cache_stats['hits'] += 1
                    return cache_item['value']
                else:
                    # 过期，删除文件
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"读取文件缓存失败: {e}")
        
        self.cache_stats['misses'] += 1
        return default
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """设置缓存值"""
        expires_at = time.time() + ttl
        
        # 设置内存缓存
        self._set_memory_cache(key, value, expires_at)
        
        # 设置文件缓存
        file_path = self.cache_dir / f"{key}.pkl"
        try:
            cache_item = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            with open(file_path, 'wb') as f:
                pickle.dump(cache_item, f)
        except Exception as e:
            logger.warning(f"写入文件缓存失败: {e}")
    
    def _set_memory_cache(self, key: str, value: Any, expires_at: float) -> None:
        """设置内存缓存"""
        # 检查内存缓存大小
        if len(self.memory_cache) >= self.max_memory_size:
            # 删除最旧的缓存项
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]['expires_at'])
            del self.memory_cache[oldest_key]
            self.cache_stats['evictions'] += 1
        
        self.memory_cache[key] = {
            'value': value,
            'expires_at': expires_at
        }
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        # 删除内存缓存
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # 删除文件缓存
        file_path = self.cache_dir / f"{key}.pkl"
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        self.memory_cache.clear()
        
        # 清空文件缓存
        for file_path in self.cache_dir.glob("*.pkl"):
            file_path.unlink()
        
        logger.info("缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'memory_cache_size': len(self.memory_cache),
            'file_cache_count': len(list(self.cache_dir.glob("*.pkl"))),
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'hit_rate': f"{hit_rate:.2%}",
            'total_requests': total_requests
        }
    
    def cleanup_expired(self) -> int:
        """清理过期缓存"""
        cleaned_count = 0
        
        # 清理内存缓存
        expired_keys = [
            key for key, item in self.memory_cache.items()
            if item['expires_at'] <= time.time()
        ]
        for key in expired_keys:
            del self.memory_cache[key]
            cleaned_count += 1
        
        # 清理文件缓存
        for file_path in self.cache_dir.glob("*.pkl"):
            try:
                with open(file_path, 'rb') as f:
                    cache_item = pickle.load(f)
                if cache_item['expires_at'] <= time.time():
                    file_path.unlink()
                    cleaned_count += 1
            except Exception:
                # 文件损坏，删除
                file_path.unlink()
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 个过期缓存")
        
        return cleaned_count


# 全局缓存实例
cache_manager = CacheManager()


def cached(ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}_{cache_manager._generate_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class QueryCache:
    """查询缓存专用类"""
    
    def __init__(self):
        self.cache_manager = cache_manager
    
    def get_cached_answer(self, question: str, relevant_docs: List[Dict]) -> Optional[str]:
        """获取缓存的回答"""
        # 基于问题和相关文档生成缓存键
        docs_hash = hashlib.md5(str(relevant_docs).encode()).hexdigest()
        cache_key = f"query_{hashlib.md5(question.encode()).hexdigest()}_{docs_hash}"
        
        return self.cache_manager.get(cache_key)
    
    def cache_answer(self, question: str, answer: str, relevant_docs: List[Dict], ttl: int = 3600) -> None:
        """缓存回答"""
        docs_hash = hashlib.md5(str(relevant_docs).encode()).hexdigest()
        cache_key = f"query_{hashlib.md5(question.encode()).hexdigest()}_{docs_hash}"
        
        self.cache_manager.set(cache_key, answer, ttl)
    
    def get_badcase_stats(self) -> Dict[str, Any]:
        """获取BadCase统计信息（缓存）"""
        cache_key = "badcase_stats"
        cached_stats = self.cache_manager.get(cache_key)
        if cached_stats is not None:
            return cached_stats
        
        # 这里应该调用实际的统计函数
        # 暂时返回空结果
        stats = {'total_count': 0, 'feedback_stats': {}, 'user_stats': {}}
        self.cache_manager.set(cache_key, stats, ttl=300)  # 5分钟缓存
        return stats 