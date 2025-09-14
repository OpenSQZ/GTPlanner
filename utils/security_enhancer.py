"""
安全增强模块

为GTPlanner提供全面的安全功能，包括：
- 输入验证和清理
- API密钥验证
- 速率限制
- SQL注入防护
- XSS防护
- 敏感数据保护
"""

import re
import hashlib
import hmac
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
import html
import json

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """安全配置"""
    # 输入验证
    max_input_length: int = 10000
    enable_input_validation: bool = True
    enable_html_escaping: bool = True
    
    # API密钥验证
    enable_api_key_validation: bool = True
    api_key_header: str = "X-API-Key"
    api_keys: List[str] = None
    
    # 速率限制
    enable_rate_limiting: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_window_minutes: int = 1
    
    # SQL注入防护
    enable_sql_injection_protection: bool = True
    
    # 敏感数据保护
    enable_sensitive_data_protection: bool = True
    sensitive_patterns: List[str] = None
    
    def __post_init__(self):
        if self.api_keys is None:
            self.api_keys = []
        if self.sensitive_patterns is None:
            self.sensitive_patterns = [
                r'password\s*[:=]\s*["\']?[^"\'\s]+["\']?',
                r'api[_-]?key\s*[:=]\s*["\']?[^"\'\s]+["\']?',
                r'token\s*[:=]\s*["\']?[^"\'\s]+["\']?',
                r'secret\s*[:=]\s*["\']?[^"\'\s]+["\']?',
                r'credit[_-]?card\s*[:=]\s*["\']?[^"\'\s]+["\']?',
                r'ssn\s*[:=]\s*["\']?[^"\'\s]+["\']?',
            ]


