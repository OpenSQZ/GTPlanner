"""
验证系统核心接口定义

基于SOLID原则设计的接口体系，支持：
- 接口隔离原则：细粒度的专用接口
- 依赖倒置原则：高层模块依赖抽象接口
- 开闭原则：支持扩展新的验证器和观察者
- 里氏替换原则：所有实现都可以替换基接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator
from enum import Enum


class ValidatorPriority(Enum):
    """验证器优先级枚举
    
    定义验证器的执行优先级，数值越小优先级越高
    """
    CRITICAL = 1    # 关键验证（安全、认证）
    HIGH = 2        # 高优先级（格式、大小）
    MEDIUM = 3      # 中优先级（内容、语言）
    LOW = 4         # 低优先级（性能优化）


class IValidator(ABC):
    """验证器基础接口
    
    定义了所有验证器必须实现的基本方法。
    支持异步验证、优先级排序和流式响应。
    """
    
    @abstractmethod
    async def validate(self, context: 'ValidationContext') -> 'ValidationResult':
        """执行验证
        
        Args:
            context: 验证上下文，包含请求信息和配置
            
        Returns:
            验证结果，包含成功/失败状态和详细信息
        """
        pass
    
    @abstractmethod
    def get_validator_name(self) -> str:
        """获取验证器名称
        
        Returns:
            验证器的唯一标识名称
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> ValidatorPriority:
        """获取验证器优先级
        
        Returns:
            验证器的执行优先级
        """
        pass
    
    @abstractmethod
    def supports_async(self) -> bool:
        """是否支持异步验证
        
        Returns:
            True表示支持异步验证，False表示仅支持同步
        """
        pass
    
    def can_cache_result(self) -> bool:
        """是否可以缓存验证结果
        
        Returns:
            True表示可以缓存结果，False表示每次都需要重新验证
        """
        return True
    
    def get_cache_key(self, context: 'ValidationContext') -> Optional[str]:
        """获取缓存键
        
        Args:
            context: 验证上下文
            
        Returns:
            缓存键字符串，如果返回None则不缓存
        """
        if not self.can_cache_result():
            return None
        
        # 默认缓存键生成策略
        return f"{self.get_validator_name()}:{hash(str(context.request_data))}"


class IValidationStrategy(ABC):
    """验证策略接口
    
    基于策略模式的验证策略接口，支持不同的验证算法。
    """
    
    @abstractmethod
    async def execute(self, data: Any, rules: Dict[str, Any]) -> 'ValidationResult':
        """执行验证策略
        
        Args:
            data: 待验证的数据
            rules: 验证规则配置
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """获取策略名称
        
        Returns:
            策略的唯一标识名称
        """
        pass
    
    def get_supported_data_types(self) -> List[type]:
        """获取支持的数据类型
        
        Returns:
            支持验证的数据类型列表
        """
        return [str, dict, list]


class IValidationChain(ABC):
    """验证链接口
    
    基于责任链模式的验证链接口，支持串行和并行验证执行。
    """
    
    @abstractmethod
    def add_validator(self, validator: IValidator) -> 'IValidationChain':
        """添加验证器到链中
        
        Args:
            validator: 要添加的验证器
            
        Returns:
            返回自身，支持链式调用
        """
        pass
    
    @abstractmethod
    def remove_validator(self, validator_name: str) -> 'IValidationChain':
        """从链中移除验证器
        
        Args:
            validator_name: 要移除的验证器名称
            
        Returns:
            返回自身，支持链式调用
        """
        pass
    
    @abstractmethod
    async def validate(self, context: 'ValidationContext') -> 'ValidationResult':
        """串行执行验证链
        
        Args:
            context: 验证上下文
            
        Returns:
            合并后的验证结果
        """
        pass
    
    @abstractmethod
    async def validate_parallel(self, context: 'ValidationContext') -> 'ValidationResult':
        """并行执行验证链
        
        Args:
            context: 验证上下文
            
        Returns:
            合并后的验证结果
        """
        pass
    
    def get_chain_name(self) -> str:
        """获取验证链名称
        
        Returns:
            验证链的标识名称
        """
        return "default_chain"
    
    def get_validator_count(self) -> int:
        """获取验证器数量
        
        Returns:
            链中验证器的数量
        """
        return 0


class IValidationObserver(ABC):
    """验证观察者接口
    
    基于观察者模式的事件通知接口，支持验证过程的事件监听。
    """
    
    @abstractmethod
    async def on_validation_start(self, context: 'ValidationContext') -> None:
        """验证开始事件
        
        Args:
            context: 验证上下文
        """
        pass
    
    @abstractmethod
    async def on_validation_step(self, validator_name: str, result: 'ValidationResult') -> None:
        """验证步骤完成事件
        
        Args:
            validator_name: 完成验证的验证器名称
            result: 验证结果
        """
        pass
    
    @abstractmethod
    async def on_validation_complete(self, result: 'ValidationResult') -> None:
        """验证完成事件
        
        Args:
            result: 最终验证结果
        """
        pass
    
    @abstractmethod
    async def on_validation_error(self, error: Exception, context: Optional['ValidationContext'] = None) -> None:
        """验证错误事件
        
        Args:
            error: 发生的异常
            context: 验证上下文（可能为None）
        """
        pass
    
    def get_observer_name(self) -> str:
        """获取观察者名称
        
        Returns:
            观察者的标识名称
        """
        return self.__class__.__name__


class IValidationMiddleware(ABC):
    """验证中间件接口
    
    基于装饰器模式的中间件接口，支持FastAPI中间件集成。
    """
    
    @abstractmethod
    async def process_request(self, request: Any, call_next: Any) -> Any:
        """处理请求
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            响应对象
        """
        pass
    
    @abstractmethod
    def get_middleware_name(self) -> str:
        """获取中间件名称
        
        Returns:
            中间件的标识名称
        """
        pass
    
    def get_execution_order(self) -> int:
        """获取执行顺序
        
        Returns:
            中间件的执行顺序，数值越小越早执行
        """
        return 0


class IValidationCache(ABC):
    """验证缓存接口
    
    支持验证结果的缓存存储和检索。
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional['ValidationResult']:
        """获取缓存的验证结果
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的验证结果，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, result: 'ValidationResult', ttl: int = 300) -> None:
        """设置缓存的验证结果
        
        Args:
            key: 缓存键
            result: 验证结果
            ttl: 生存时间（秒）
        """
        pass
    
    @abstractmethod
    async def invalidate(self, pattern: str) -> None:
        """失效匹配模式的缓存
        
        Args:
            pattern: 匹配模式，支持通配符
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空所有缓存"""
        pass
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息字典
        """
        return {
            "cache_type": self.__class__.__name__,
            "total_keys": 0,
            "hit_rate": 0.0,
            "miss_rate": 0.0
        }


