"""
Sentry错误追踪集成（可选）

提供Sentry集成用于生产环境错误追踪和性能监控。
需要安装: pip install sentry-sdk
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Sentry可用性检查
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("Sentry SDK not available. Install with: pip install sentry-sdk")


def init_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
    enable_logging_integration: bool = True,
    logging_level: int = logging.ERROR,
    logging_event_level: int = logging.ERROR,
    **kwargs
) -> bool:
    """
    初始化Sentry错误追踪
    
    Args:
        dsn: Sentry DSN（从环境变量SENTRY_DSN获取）
        environment: 环境名称（development/staging/production）
        release: 版本号
        traces_sample_rate: 性能追踪采样率 (0.0-1.0)
        profiles_sample_rate: 性能分析采样率 (0.0-1.0)
        enable_logging_integration: 是否启用日志集成
        logging_level: 日志级别
        logging_event_level: 创建Sentry事件的日志级别
        **kwargs: 其他Sentry配置选项
    
    Returns:
        是否成功初始化
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry SDK not installed, skipping initialization")
        return False
    
    # 从环境变量获取DSN
    dsn = dsn or os.getenv("SENTRY_DSN")
    if not dsn:
        logger.info("Sentry DSN not provided, skipping initialization")
        return False
    
    # 环境配置
    environment = environment or os.getenv("ENV", "development")
    release = release or os.getenv("APP_VERSION", "unknown")
    
    # 根据环境调整采样率
    if environment == "production":
        traces_sample_rate = traces_sample_rate or 0.1
        profiles_sample_rate = profiles_sample_rate or 0.1
    elif environment == "staging":
        traces_sample_rate = traces_sample_rate or 0.5
        profiles_sample_rate = profiles_sample_rate or 0.5
    else:  # development
        traces_sample_rate = traces_sample_rate or 1.0
        profiles_sample_rate = profiles_sample_rate or 1.0
    
    # 配置集成
    integrations = [
        FastApiIntegration(),
        AsyncioIntegration(),
    ]
    
    # 添加日志集成
    if enable_logging_integration:
        integrations.append(
            LoggingIntegration(
                level=logging_level,
                event_level=logging_event_level
            )
        )
    
    try:
        # 初始化Sentry
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=integrations,
            # 自动捕获异常
            attach_stacktrace=True,
            # 发送默认PII（个人身份信息）
            send_default_pii=False,
            # 其他配置
            **kwargs
        )
        
        logger.info(
            f"Sentry initialized successfully",
            extra={
                "environment": environment,
                "release": release,
                "traces_sample_rate": traces_sample_rate,
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}", exc_info=True)
        return False


def capture_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error",
    tags: Optional[Dict[str, str]] = None,
    user_info: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    捕获并发送异常到Sentry
    
    Args:
        exception: 异常对象
        context: 额外上下文信息
        level: 错误级别 (fatal, error, warning, info, debug)
        tags: 标签字典
        user_info: 用户信息字典
    
    Returns:
        事件ID（如果成功发送）
    """
    if not SENTRY_AVAILABLE:
        return None
    
    try:
        # 设置作用域
        with sentry_sdk.push_scope() as scope:
            # 设置级别
            scope.level = level
            
            # 添加上下文
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            # 添加标签
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)
            
            # 添加用户信息
            if user_info:
                scope.user = user_info
            
            # 捕获异常
            event_id = sentry_sdk.capture_exception(exception)
            
            return event_id
    
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")
        return None


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    捕获并发送消息到Sentry
    
    Args:
        message: 消息内容
        level: 消息级别
        context: 额外上下文
        tags: 标签字典
    
    Returns:
        事件ID（如果成功发送）
    """
    if not SENTRY_AVAILABLE:
        return None
    
    try:
        with sentry_sdk.push_scope() as scope:
            scope.level = level
            
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)
            
            event_id = sentry_sdk.capture_message(message, level=level)
            
            return event_id
    
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")
        return None


def set_user(
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    email: Optional[str] = None,
    **kwargs
) -> None:
    """
    设置当前用户信息
    
    Args:
        user_id: 用户ID
        username: 用户名
        email: 邮箱
        **kwargs: 其他用户信息
    """
    if not SENTRY_AVAILABLE:
        return
    
    user_info = {}
    if user_id:
        user_info["id"] = user_id
    if username:
        user_info["username"] = username
    if email:
        user_info["email"] = email
    
    user_info.update(kwargs)
    
    sentry_sdk.set_user(user_info)


def set_context(name: str, context: Dict[str, Any]) -> None:
    """
    设置上下文信息
    
    Args:
        name: 上下文名称
        context: 上下文数据
    """
    if not SENTRY_AVAILABLE:
        return
    
    sentry_sdk.set_context(name, context)


def set_tag(key: str, value: str) -> None:
    """
    设置标签
    
    Args:
        key: 标签键
        value: 标签值
    """
    if not SENTRY_AVAILABLE:
        return
    
    sentry_sdk.set_tag(key, value)


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    添加面包屑（用于追踪事件发生前的操作）
    
    Args:
        message: 消息内容
        category: 类别
        level: 级别
        data: 额外数据
    """
    if not SENTRY_AVAILABLE:
        return
    
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


class SentryContext:
    """Sentry上下文管理器"""
    
    def __init__(
        self,
        transaction_name: Optional[str] = None,
        operation: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化上下文管理器
        
        Args:
            transaction_name: 事务名称
            operation: 操作名称
            tags: 标签
            context: 上下文数据
        """
        self.transaction_name = transaction_name
        self.operation = operation
        self.tags = tags or {}
        self.context = context or {}
        self.transaction = None
    
    def __enter__(self):
        """进入上下文"""
        if not SENTRY_AVAILABLE:
            return self
        
        # 开始事务
        if self.transaction_name:
            self.transaction = sentry_sdk.start_transaction(
                name=self.transaction_name,
                op=self.operation or "function"
            )
            self.transaction.__enter__()
        
        # 设置标签和上下文
        for key, value in self.tags.items():
            set_tag(key, value)
        
        for key, value in self.context.items():
            set_context(key, value)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if not SENTRY_AVAILABLE:
            return False
        
        # 如果有异常，捕获它
        if exc_type is not None:
            capture_exception(exc_val)
        
        # 结束事务
        if self.transaction:
            self.transaction.__exit__(exc_type, exc_val, exc_tb)
        
        return False  # 不抑制异常