class InputValidator:
    """输入验证器"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        
        # 危险模式
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS脚本
            r'javascript:',  # JavaScript协议
            r'data:text/html',  # 数据URI
            r'vbscript:',  # VBScript协议
            r'on\w+\s*=',  # 事件处理器
            r'<iframe[^>]*>',  # iframe标签
            r'<object[^>]*>',  # object标签
            r'<embed[^>]*>',  # embed标签
            r'<link[^>]*>',  # link标签
            r'<meta[^>]*>',  # meta标签
        ]
        
        # SQL注入模式
        self.sql_injection_patterns = [
            r'union\s+select',  # UNION SELECT
            r'drop\s+table',  # DROP TABLE
            r'delete\s+from',  # DELETE FROM
            r'insert\s+into',  # INSERT INTO
            r'update\s+set',  # UPDATE SET
            r'exec\s*\(',  # EXEC
            r'sp_\w+',  # 存储过程
            r'xp_\w+',  # 扩展存储过程
            r'--',  # SQL注释
            r'/\*.*?\*/',  # SQL块注释
            r';\s*drop',  # 分号后跟DROP
            r';\s*delete',  # 分号后跟DELETE
            r';\s*insert',  # 分号后跟INSERT
            r';\s*update',  # 分号后跟UPDATE
        ]
    
    def validate_input(self, input_data: str, input_type: str = "text") -> Dict[str, Any]:
        """验证输入数据"""
        if not self.config.enable_input_validation:
            return {"valid": True, "cleaned_data": input_data, "warnings": []}
        
        warnings = []
        cleaned_data = input_data
        
        # 长度检查
        if len(input_data) > self.config.max_input_length:
            return {
                "valid": False,
                "error": f"输入长度超过限制 ({self.config.max_input_length} 字符)",
                "cleaned_data": "",
                "warnings": []
            }
        
        # HTML转义
        if self.config.enable_html_escaping:
            cleaned_data = html.escape(cleaned_data)
        
        # XSS检查
        xss_result = self._check_xss(cleaned_data)
        if not xss_result["valid"]:
            warnings.append(f"检测到潜在的XSS攻击: {xss_result['pattern']}")
        
        # SQL注入检查
        if self.config.enable_sql_injection_protection:
            sql_result = self._check_sql_injection(cleaned_data)
            if not sql_result["valid"]:
                warnings.append(f"检测到潜在的SQL注入攻击: {sql_result['pattern']}")
        
        # 敏感数据检查
        sensitive_result = self._check_sensitive_data(cleaned_data)
        if not sensitive_result["valid"]:
            warnings.append(f"检测到敏感数据: {sensitive_result['pattern']}")
        
        return {
            "valid": len(warnings) == 0,
            "cleaned_data": cleaned_data,
            "warnings": warnings
        }
    
    def _check_xss(self, data: str) -> Dict[str, Any]:
        """检查XSS攻击"""
        for pattern in self.dangerous_patterns:
            if re.search(pattern, data, re.IGNORECASE | re.DOTALL):
                return {"valid": False, "pattern": pattern}
        return {"valid": True}
    
    def _check_sql_injection(self, data: str) -> Dict[str, Any]:
        """检查SQL注入攻击"""
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                return {"valid": False, "pattern": pattern}
        return {"valid": True}
    
    def _check_sensitive_data(self, data: str) -> Dict[str, Any]:
        """检查敏感数据"""
        for pattern in self.config.sensitive_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                return {"valid": False, "pattern": pattern}
        return {"valid": True}


class APIKeyValidator:
    """API密钥验证器"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.valid_keys = set(config.api_keys) if config.api_keys else set()
    
    def validate_api_key(self, api_key: str) -> bool:
        """验证API密钥"""
        if not self.config.enable_api_key_validation:
            return True
        
        if not api_key:
            return False
        
        return api_key in self.valid_keys
    
    def add_api_key(self, api_key: str):
        """添加API密钥"""
        self.valid_keys.add(api_key)
    
    def remove_api_key(self, api_key: str):
        """移除API密钥"""
        self.valid_keys.discard(api_key)


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
    
    def is_rate_limited(self, client_id: str) -> Dict[str, Any]:
        """检查是否被速率限制"""
        if not self.config.enable_rate_limiting:
            return {"limited": False, "remaining": float('inf')}
        
        now = datetime.now()
        window_start = now - timedelta(minutes=self.config.rate_limit_window_minutes)
        
        # 清理过期请求
        client_requests = self.requests[client_id]
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()
        
        # 检查请求数量
        request_count = len(client_requests)
        max_requests = self.config.rate_limit_requests_per_minute
        
        if request_count >= max_requests:
            # 记录当前请求
            client_requests.append(now)
            return {
                "limited": True,
                "remaining": 0,
                "reset_time": (client_requests[0] + timedelta(minutes=self.config.rate_limit_window_minutes)).isoformat()
            }
        
        # 记录当前请求
        client_requests.append(now)
        
        return {
            "limited": False,
            "remaining": max_requests - request_count - 1,
            "reset_time": (now + timedelta(minutes=self.config.rate_limit_window_minutes)).isoformat()
        }
    
    def block_ip(self, ip: str, duration_minutes: int = 60):
        """临时封禁IP"""
        self.blocked_ips[ip] = datetime.now() + timedelta(minutes=duration_minutes)
        logger.warning(f"IP {ip} 已被封禁 {duration_minutes} 分钟")
    
    def is_ip_blocked(self, ip: str) -> bool:
        """检查IP是否被封禁"""
        if ip not in self.blocked_ips:
            return False
        
        if datetime.now() > self.blocked_ips[ip]:
            del self.blocked_ips[ip]
            return False
        
        return True