class IValidationMetrics(ABC):
    """验证指标收集接口
    
    支持验证过程的性能指标收集和统计。
    """
    
    @abstractmethod
    def record_validation_time(self, validator_name: str, duration: float) -> None:
        """记录验证执行时间
        
        Args:
            validator_name: 验证器名称
            duration: 执行时间（秒）
        """
        pass
    
    @abstractmethod
    def record_validation_result(self, validator_name: str, success: bool) -> None:
        """记录验证结果
        
        Args:
            validator_name: 验证器名称
            success: 验证是否成功
        """
        pass
    
    @abstractmethod
    def record_cache_hit(self, validator_name: str, hit: bool) -> None:
        """记录缓存命中情况
        
        Args:
            validator_name: 验证器名称
            hit: 是否命中缓存
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标数据
        
        Returns:
            指标数据字典
        """
        pass
    
    def reset_metrics(self) -> None:
        """重置所有指标数据"""
        pass
    
    def export_metrics(self, format: str = "json") -> str:
        """导出指标数据
        
        Args:
            format: 导出格式（json, csv等）
            
        Returns:
            格式化的指标数据字符串
        """
        import json
        return json.dumps(self.get_metrics(), indent=2, ensure_ascii=False)


class IValidationRegistry(ABC):
    """验证器注册表接口
    
    支持验证器的注册、查找和管理。
    """
    
    @abstractmethod
    def register_validator(self, validator_type: str, validator_class: type) -> None:
        """注册验证器类型
        
        Args:
            validator_type: 验证器类型标识
            validator_class: 验证器类
        """
        pass
    
    @abstractmethod
    def get_validator(self, validator_type: str, config: Dict[str, Any]) -> Optional[IValidator]:
        """获取验证器实例
        
        Args:
            validator_type: 验证器类型标识
            config: 验证器配置
            
        Returns:
            验证器实例，如果类型不存在则返回None
        """
        pass
    
    @abstractmethod
    def list_validators(self) -> List[str]:
        """列出所有已注册的验证器类型
        
        Returns:
            验证器类型列表
        """
        pass
    
    def unregister_validator(self, validator_type: str) -> bool:
        """注销验证器类型
        
        Args:
            validator_type: 验证器类型标识
            
        Returns:
            True表示注销成功，False表示类型不存在
        """
        return False


# 为了避免循环导入，在这里定义类型提示
# 实际的类将在其他模块中定义
if False:  # TYPE_CHECKING
    from .validation_context import ValidationContext
    from .validation_result import ValidationResult

