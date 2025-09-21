"""
HTTP连接池管理器

提供全局HTTP连接池管理，支持连接复用、指数退避重试和LRU缓存。
"""

import asyncio
import aiohttp
import time
import hashlib
import json
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConnectionPoolConfig:
    """连接池配置"""
    connector_limit: int = 100  # 总连接数限制
    connector_limit_per_host: int = 30  # 每个主机连接数限制
    timeout_total: int = 60  # 总超时时间（秒）
    timeout_connect: int = 10  # 连接超时时间（秒）
    timeout_sock_read: int = 30  # 读取超时时间（秒）
    keepalive_timeout: int = 30  # 保持连接时间（秒）
    enable_cleanup_closed: bool = True  # 启用清理关闭的连接


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    max_size: int = 1000
    ttl_seconds: int = 300  # 5分钟


class HTTPPoolManager:
    """HTTP连接池管理器"""
    
    _instance: Optional['HTTPPoolManager'] = None
    _lock = asyncio.Lock()
    
    def __init__(
        self,
        pool_config: Optional[ConnectionPoolConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        cache_config: Optional[CacheConfig] = None
    ):
        self.pool_config = pool_config or ConnectionPoolConfig()
        self.retry_config = retry_config or RetryConfig()
        self.cache_config = cache_config or CacheConfig()
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        
        # 缓存
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "retry_attempts": 0,
            "connection_errors": 0,
            "timeout_errors": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }
    
    @classmethod
    async def get_instance(cls) -> 'HTTPPoolManager':
        """获取单例实例"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._initialize()
        return cls._instance
    
    async def _initialize(self):
        """初始化连接池"""
        if self._session is not None:
            return
        
        # 创建TCP连接器
        self._connector = aiohttp.TCPConnector(
            limit=self.pool_config.connector_limit,
            limit_per_host=self.pool_config.connector_limit_per_host,
            keepalive_timeout=self.pool_config.keepalive_timeout,
            enable_cleanup_closed=self.pool_config.enable_cleanup_closed,
            use_dns_cache=True,
            ttl_dns_cache=300,  # DNS缓存5分钟
            family=0  # 支持IPv4和IPv6
        )
        
        # 创建超时配置
        timeout = aiohttp.ClientTimeout(
            total=self.pool_config.timeout_total,
            connect=self.pool_config.timeout_connect,
            sock_read=self.pool_config.timeout_sock_read
        )
        
        # 创建会话
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            headers={
                'User-Agent': 'GTPlanner/1.0 (HTTP Pool Manager)',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate'
            }
        )
        
        logger.info(f"HTTP连接池已初始化 - 最大连接数: {self.pool_config.connector_limit}")
    
    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[str, bytes, Dict]] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            data: 请求数据
            json_data: JSON数据
            params: URL参数
            cache_key: 缓存键（如果提供则启用缓存）
            cache_ttl: 缓存TTL（秒）
            **kwargs: 其他参数
            
        Returns:
            响应数据字典
        """
        await self._initialize()
        
        self.stats["total_requests"] += 1
        
        # 检查缓存
        if cache_key and self.cache_config.enabled:
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                self.stats["cache_hits"] += 1
                return cached_response
            self.stats["cache_misses"] += 1
        
        # 执行请求（带重试）
        response_data = await self._request_with_retry(
            method, url, headers, data, json_data, params, **kwargs
        )
        
        # 缓存响应
        if cache_key and self.cache_config.enabled and response_data.get("success"):
            ttl = cache_ttl or self.cache_config.ttl_seconds
            self._put_to_cache(cache_key, response_data, ttl)
        
        return response_data
    
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]],
        data: Optional[Union[str, bytes, Dict]],
        json_data: Optional[Dict],
        params: Optional[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """带重试的请求执行"""
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                start_time = time.time()
                
                # 执行请求
                async with self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    json=json_data,
                    params=params,
                    **kwargs
                ) as response:
                    
                    # 读取响应
                    response_text = await response.text()
                    
                    # 尝试解析JSON
                    try:
                        response_json = await response.json()
                    except:
                        response_json = None
                    
                    execution_time = time.time() - start_time
                    
                    # 构建响应数据
                    response_data = {
                        "success": response.status < 400,
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "text": response_text,
                        "json": response_json,
                        "execution_time": execution_time,
                        "attempt": attempt + 1
                    }
                    
                    if response_data["success"]:
                        self.stats["successful_requests"] += 1
                        return response_data
                    else:
                        # HTTP错误，但不重试4xx错误
                        if 400 <= response.status < 500:
                            self.stats["failed_requests"] += 1
                            return response_data
                        
                        # 5xx错误，可以重试
                        last_exception = Exception(f"HTTP {response.status}: {response_text}")
                        
            except asyncio.TimeoutError as e:
                self.stats["timeout_errors"] += 1
                last_exception = e
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.retry_config.max_retries + 1}): {url}")
                
            except aiohttp.ClientError as e:
                self.stats["connection_errors"] += 1
                last_exception = e
                logger.warning(f"连接错误 (尝试 {attempt + 1}/{self.retry_config.max_retries + 1}): {e}")
                
            except Exception as e:
                last_exception = e
                logger.error(f"请求异常 (尝试 {attempt + 1}/{self.retry_config.max_retries + 1}): {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.retry_config.max_retries:
                self.stats["retry_attempts"] += 1
                delay = self._calculate_retry_delay(attempt)
                logger.info(f"等待 {delay:.2f} 秒后重试...")
                await asyncio.sleep(delay)
        
        # 所有重试都失败了
        self.stats["failed_requests"] += 1
        return {
            "success": False,
            "error": str(last_exception),
            "attempts": self.retry_config.max_retries + 1
        }
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """计算重试延迟（指数退避）"""
        delay = self.retry_config.base_delay * (
            self.retry_config.exponential_base ** attempt
        )
        delay = min(delay, self.retry_config.max_delay)
        
        # 添加抖动
        if self.retry_config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def _generate_cache_key(self, method: str, url: str, **kwargs) -> str:
        """生成缓存键"""
        cache_data = {
            "method": method,
            "url": url,
            **kwargs
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        if cache_key not in self._cache:
            return None
        
        cache_entry = self._cache[cache_key]
        if time.time() > cache_entry["expires_at"]:
            del self._cache[cache_key]
            return None
        
        return cache_entry["data"]
    
    def _put_to_cache(self, cache_key: str, data: Dict[str, Any], ttl: int):
        """将数据放入缓存"""
        # 清理过期缓存
        self._cleanup_expired_cache()
        
        # 如果缓存已满，删除最旧的条目
        if len(self._cache) >= self.cache_config.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["created_at"])
            del self._cache[oldest_key]
        
        # 添加新缓存条目
        self._cache[cache_key] = {
            "data": data,
            "created_at": time.time(),
            "expires_at": time.time() + ttl
        }
    
    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry["expires_at"]
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 添加连接池统计
        if self._connector:
            stats.update({
                "pool_size": len(self._connector._conns),
                "pool_limit": self._connector._limit,
                "pool_limit_per_host": self._connector._limit_per_host
            })
        
        # 添加缓存统计
        stats.update({
            "cache_size": len(self._cache),
            "cache_max_size": self.cache_config.max_size,
            "cache_hit_rate": (
                stats["cache_hits"] / (stats["cache_hits"] + stats["cache_misses"])
                if (stats["cache_hits"] + stats["cache_misses"]) > 0 else 0
            )
        })
        
        return stats
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("HTTP缓存已清空")
    
    async def close(self):
        """关闭连接池"""
        if self._session:
            await self._session.close()
            self._session = None
        
        if self._connector:
            await self._connector.close()
            self._connector = None
        
        logger.info("HTTP连接池已关闭")


# 全局实例获取函数
async def get_http_pool() -> HTTPPoolManager:
    """获取全局HTTP连接池实例"""
    return await HTTPPoolManager.get_instance()


# 便捷函数
async def http_request(
    method: str,
    url: str,
    cache_enabled: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """便捷的HTTP请求函数"""
    pool = await get_http_pool()
    
    cache_key = None
    if cache_enabled and method.upper() == "GET":
        cache_key = pool._generate_cache_key(method, url, **kwargs)
    
    return await pool.request(method, url, cache_key=cache_key, **kwargs)
