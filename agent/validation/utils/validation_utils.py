"""
验证工具类

提供验证系统的辅助工具函数：
- 性能计时功能
- 缓存管理
- 数据处理工具
- 验证辅助函数
"""

import time
import hashlib
import json
from typing import Any, Dict, Optional, List, Union
from threading import Lock


class ValidationTimer:
    """验证性能计时器 - 上下文管理器支持"""
    
    def __init__(self):
        self.start_time = 0.0
        self.end_time = 0.0
        self.elapsed_time = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
    
    def start(self) -> None:
        """开始计时"""
        self.start_time = time.time()
    
    def stop(self) -> float:
        """停止计时并返回经过的时间
        
        Returns:
            经过的时间（秒）
        """
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        return self.elapsed_time
    
    def reset(self) -> None:
        """重置计时器"""
        self.start_time = 0.0
        self.end_time = 0.0
        self.elapsed_time = 0.0


class ValidationCache:
    """验证缓存管理器 - 内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, tuple[Any, float]] = {}  # (value, expiry_time)
        self._access_order: List[str] = []
        self._lock = Lock()
        self._hit_count = 0
        self._miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        with self._lock:
            if key not in self._cache:
                self._miss_count += 1
                return None
            
            value, expiry_time = self._cache[key]
            current_time = time.time()
            
            if current_time > expiry_time:
                # 缓存过期，删除
                del self._cache[key]
                self._access_order.remove(key)
                self._miss_count += 1
                return None
            
            # 更新访问顺序
            self._access_order.remove(key)
            self._access_order.append(key)
            
            self._hit_count += 1
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），如果为None则使用默认TTL
        """
        with self._lock:
            # 检查缓存大小限制
            if len(self._cache) >= self.max_size and key not in self._cache:
                # 移除最久未访问的条目
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]
            
            # 计算过期时间
            expiry_time = time.time() + (ttl or self.default_ttl)
            
            # 设置缓存
            self._cache[key] = (value, expiry_time)
            
            # 更新访问顺序
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
    
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
                self._access_order.remove(key)
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._hit_count = 0
            self._miss_count = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息字典
        """
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = self._hit_count / total_requests if total_requests > 0 else 0
            
            return {
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }
    
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
                self._access_order.remove(key)
            
            return len(expired_keys)


def generate_cache_key(*args, **kwargs) -> str:
    """生成缓存键
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        生成的缓存键字符串
    """
    # 将所有参数序列化为字符串
    key_parts = []
    
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            key_parts.append(str(hash(str(arg))))
    
    for key, value in sorted(kwargs.items()):
        if isinstance(value, (str, int, float, bool)):
            key_parts.append(f"{key}:{value}")
        else:
            key_parts.append(f"{key}:{hash(str(value))}")
    
    # 生成哈希
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode('utf-8')).hexdigest()


def extract_string_content(data: Any, max_depth: int = 5) -> List[str]:
    """递归提取数据中的字符串内容
    
    Args:
        data: 待提取的数据
        max_depth: 最大递归深度
        
    Returns:
        提取的字符串列表
    """
    if max_depth <= 0:
        return []
    
    strings = []
    
    if isinstance(data, str):
        strings.append(data)
    elif isinstance(data, dict):
        for value in data.values():
            strings.extend(extract_string_content(value, max_depth - 1))
    elif isinstance(data, list):
        for item in data:
            strings.extend(extract_string_content(item, max_depth - 1))
    
    return strings


def calculate_data_size(data: Any) -> int:
    """计算数据的字节大小
    
    Args:
        data: 待计算的数据
        
    Returns:
        数据大小（字节）
    """
    try:
        if isinstance(data, str):
            return len(data.encode('utf-8'))
        elif isinstance(data, (dict, list)):
            json_str = json.dumps(data, ensure_ascii=False)
            return len(json_str.encode('utf-8'))
        elif isinstance(data, bytes):
            return len(data)
        else:
            return len(str(data).encode('utf-8'))
    except Exception:
        # 如果无法计算，返回近似值
        import sys
        return sys.getsizeof(data)


def normalize_endpoint_path(path: str) -> str:
    """标准化端点路径
    
    Args:
        path: 原始路径
        
    Returns:
        标准化的路径
    """
    # 确保以/开头
    if not path.startswith('/'):
        path = '/' + path
    
    # 移除尾部的/
    if path.endswith('/') and path != '/':
        path = path[:-1]
    
    # 转换为小写
    path = path.lower()
    
    return path


def is_json_serializable(data: Any) -> bool:
    """检查数据是否可以JSON序列化
    
    Args:
        data: 待检查的数据
        
    Returns:
        True表示可以序列化，False表示不可以
    """
    try:
        json.dumps(data)
        return True
    except (TypeError, ValueError):
        return False


def sanitize_for_logging(data: Any, max_length: int = 200) -> str:
    """为日志记录清理数据
    
    Args:
        data: 原始数据
        max_length: 最大长度
        
    Returns:
        清理后的字符串
    """
    # 转换为字符串
    if isinstance(data, str):
        content = data
    elif isinstance(data, (dict, list)):
        try:
            content = json.dumps(data, ensure_ascii=False)
        except Exception:
            content = str(data)
    else:
        content = str(data)
    
    # 截断长度
    if len(content) > max_length:
        content = content[:max_length] + "..."
    
    # 简单的敏感信息替换
    import re
    content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', content)
    content = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD]', content)
    
    return content


def create_request_fingerprint(
    method: str, 
    path: str, 
    data: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None
) -> str:
    """创建请求指纹
    
    Args:
        method: HTTP方法
        path: 请求路径
        data: 请求数据
        headers: 请求头
        
    Returns:
        请求指纹字符串
    """
    fingerprint_parts = [method.upper(), normalize_endpoint_path(path)]
    
    if data:
        data_size = calculate_data_size(data)
        data_hash = hash(str(data)) if data else 0
        fingerprint_parts.append(f"data:{data_size}:{data_hash}")
    
    if headers:
        # 只包含重要的头部信息
        important_headers = ["content-type", "user-agent", "accept-language"]
        header_parts = []
        for header in important_headers:
            if header in headers:
                header_parts.append(f"{header}:{headers[header]}")
        if header_parts:
            fingerprint_parts.append("headers:" + "|".join(header_parts))
    
    fingerprint_string = "|".join(fingerprint_parts)
    return hashlib.md5(fingerprint_string.encode('utf-8')).hexdigest()[:16]
