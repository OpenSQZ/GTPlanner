"""
验证策略实现

包含所有具体的验证策略实现，基于策略模式设计。

可用的验证策略：
- SecurityValidator: 安全验证（XSS、SQL注入检测）
- SizeValidator: 大小验证（请求大小、内容长度）
- FormatValidator: 格式验证（JSON、字段验证）
- ContentValidator: 内容验证（内容质量、垃圾检测）
- LanguageValidator: 多语言验证
- RateLimitValidator: 频率限制验证
- SessionValidator: 会话验证
"""

from typing import Dict, Any

# 导入所有验证策略（注意：需要处理可能的导入错误）
try:
    from .security_validator import SecurityValidator, SecurityValidationStrategy
    SECURITY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SecurityValidator not available: {e}")
    SECURITY_AVAILABLE = False

try:
    from .size_validator import SizeValidator, SizeValidationStrategy
    SIZE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SizeValidator not available: {e}")
    SIZE_AVAILABLE = False

try:
    from .format_validator import FormatValidator, FormatValidationStrategy
    FORMAT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: FormatValidator not available: {e}")
    FORMAT_AVAILABLE = False

try:
    from .content_validator import ContentValidator, ContentValidationStrategy
    CONTENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ContentValidator not available: {e}")
    CONTENT_AVAILABLE = False

try:
    from .language_validator import LanguageValidator, LanguageValidationStrategy
    LANGUAGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: LanguageValidator not available: {e}")
    LANGUAGE_AVAILABLE = False

try:
    from .rate_limit_validator import RateLimitValidator, RateLimitValidationStrategy
    RATE_LIMIT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: RateLimitValidator not available: {e}")
    RATE_LIMIT_AVAILABLE = False

try:
    from .session_validator import SessionValidator, SessionValidationStrategy
    SESSION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SessionValidator not available: {e}")
    SESSION_AVAILABLE = False


# 构建可用的验证器列表
AVAILABLE_VALIDATORS = {}
AVAILABLE_STRATEGIES = {}

if SECURITY_AVAILABLE:
    AVAILABLE_VALIDATORS["security"] = SecurityValidator
    AVAILABLE_STRATEGIES["security"] = SecurityValidationStrategy

if SIZE_AVAILABLE:
    AVAILABLE_VALIDATORS["size"] = SizeValidator
    AVAILABLE_STRATEGIES["size"] = SizeValidationStrategy

if FORMAT_AVAILABLE:
    AVAILABLE_VALIDATORS["format"] = FormatValidator
    AVAILABLE_STRATEGIES["format"] = FormatValidationStrategy

if CONTENT_AVAILABLE:
    AVAILABLE_VALIDATORS["content"] = ContentValidator
    AVAILABLE_STRATEGIES["content"] = ContentValidationStrategy

if LANGUAGE_AVAILABLE:
    AVAILABLE_VALIDATORS["language"] = LanguageValidator
    AVAILABLE_STRATEGIES["language"] = LanguageValidationStrategy

if RATE_LIMIT_AVAILABLE:
    AVAILABLE_VALIDATORS["rate_limit"] = RateLimitValidator
    AVAILABLE_STRATEGIES["rate_limit"] = RateLimitValidationStrategy

if SESSION_AVAILABLE:
    AVAILABLE_VALIDATORS["session"] = SessionValidator
    AVAILABLE_STRATEGIES["session"] = SessionValidationStrategy


def get_available_validators() -> Dict[str, type]:
    """获取所有可用的验证器类
    
    Returns:
        验证器名称到类的映射字典
    """
    return AVAILABLE_VALIDATORS.copy()


def get_available_strategies() -> Dict[str, type]:
    """获取所有可用的验证策略类
    
    Returns:
        策略名称到类的映射字典
    """
    return AVAILABLE_STRATEGIES.copy()


def create_validator(validator_type: str, config: Dict[str, Any]):
    """创建验证器实例
    
    Args:
        validator_type: 验证器类型
        config: 验证器配置
        
    Returns:
        验证器实例，如果类型不支持则返回None
    """
    validator_class = AVAILABLE_VALIDATORS.get(validator_type)
    if validator_class:
        try:
            return validator_class(config)
        except Exception as e:
            print(f"Error creating validator {validator_type}: {e}")
            return None
    return None


def create_strategy(strategy_type: str, config: Dict[str, Any]):
    """创建验证策略实例
    
    Args:
        strategy_type: 策略类型
        config: 策略配置
        
    Returns:
        策略实例，如果类型不支持则返回None
    """
    strategy_class = AVAILABLE_STRATEGIES.get(strategy_type)
    if strategy_class:
        try:
            return strategy_class(config)
        except Exception as e:
            print(f"Error creating strategy {strategy_type}: {e}")
            return None
    return None


__all__ = [
    "AVAILABLE_VALIDATORS",
    "AVAILABLE_STRATEGIES", 
    "get_available_validators",
    "get_available_strategies",
    "create_validator",
    "create_strategy"
]

# 动态添加可用的类到__all__
if SECURITY_AVAILABLE:
    __all__.extend(["SecurityValidator", "SecurityValidationStrategy"])
if SIZE_AVAILABLE:
    __all__.extend(["SizeValidator", "SizeValidationStrategy"])
if FORMAT_AVAILABLE:
    __all__.extend(["FormatValidator", "FormatValidationStrategy"])
if CONTENT_AVAILABLE:
    __all__.extend(["ContentValidator", "ContentValidationStrategy"])
if LANGUAGE_AVAILABLE:
    __all__.extend(["LanguageValidator", "LanguageValidationStrategy"])
if RATE_LIMIT_AVAILABLE:
    __all__.extend(["RateLimitValidator", "RateLimitValidationStrategy"])
if SESSION_AVAILABLE:
    __all__.extend(["SessionValidator", "SessionValidationStrategy"])