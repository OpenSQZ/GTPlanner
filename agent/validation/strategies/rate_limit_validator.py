"""
频率限制验证策略

基于策略模式的频率限制实现，提供：
- 基于IP的频率限制
- 基于用户的频率限制
- 基于会话的频率限制
- 滑动窗口算法
- 内存/Redis缓存支持
- 突发请求处理
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from collections import deque, defaultdict
from threading import Lock
from ..core.interfaces import IValidationStrategy, ValidatorPriority
from ..core.validation_context import ValidationContext
from ..core.validation_result import (
    ValidationResult, ValidationError, ValidationStatus, ValidationSeverity
)
# from ..core.base_validator import BaseValidator  # 暂时注释避免dynaconf依赖


class SlidingWindowRateLimiter:
    """滑动窗口频率限制器"""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000, burst_size: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        
        # 使用deque存储请求时间戳
        self.minute_windows: Dict[str, deque] = defaultdict(lambda: deque())
        self.hour_windows: Dict[str, deque] = defaultdict(lambda: deque())
        self.burst_windows: Dict[str, deque] = defaultdict(lambda: deque())
        
        # 线程锁
        self._lock = Lock()
    
    def is_allowed(self, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """检查是否允许请求
        
        Args:
            identifier: 标识符（IP、用户ID等）
            
        Returns:
            (是否允许, 限制信息)
        """
        current_time = time.time()
        
        with self._lock:
            # 清理过期的时间戳
            self._cleanup_expired_timestamps(identifier, current_time)
            
            # 检查突发限制（最近10秒）
            burst_window = self.burst_windows[identifier]
            burst_count = len(burst_window)
            
            if burst_count >= self.burst_size:
                return False, {
                    "limit_type": "burst",
                    "limit": self.burst_size,
                    "current": burst_count,
                    "reset_time": burst_window[0] + 10,  # 10秒窗口
                    "retry_after": max(0, burst_window[0] + 10 - current_time)
                }
            
            # 检查分钟限制
            minute_window = self.minute_windows[identifier]
            minute_count = len(minute_window)
            
            if minute_count >= self.requests_per_minute:
                return False, {
                    "limit_type": "minute",
                    "limit": self.requests_per_minute,
                    "current": minute_count,
                    "reset_time": minute_window[0] + 60,  # 60秒窗口
                    "retry_after": max(0, minute_window[0] + 60 - current_time)
                }
            
            # 检查小时限制
            hour_window = self.hour_windows[identifier]
            hour_count = len(hour_window)
            
            if hour_count >= self.requests_per_hour:
                return False, {
                    "limit_type": "hour",
                    "limit": self.requests_per_hour,
                    "current": hour_count,
                    "reset_time": hour_window[0] + 3600,  # 3600秒窗口
                    "retry_after": max(0, hour_window[0] + 3600 - current_time)
                }
            
            # 记录当前请求
            burst_window.append(current_time)
            minute_window.append(current_time)
            hour_window.append(current_time)
            
            return True, {
                "limit_type": "allowed",
                "burst_remaining": self.burst_size - burst_count - 1,
                "minute_remaining": self.requests_per_minute - minute_count - 1,
                "hour_remaining": self.requests_per_hour - hour_count - 1
            }
    
    def _cleanup_expired_timestamps(self, identifier: str, current_time: float) -> None:
        """清理过期的时间戳"""
        # 清理突发窗口（10秒）
        burst_window = self.burst_windows[identifier]
        while burst_window and current_time - burst_window[0] > 10:
            burst_window.popleft()
        
        # 清理分钟窗口（60秒）
        minute_window = self.minute_windows[identifier]
        while minute_window and current_time - minute_window[0] > 60:
            minute_window.popleft()
        
        # 清理小时窗口（3600秒）
        hour_window = self.hour_windows[identifier]
        while hour_window and current_time - hour_window[0] > 3600:
            hour_window.popleft()
    
    def get_stats(self, identifier: str) -> Dict[str, Any]:
        """获取频率限制统计信息"""
        current_time = time.time()
        
        with self._lock:
            self._cleanup_expired_timestamps(identifier, current_time)
            
            return {
                "burst_count": len(self.burst_windows[identifier]),
                "minute_count": len(self.minute_windows[identifier]),
                "hour_count": len(self.hour_windows[identifier]),
                "burst_limit": self.burst_size,
                "minute_limit": self.requests_per_minute,
                "hour_limit": self.requests_per_hour
            }


class RateLimitValidationStrategy(IValidationStrategy):
    """频率限制验证策略 - 基于滑动窗口的频率控制"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.requests_per_minute = config.get("requests_per_minute", 60)
        self.requests_per_hour = config.get("requests_per_hour", 1000)
        self.burst_size = config.get("burst_size", 10)
        self.enable_ip_based_limiting = config.get("enable_ip_based_limiting", True)
        self.enable_user_based_limiting = config.get("enable_user_based_limiting", True)
        self.enable_session_based_limiting = config.get("enable_session_based_limiting", False)
        
        # 创建频率限制器
        self.ip_limiter = SlidingWindowRateLimiter(
            self.requests_per_minute,
            self.requests_per_hour,
            self.burst_size
        )
        
        self.user_limiter = SlidingWindowRateLimiter(
            self.requests_per_minute * 2,  # 用户限制比IP限制更宽松
            self.requests_per_hour * 2,
            self.burst_size * 2
        )
        
        self.session_limiter = SlidingWindowRateLimiter(
            self.requests_per_minute // 2,  # 会话限制比用户限制更严格
            self.requests_per_hour // 2,
            self.burst_size
        )
    
    async def execute(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        """执行频率限制验证"""
        result = ValidationResult(ValidationStatus.SUCCESS)
        
        # 从规则中获取标识符信息
        client_ip = rules.get("client_ip")
        user_id = rules.get("user_id")
        session_id = rules.get("session_id")
        
        # IP频率限制
        if self.enable_ip_based_limiting and client_ip:
            await self._check_ip_rate_limit(client_ip, result)
        
        # 用户频率限制
        if self.enable_user_based_limiting and user_id:
            await self._check_user_rate_limit(user_id, result)
        
        # 会话频率限制
        if self.enable_session_based_limiting and session_id:
            await self._check_session_rate_limit(session_id, result)
        
        return result
    
    async def _check_ip_rate_limit(self, client_ip: str, result: ValidationResult) -> None:
        """检查IP频率限制"""
        allowed, limit_info = self.ip_limiter.is_allowed(f"ip:{client_ip}")
        
        if not allowed:
            error = self._create_rate_limit_error(
                limit_type="IP",
                identifier=client_ip,
                limit_info=limit_info
            )
            result.add_error(error)
        else:
            # 添加限制信息到元数据
            result.metadata["ip_rate_limit"] = limit_info
    
    async def _check_user_rate_limit(self, user_id: str, result: ValidationResult) -> None:
        """检查用户频率限制"""
        allowed, limit_info = self.user_limiter.is_allowed(f"user:{user_id}")
        
        if not allowed:
            error = self._create_rate_limit_error(
                limit_type="用户",
                identifier=user_id,
                limit_info=limit_info
            )
            result.add_error(error)
        else:
            result.metadata["user_rate_limit"] = limit_info
    
    async def _check_session_rate_limit(self, session_id: str, result: ValidationResult) -> None:
        """检查会话频率限制"""
        allowed, limit_info = self.session_limiter.is_allowed(f"session:{session_id}")
        
        if not allowed:
            error = self._create_rate_limit_error(
                limit_type="会话",
                identifier=session_id,
                limit_info=limit_info
            )
            result.add_error(error)
        else:
            result.metadata["session_rate_limit"] = limit_info
    
    def _create_rate_limit_error(self, limit_type: str, identifier: str, limit_info: Dict[str, Any]) -> ValidationError:
        """创建频率限制错误"""
        limit_name_map = {
            "burst": "突发",
            "minute": "分钟",
            "hour": "小时"
        }
        
        limit_type_name = limit_name_map.get(limit_info["limit_type"], limit_info["limit_type"])
        retry_after = int(limit_info.get("retry_after", 60))
        
        return ValidationError(
            code=f"RATE_LIMIT_{limit_info['limit_type'].upper()}",
            message=(
                f"{limit_type}频率限制：{limit_type_name}限制 {limit_info['limit']} 次/期间，"
                f"当前 {limit_info['current']} 次，请在 {retry_after} 秒后重试"
            ),
            validator="rate_limit",
            severity=ValidationSeverity.HIGH,
            suggestion=f"请降低请求频率，等待 {retry_after} 秒后重试",
            metadata={
                "limit_type": limit_info["limit_type"],
                "limit": limit_info["limit"],
                "current": limit_info["current"],
                "retry_after": retry_after,
                "identifier_type": limit_type,
                "identifier": identifier
            }
        )
    
    def get_strategy_name(self) -> str:
        return "rate_limit"


# class RateLimitValidator(BaseValidator):  # 暂时注释避免dynaconf依赖
    """频率限制验证器 - 基于BaseValidator的完整实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.strategy = RateLimitValidationStrategy(config)
    
    async def _do_validate(self, context: ValidationContext) -> ValidationResult:
        """执行频率限制验证逻辑"""
        # 准备验证规则，包含标识符信息
        validation_rules = {
            "client_ip": context.client_ip,
            "user_id": context.user_id,
            "session_id": context.session_id,
            **context.validation_rules
        }
        
        return await self.strategy.execute(context.request_data, validation_rules)
    
    def get_validator_name(self) -> str:
        return "rate_limit"
    
    def get_priority(self) -> ValidatorPriority:
        return ValidatorPriority.HIGH  # 频率限制优先级很高
    
    def can_cache_result(self) -> bool:
        # 频率限制结果不应该缓存，因为状态会实时变化
        return False
    
    def supports_async(self) -> bool:
        return True
