"""
验证上下文模块

包含完整的验证环境信息，支持：
- FastAPI Request对象解析
- 多语言验证支持
- 流式验证会话集成
- 缓存键生成
- 验证路径追踪
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Union
import datetime
from enum import Enum

try:
    from fastapi import Request
except ImportError:
    Request = None


class ValidationMode(Enum):
    """验证模式枚举
    
    定义不同的验证执行模式
    """
    STRICT = "strict"        # 严格模式：所有验证器必须通过
    LENIENT = "lenient"      # 宽松模式：允许警告
    FAIL_FAST = "fail_fast"  # 快速失败：遇到错误立即停止
    CONTINUE = "continue"    # 继续模式：收集所有错误后返回


@dataclass
class ValidationContext:
    """验证上下文 - 包含完整的验证环境信息
    
    这个类包含了验证过程中需要的所有信息，包括：
    - 请求相关信息（FastAPI Request、数据、头部等）
    - 验证配置（模式、规则、跳过的验证器等）
    - 会话和用户信息（用户ID、会话ID、客户端信息等）
    - 多语言支持（语言检测、支持的语言列表等）
    - 验证状态追踪（当前验证器、执行路径、时间等）
    - 缓存和性能配置
    - 流式响应支持
    """
    
    # 请求相关信息
    request: Optional[Request] = None
    request_data: Any = None
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_method: str = "POST"
    request_path: str = ""
    request_size: int = 0
    
    # 验证配置
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    validation_mode: ValidationMode = ValidationMode.STRICT
    skip_validators: List[str] = field(default_factory=list)
    enabled_validators: List[str] = field(default_factory=list)
    
    # 会话和用户信息
    request_id: str = field(default_factory=lambda: f"req_{datetime.datetime.now().timestamp()}")
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    # 多语言支持
    language: Optional[str] = None
    detected_language: Optional[str] = None
    supported_languages: List[str] = field(default_factory=lambda: ["en", "zh", "es", "fr", "ja"])
    
    # 验证状态追踪
    current_validator: Optional[str] = None
    validation_path: List[str] = field(default_factory=list)
    validation_start_time: Optional[datetime.datetime] = None
    validation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 缓存和性能
    cache_key: Optional[str] = None
    enable_cache: bool = True
    cache_ttl: int = 300  # 5分钟
    
    # 流式响应支持
    streaming_session: Optional[Any] = None  # StreamingSession类型
    enable_streaming_validation: bool = False
    
    def __post_init__(self):
        """初始化后处理
        
        自动执行以下操作：
        - 设置验证开始时间
        - 从FastAPI Request对象中提取信息
        - 生成缓存键
        """
        if self.validation_start_time is None:
            self.validation_start_time = datetime.datetime.now()
        
        # 从request中提取信息
        if self.request:
            self._extract_request_info()
        
        # 生成缓存键
        if self.enable_cache and not self.cache_key:
            self._generate_cache_key()
    
    def _extract_request_info(self) -> None:
        """从FastAPI Request对象中提取信息
        
        提取以下信息：
        - 请求头部
        - 请求方法和路径
        - 客户端IP和User-Agent
        - Content-Length
        """
        if not self.request or Request is None:
            return
            
        self.request_headers = dict(self.request.headers)
        self.request_method = self.request.method
        self.request_path = str(self.request.url.path)
        self.client_ip = self.request.client.host if self.request.client else None
        self.user_agent = self.request_headers.get("user-agent")
        
        # 提取Content-Length
        content_length = self.request_headers.get("content-length")
        if content_length:
            try:
                self.request_size = int(content_length)
            except ValueError:
                self.request_size = 0
    
    def _generate_cache_key(self) -> None:
        """生成验证缓存键
        
        基于以下信息生成唯一的缓存键：
        - 请求方法和路径
        - 请求大小
        - 用户ID（匿名用户使用"anonymous"）
        - 验证规则的哈希值
        """
        key_parts = [
            self.request_method,
            self.request_path,
            str(self.request_size),
            self.user_id or "anonymous",
            str(hash(str(self.validation_rules)))
        ]
        self.cache_key = "|".join(key_parts)
    
    def should_skip_validator(self, validator_name: str) -> bool:
        """检查是否应跳过指定验证器
        
        Args:
            validator_name: 验证器名称
            
        Returns:
            True表示应该跳过，False表示应该执行
        """
        # 如果在跳过列表中，则跳过
        if validator_name in self.skip_validators:
            return True
        
        # 如果指定了enabled_validators，只运行列表中的验证器
        if self.enabled_validators and validator_name not in self.enabled_validators:
            return True
            
        return False
    
    def add_to_path(self, validator_name: str) -> None:
        """添加验证器到验证路径
        
        Args:
            validator_name: 验证器名称
        """
        self.validation_path.append(validator_name)
        self.current_validator = validator_name
    
    def get_execution_time(self) -> float:
        """获取验证执行时间（秒）
        
        Returns:
            从验证开始到现在的时间差（秒）
        """
        if self.validation_start_time:
            return (datetime.datetime.now() - self.validation_start_time).total_seconds()
        return 0.0
    
    def is_api_endpoint(self) -> bool:
        """判断是否为API端点
        
        Returns:
            True表示是API端点，False表示不是
        """
        return self.request_path.startswith("/api/")
    
    def is_streaming_request(self) -> bool:
        """判断是否为流式请求
        
        Returns:
            True表示是流式请求，False表示不是
        """
        return (
            self.enable_streaming_validation and 
            self.streaming_session is not None
        )
    
    def get_language_preference(self) -> str:
        """获取语言偏好
        
        按优先级返回语言设置：
        1. 显式指定的语言
        2. 检测到的语言
        3. 默认语言
        
        Returns:
            语言代码字符串
        """
        return (
            self.language or 
            self.detected_language or 
            (self.supported_languages[0] if self.supported_languages else "en")
        )
    
    def get_request_content_type(self) -> Optional[str]:
        """获取请求的Content-Type
        
        Returns:
            Content-Type字符串，如果不存在则返回None
        """
        return self.request_headers.get("content-type")
    
    def is_json_request(self) -> bool:
        """判断是否为JSON请求
        
        Returns:
            True表示是JSON请求，False表示不是
        """
        content_type = self.get_request_content_type()
        return content_type is not None and "application/json" in content_type.lower()
    
    def get_user_identifier(self) -> str:
        """获取用户标识符
        
        按优先级返回用户标识：
        1. 用户ID
        2. 会话ID
        3. 客户端IP
        4. "anonymous"
        
        Returns:
            用户标识符字符串
        """
        return (
            self.user_id or
            self.session_id or
            self.client_ip or
            "anonymous"
        )
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加验证元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.validation_metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取验证元数据
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            元数据值，如果不存在则返回默认值
        """
        return self.validation_metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于日志和调试）
        
        Returns:
            包含主要信息的字典
        """
        return {
            "request_id": self.request_id,
            "request_method": self.request_method,
            "request_path": self.request_path,
            "request_size": self.request_size,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "language": self.get_language_preference(),
            "validation_mode": self.validation_mode.value,
            "validation_path": self.validation_path,
            "execution_time": self.get_execution_time(),
            "cache_enabled": self.enable_cache,
            "streaming_enabled": self.enable_streaming_validation,
            "user_identifier": self.get_user_identifier(),
            "is_api_endpoint": self.is_api_endpoint(),
            "is_json_request": self.is_json_request(),
            "metadata_keys": list(self.validation_metadata.keys())
        }
    
    def to_summary(self) -> str:
        """生成上下文摘要字符串
        
        Returns:
            包含关键信息的摘要字符串
        """
        return (
            f"ValidationContext(request_id={self.request_id}, "
            f"method={self.request_method}, path={self.request_path}, "
            f"user={self.get_user_identifier()}, "
            f"mode={self.validation_mode.value}, "
            f"execution_time={self.get_execution_time():.3f}s)"
        )
    
    @classmethod
    def create_from_request(
        cls,
        request: Optional[Request] = None,
        request_data: Any = None,
        **kwargs
    ) -> 'ValidationContext':
        """从FastAPI Request创建验证上下文
        
        Args:
            request: FastAPI Request对象
            request_data: 请求数据
            **kwargs: 其他配置参数
            
        Returns:
            新创建的验证上下文实例
        """
        return cls(
            request=request,
            request_data=request_data,
            **kwargs
        )
    
    @classmethod
    def create_for_testing(
        cls,
        request_data: Any = None,
        validation_mode: ValidationMode = ValidationMode.STRICT,
        **kwargs
    ) -> 'ValidationContext':
        """创建用于测试的验证上下文
        
        Args:
            request_data: 测试数据
            validation_mode: 验证模式
            **kwargs: 其他配置参数
            
        Returns:
            用于测试的验证上下文实例
        """
        return cls(
            request_data=request_data,
            validation_mode=validation_mode,
            request_method="POST",
            request_path="/api/test",
            enable_cache=False,  # 测试时通常不需要缓存
            **kwargs
        )

