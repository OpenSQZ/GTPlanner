"""
基础验证器模板

基于模板方法模式的验证器基类，提供：
- 通用的验证流程模板
- 缓存支持
- 性能计时
- 错误处理
- 日志记录
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from utils.logger_config import get_logger

from .interfaces import IValidator, ValidatorPriority
from .validation_context import ValidationContext
from .validation_result import ValidationResult, ValidationError, ValidationStatus


class BaseValidator(IValidator, ABC):
    """基础验证器抽象类
    
    实现了验证器的通用逻辑，子类只需要实现具体的验证逻辑。
    提供以下功能：
    - 模板方法模式的验证流程
    - 自动性能计时
    - 缓存支持
    - 错误处理和日志记录
    - 配置管理
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化基础验证器
        
        Args:
            config: 验证器配置字典
        """
        self.config = config
        self.logger = get_logger(f"validator.{self.get_validator_name()}")
        self._cache = {}  # 简单的内存缓存
        
    async def validate(self, context: ValidationContext) -> ValidationResult:
        """执行验证（模板方法）
        
        这是模板方法，定义了验证的标准流程：
        1. 检查缓存
        2. 执行前置检查
        3. 执行具体验证逻辑
        4. 处理结果
        5. 更新缓存
        6. 记录日志和指标
        
        Args:
            context: 验证上下文
            
        Returns:
            验证结果
        """
        start_time = time.time()
        validator_name = self.get_validator_name()
        
        try:
            # 检查是否应该跳过此验证器
            if context.should_skip_validator(validator_name):
                self.logger.debug(f"跳过验证器 {validator_name}")
                return ValidationResult(
                    status=ValidationStatus.SKIPPED,
                    request_id=context.request_id
                )
            
            # 检查缓存
            cache_key = None
            if self.can_cache_result() and context.enable_cache:
                cache_key = self.get_cache_key(context)
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    execution_time = time.time() - start_time
                    self.logger.debug(f"验证器 {validator_name} 使用缓存结果，耗时 {execution_time:.3f}s")
                    cached_result.metrics.cache_hits += 1
                    return cached_result
            
            # 执行前置检查
            pre_check_result = await self._pre_validate(context)
            if pre_check_result and not pre_check_result.is_valid:
                execution_time = time.time() - start_time
                pre_check_result.add_validator_result(validator_name, pre_check_result.status, execution_time)
                return pre_check_result
            
            # 执行具体验证逻辑
            result = await self._do_validate(context)
            
            # 执行后置处理
            result = await self._post_validate(context, result)
            
            # 设置请求ID和验证器信息
            if not result.request_id:
                result.request_id = context.request_id
            
            execution_time = time.time() - start_time
            result.add_validator_result(validator_name, result.status, execution_time)
            
            # 更新缓存
            if cache_key and result.is_valid:
                await self._set_to_cache(cache_key, result, context.cache_ttl)
                result.metrics.cache_misses += 1
            
            # 记录日志
            self._log_validation_result(context, result, execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"验证器 {validator_name} 执行失败: {str(e)}", exc_info=True)
            
            error = ValidationError(
                code="VALIDATOR_EXCEPTION",
                message=f"验证器内部错误: {str(e)}",
                validator=validator_name,
                suggestion="请检查验证器配置或联系系统管理员"
            )
            
            result = ValidationResult.create_error(error, request_id=context.request_id)
            result.add_validator_result(validator_name, ValidationStatus.ERROR, execution_time)
            
            return result
    
    @abstractmethod
    async def _do_validate(self, context: ValidationContext) -> ValidationResult:
        """执行具体的验证逻辑（抽象方法）
        
        子类必须实现这个方法来提供具体的验证逻辑。
        
        Args:
            context: 验证上下文
            
        Returns:
            验证结果
        """
        pass
    
    async def _pre_validate(self, context: ValidationContext) -> Optional[ValidationResult]:
        """验证前置检查
        
        子类可以重写此方法来添加前置检查逻辑。
        如果返回非None的结果，将跳过主要验证逻辑。
        
        Args:
            context: 验证上下文
            
        Returns:
            前置检查结果，None表示通过检查
        """
        return None
    
    async def _post_validate(self, context: ValidationContext, result: ValidationResult) -> ValidationResult:
        """验证后置处理
        
        子类可以重写此方法来添加后置处理逻辑。
        
        Args:
            context: 验证上下文
            result: 验证结果
            
        Returns:
            处理后的验证结果
        """
        return result
    
    def get_priority(self) -> ValidatorPriority:
        """获取验证器优先级
        
        默认返回MEDIUM优先级，子类可以重写。
        
        Returns:
            验证器优先级
        """
        return ValidatorPriority.MEDIUM
    
    def supports_async(self) -> bool:
        """是否支持异步验证
        
        默认返回True，子类可以重写。
        
        Returns:
            是否支持异步
        """
        return True
    
    def can_cache_result(self) -> bool:
        """是否可以缓存验证结果
        
        默认返回True，子类可以重写。
        
        Returns:
            是否可以缓存
        """
        return self.config.get("enable_cache", True)
    
    def get_cache_key(self, context: ValidationContext) -> Optional[str]:
        """获取缓存键
        
        默认实现基于验证器名称和请求数据生成缓存键。
        子类可以重写来提供更精确的缓存策略。
        
        Args:
            context: 验证上下文
            
        Returns:
            缓存键，None表示不缓存
        """
        if not self.can_cache_result():
            return None
        
        # 基于验证器名称、请求路径、方法和数据哈希生成缓存键
        data_hash = hash(str(context.request_data)) if context.request_data else 0
        return f"{self.get_validator_name()}:{context.request_path}:{context.request_method}:{data_hash}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[ValidationResult]:
        """从缓存获取结果
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存的结果，None表示未命中
        """
        # 简单的内存缓存实现
        cache_entry = self._cache.get(cache_key)
        if cache_entry:
            result, expiry_time = cache_entry
            if time.time() < expiry_time:
                return result
            else:
                # 缓存过期，删除
                del self._cache[cache_key]
        return None
    
    async def _set_to_cache(self, cache_key: str, result: ValidationResult, ttl: int) -> None:
        """设置缓存
        
        Args:
            cache_key: 缓存键
            result: 验证结果
            ttl: 生存时间（秒）
        """
        # 简单的内存缓存实现
        expiry_time = time.time() + ttl
        self._cache[cache_key] = (result, expiry_time)
        
        # 简单的缓存清理（保留最近100个条目）
        if len(self._cache) > 100:
            # 删除最旧的条目
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
    
    def _log_validation_result(self, context: ValidationContext, result: ValidationResult, execution_time: float) -> None:
        """记录验证结果日志
        
        Args:
            context: 验证上下文
            result: 验证结果
            execution_time: 执行时间
        """
        validator_name = self.get_validator_name()
        
        if result.is_valid:
            self.logger.debug(
                f"验证器 {validator_name} 通过验证 - "
                f"请求ID: {context.request_id}, "
                f"执行时间: {execution_time:.3f}s, "
                f"状态: {result.status.value}"
            )
        else:
            self.logger.warning(
                f"验证器 {validator_name} 验证失败 - "
                f"请求ID: {context.request_id}, "
                f"执行时间: {execution_time:.3f}s, "
                f"状态: {result.status.value}, "
                f"错误数: {len(result.errors)}, "
                f"错误代码: {[error.code for error in result.errors]}"
            )
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def is_enabled(self) -> bool:
        """检查验证器是否启用
        
        Returns:
            True表示启用，False表示禁用
        """
        return self.config.get("enabled", True)
    
    def get_error_message(self, error_code: str, default_message: str, **kwargs) -> str:
        """获取错误消息
        
        支持模板化的错误消息和多语言。
        
        Args:
            error_code: 错误代码
            default_message: 默认消息
            **kwargs: 消息模板参数
            
        Returns:
            格式化的错误消息
        """
        # 从配置中获取错误消息模板
        messages = self.config.get("error_messages", {})
        template = messages.get(error_code, default_message)
        
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return default_message
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            验证器的字符串描述
        """
        return f"{self.__class__.__name__}(name={self.get_validator_name()}, priority={self.get_priority().name})"
    
    def __repr__(self) -> str:
        """详细字符串表示
        
        Returns:
            验证器的详细字符串描述
        """
        return (
            f"{self.__class__.__name__}("
            f"name={self.get_validator_name()}, "
            f"priority={self.get_priority().name}, "
            f"enabled={self.is_enabled()}, "
            f"cacheable={self.can_cache_result()}, "
            f"async={self.supports_async()})"
        )