class SecurityEnhancer:
    """安全增强器"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.input_validator = InputValidator(self.config)
        self.api_key_validator = APIKeyValidator(self.config)
        self.rate_limiter = RateLimiter(self.config)
        
        logger.info("安全增强模块初始化完成")
    
    def validate_request(
        self,
        request_data: Dict[str, Any],
        client_id: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """验证请求"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "sanitized_data": request_data.copy()
        }
        
        # API密钥验证
        if api_key:
            if not self.api_key_validator.validate_api_key(api_key):
                validation_result["valid"] = False
                validation_result["errors"].append("无效的API密钥")
        
        # 速率限制检查
        rate_limit_result = self.rate_limiter.is_rate_limited(client_id)
        if rate_limit_result["limited"]:
            validation_result["valid"] = False
            validation_result["errors"].append("请求频率过高，请稍后重试")
        
        # 输入验证
        for key, value in request_data.items():
            if isinstance(value, str):
                input_result = self.input_validator.validate_input(value, key)
                if not input_result["valid"]:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"输入验证失败: {key}")
                
                validation_result["warnings"].extend(input_result["warnings"])
                validation_result["sanitized_data"][key] = input_result["cleaned_data"]
        
        return validation_result
    
    def sanitize_data(self, data: Any) -> Any:
        """清理数据"""
        if isinstance(data, str):
            result = self.input_validator.validate_input(data)
            return result["cleaned_data"]
        elif isinstance(data, dict):
            return {key: self.sanitize_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        else:
            return data
    
    def generate_secure_token(self, data: str, secret: str) -> str:
        """生成安全令牌"""
        timestamp = str(int(time.time()))
        message = f"{data}:{timestamp}"
        token = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{token}:{timestamp}"
    
    def verify_secure_token(self, token: str, data: str, secret: str, max_age: int = 3600) -> bool:
        """验证安全令牌"""
        try:
            token_part, timestamp_part = token.split(":")
            timestamp = int(timestamp_part)
            
            # 检查时间戳
            if time.time() - timestamp > max_age:
                return False
            
            # 验证令牌
            message = f"{data}:{timestamp_part}"
            expected_token = hmac.new(
                secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(token_part, expected_token)
            
        except Exception:
            return False
    
    def mask_sensitive_data(self, data: str) -> str:
        """遮蔽敏感数据"""
        masked_data = data
        
        for pattern in self.config.sensitive_patterns:
            masked_data = re.sub(
                pattern,
                lambda m: m.group(0).split('=')[0] + '=***MASKED***',
                masked_data,
                flags=re.IGNORECASE
            )
        
        return masked_data
    
    def get_security_report(self) -> Dict[str, Any]:
        """获取安全报告"""
        return {
            "config": {
                "max_input_length": self.config.max_input_length,
                "enable_input_validation": self.config.enable_input_validation,
                "enable_api_key_validation": self.config.enable_api_key_validation,
                "enable_rate_limiting": self.config.enable_rate_limiting,
                "rate_limit_requests_per_minute": self.config.rate_limit_requests_per_minute,
            },
            "rate_limiter": {
                "active_clients": len(self.rate_limiter.requests),
                "blocked_ips": len(self.rate_limiter.blocked_ips),
            },
            "api_keys": {
                "total_keys": len(self.api_key_validator.valid_keys),
                "keys_configured": len(self.api_key_validator.valid_keys) > 0,
            }
        }


# 全局安全增强器实例
_global_security_enhancer: Optional[SecurityEnhancer] = None


def get_global_security_enhancer() -> SecurityEnhancer:
    """获取全局安全增强器实例"""
    global _global_security_enhancer
    if _global_security_enhancer is None:
        _global_security_enhancer = SecurityEnhancer()
    return _global_security_enhancer


# 装饰器
def secure_request(security_enhancer: Optional[SecurityEnhancer] = None):
    """安全请求装饰器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            enhancer = security_enhancer or get_global_security_enhancer()
            
            # 这里可以添加更多的安全检查逻辑
            # 例如从请求中提取client_id和api_key
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_input(input_type: str = "text", security_enhancer: Optional[SecurityEnhancer] = None):
    """输入验证装饰器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            enhancer = security_enhancer or get_global_security_enhancer()
            
            # 验证输入参数
            for key, value in kwargs.items():
                if isinstance(value, str):
                    result = enhancer.input_validator.validate_input(value, input_type)
                    if not result["valid"]:
                        raise ValueError(f"输入验证失败: {key}")
                    kwargs[key] = result["cleaned_data"]
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
