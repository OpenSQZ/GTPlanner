"""
性能优化器

提供验证系统的性能优化功能：
- 验证器预热机制
- 异步I/O优化
- 内存使用优化
- 并发控制
- 批量验证支持
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Set
from concurrent.futures import ThreadPoolExecutor
from threading import Semaphore, Lock
from ..core.interfaces import IValidator
from ..core.validation_context import ValidationContext
from ..core.validation_result import ValidationResult


class ValidatorPrewarmer:
    """验证器预热器 - 提前初始化和缓存验证器"""
    
    def __init__(self, max_prewarmed: int = 50):
        self.max_prewarmed = max_prewarmed
        self.prewarmed_validators: Dict[str, IValidator] = {}
        self.prewarming_stats: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
    
    async def prewarm_validator(self, validator_type: str, validator_factory: Callable[[Dict[str, Any]], IValidator], config: Dict[str, Any]) -> bool:
        """预热验证器
        
        Args:
            validator_type: 验证器类型
            validator_factory: 验证器工厂函数
            config: 验证器配置
            
        Returns:
            True表示预热成功，False表示失败
        """
        try:
            start_time = time.time()
            
            # 创建验证器实例
            validator = validator_factory(config)
            if not validator:
                return False
            
            # 执行预热验证（使用空数据）
            test_context = ValidationContext.create_for_testing(request_data={})
            await validator.validate(test_context)
            
            # 缓存预热的验证器
            with self._lock:
                if len(self.prewarmed_validators) < self.max_prewarmed:
                    cache_key = f"{validator_type}:{hash(str(config))}"
                    self.prewarmed_validators[cache_key] = validator
                    
                    # 记录预热统计
                    prewarm_time = time.time() - start_time
                    self.prewarming_stats[validator_type] = {
                        "prewarm_time": prewarm_time,
                        "prewarmed_at": time.time(),
                        "config_hash": hash(str(config))
                    }
            
            return True
            
        except Exception as e:
            print(f"Warning: Failed to prewarm validator {validator_type}: {e}")
            return False
    
    def get_prewarmed_validator(self, validator_type: str, config: Dict[str, Any]) -> Optional[IValidator]:
        """获取预热的验证器
        
        Args:
            validator_type: 验证器类型
            config: 验证器配置
            
        Returns:
            预热的验证器实例，如果不存在则返回None
        """
        with self._lock:
            cache_key = f"{validator_type}:{hash(str(config))}"
            return self.prewarmed_validators.get(cache_key)
    
    def get_prewarming_stats(self) -> Dict[str, Any]:
        """获取预热统计信息
        
        Returns:
            预热统计信息字典
        """
        with self._lock:
            return {
                "prewarmed_count": len(self.prewarmed_validators),
                "max_prewarmed": self.max_prewarmed,
                "prewarming_stats": dict(self.prewarming_stats)
            }


class ConcurrencyController:
    """并发控制器 - 控制验证器的并发执行"""
    
    def __init__(self, max_concurrent_validations: int = 100, max_concurrent_per_validator: int = 10):
        self.max_concurrent_validations = max_concurrent_validations
        self.max_concurrent_per_validator = max_concurrent_per_validator
        
        # 全局并发控制
        self.global_semaphore = Semaphore(max_concurrent_validations)
        
        # 验证器级别的并发控制
        self.validator_semaphores: Dict[str, Semaphore] = {}
        self._semaphore_lock = Lock()
        
        # 统计信息
        self.active_validations = 0
        self.total_validations = 0
        self.max_concurrent_reached = 0
        self._stats_lock = Lock()
    
    def _get_validator_semaphore(self, validator_name: str) -> Semaphore:
        """获取验证器的信号量
        
        Args:
            validator_name: 验证器名称
            
        Returns:
            信号量实例
        """
        with self._semaphore_lock:
            if validator_name not in self.validator_semaphores:
                self.validator_semaphores[validator_name] = Semaphore(self.max_concurrent_per_validator)
            return self.validator_semaphores[validator_name]
    
    async def execute_with_concurrency_control(
        self,
        validator: IValidator,
        context: ValidationContext
    ) -> ValidationResult:
        """在并发控制下执行验证器
        
        Args:
            validator: 验证器实例
            context: 验证上下文
            
        Returns:
            验证结果
        """
        validator_name = validator.get_validator_name()
        
        # 获取信号量
        global_sem = self.global_semaphore
        validator_sem = self._get_validator_semaphore(validator_name)
        
        # 更新统计
        with self._stats_lock:
            self.total_validations += 1
            self.active_validations += 1
            self.max_concurrent_reached = max(self.max_concurrent_reached, self.active_validations)
        
        try:
            # 获取全局和验证器级别的许可
            async with asyncio.Semaphore(global_sem._value), asyncio.Semaphore(validator_sem._value):
                result = await validator.validate(context)
                return result
        finally:
            # 释放统计
            with self._stats_lock:
                self.active_validations -= 1
    
    def get_concurrency_stats(self) -> Dict[str, Any]:
        """获取并发统计信息
        
        Returns:
            并发统计信息字典
        """
        with self._stats_lock:
            return {
                "max_concurrent_validations": self.max_concurrent_validations,
                "max_concurrent_per_validator": self.max_concurrent_per_validator,
                "active_validations": self.active_validations,
                "total_validations": self.total_validations,
                "max_concurrent_reached": self.max_concurrent_reached,
                "validator_semaphores": len(self.validator_semaphores)
            }


class BatchValidator:
    """批量验证器 - 支持批量验证请求"""
    
    def __init__(self, max_batch_size: int = 10):
        self.max_batch_size = max_batch_size
        self.batch_stats = {
            "total_batches": 0,
            "total_items": 0,
            "avg_batch_size": 0.0,
            "avg_batch_time": 0.0
        }
        self._stats_lock = Lock()
    
    async def validate_batch(
        self,
        validator: IValidator,
        contexts: List[ValidationContext]
    ) -> List[ValidationResult]:
        """批量验证
        
        Args:
            validator: 验证器实例
            contexts: 验证上下文列表
            
        Returns:
            验证结果列表
        """
        if len(contexts) > self.max_batch_size:
            # 分批处理
            results = []
            for i in range(0, len(contexts), self.max_batch_size):
                batch = contexts[i:i + self.max_batch_size]
                batch_results = await self._validate_single_batch(validator, batch)
                results.extend(batch_results)
            return results
        else:
            return await self._validate_single_batch(validator, contexts)
    
    async def _validate_single_batch(
        self,
        validator: IValidator,
        contexts: List[ValidationContext]
    ) -> List[ValidationResult]:
        """验证单个批次
        
        Args:
            validator: 验证器实例
            contexts: 验证上下文列表
            
        Returns:
            验证结果列表
        """
        start_time = time.time()
        
        # 并行执行验证
        tasks = [validator.validate(context) for context in contexts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = ValidationResult.create_error(
                    ValidationError(
                        code="BATCH_VALIDATION_ERROR",
                        message=f"批量验证项 {i+1} 失败: {str(result)}",
                        validator=validator.get_validator_name()
                    )
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        # 更新统计
        batch_time = time.time() - start_time
        with self._stats_lock:
            self.batch_stats["total_batches"] += 1
            self.batch_stats["total_items"] += len(contexts)
            self.batch_stats["avg_batch_size"] = self.batch_stats["total_items"] / self.batch_stats["total_batches"]
            self.batch_stats["avg_batch_time"] = (
                (self.batch_stats["avg_batch_time"] * (self.batch_stats["total_batches"] - 1) + batch_time) /
                self.batch_stats["total_batches"]
            )
        
        return processed_results
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """获取批量验证统计
        
        Returns:
            批量验证统计信息
        """
        with self._stats_lock:
            return dict(self.batch_stats)


class MemoryOptimizer:
    """内存优化器 - 优化验证系统的内存使用"""
    
    def __init__(self):
        self.object_pools: Dict[str, List[Any]] = {}
        self.pool_stats: Dict[str, Dict[str, int]] = {}
        self._lock = Lock()
    
    def get_pooled_object(self, object_type: str, factory_func: Callable[[], Any]) -> Any:
        """从对象池获取对象
        
        Args:
            object_type: 对象类型
            factory_func: 对象工厂函数
            
        Returns:
            对象实例
        """
        with self._lock:
            pool = self.object_pools.get(object_type, [])
            
            if pool:
                # 从池中获取对象
                obj = pool.pop()
                self._update_pool_stats(object_type, "retrieved")
                return obj
            else:
                # 创建新对象
                obj = factory_func()
                self._update_pool_stats(object_type, "created")
                return obj
    
    def return_pooled_object(self, object_type: str, obj: Any, max_pool_size: int = 10) -> None:
        """将对象返回到对象池
        
        Args:
            object_type: 对象类型
            obj: 对象实例
            max_pool_size: 对象池最大大小
        """
        with self._lock:
            if object_type not in self.object_pools:
                self.object_pools[object_type] = []
            
            pool = self.object_pools[object_type]
            if len(pool) < max_pool_size:
                # 重置对象状态（如果有重置方法）
                if hasattr(obj, 'reset'):
                    obj.reset()
                
                pool.append(obj)
                self._update_pool_stats(object_type, "returned")
            else:
                self._update_pool_stats(object_type, "discarded")
    
    def _update_pool_stats(self, object_type: str, operation: str) -> None:
        """更新对象池统计
        
        Args:
            object_type: 对象类型
            operation: 操作类型
        """
        if object_type not in self.pool_stats:
            self.pool_stats[object_type] = {
                "created": 0,
                "retrieved": 0,
                "returned": 0,
                "discarded": 0
            }
        
        if operation in self.pool_stats[object_type]:
            self.pool_stats[object_type][operation] += 1
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息
        
        Returns:
            内存统计信息字典
        """
        with self._lock:
            total_pooled = sum(len(pool) for pool in self.object_pools.values())
            
            return {
                "total_pools": len(self.object_pools),
                "total_pooled_objects": total_pooled,
                "pool_stats": dict(self.pool_stats),
                "pool_sizes": {
                    object_type: len(pool) 
                    for object_type, pool in self.object_pools.items()
                }
            }
    
    def cleanup_pools(self) -> int:
        """清理对象池
        
        Returns:
            清理的对象数量
        """
        with self._lock:
            cleaned_count = 0
            for pool in self.object_pools.values():
                cleaned_count += len(pool)
                pool.clear()
            return cleaned_count


class PerformanceOptimizer:
    """性能优化器 - 综合的性能优化管理"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 初始化优化组件
        self.prewarmer = ValidatorPrewarmer(
            max_prewarmed=self.config.get("max_prewarmed_validators", 50)
        )
        
        self.concurrency_controller = ConcurrencyController(
            max_concurrent_validations=self.config.get("max_concurrent_validations", 100),
            max_concurrent_per_validator=self.config.get("max_concurrent_per_validator", 10)
        )
        
        self.batch_validator = BatchValidator(
            max_batch_size=self.config.get("max_batch_size", 10)
        )
        
        self.memory_optimizer = MemoryOptimizer()
        
        # 性能监控
        self.performance_stats = {
            "optimization_enabled": True,
            "start_time": time.time(),
            "optimized_validations": 0,
            "performance_improvements": {}
        }
        
        print("PerformanceOptimizer initialized")
    
    async def optimized_validate(
        self,
        validator: IValidator,
        context: ValidationContext,
        use_concurrency_control: bool = True,
        use_prewarming: bool = True
    ) -> ValidationResult:
        """执行优化的验证
        
        Args:
            validator: 验证器实例
            context: 验证上下文
            use_concurrency_control: 是否使用并发控制
            use_prewarming: 是否使用预热
            
        Returns:
            验证结果
        """
        start_time = time.time()
        
        try:
            if use_concurrency_control:
                # 使用并发控制
                result = await self.concurrency_controller.execute_with_concurrency_control(
                    validator, context
                )
            else:
                # 直接执行
                result = await validator.validate(context)
            
            # 记录性能改进
            execution_time = time.time() - start_time
            self._record_performance_improvement(validator.get_validator_name(), execution_time)
            
            return result
            
        except Exception as e:
            # 性能优化失败，回退到标准验证
            print(f"Warning: Optimized validation failed for {validator.get_validator_name()}, falling back: {e}")
            return await validator.validate(context)
    
    async def optimized_batch_validate(
        self,
        validator: IValidator,
        contexts: List[ValidationContext]
    ) -> List[ValidationResult]:
        """执行优化的批量验证
        
        Args:
            validator: 验证器实例
            contexts: 验证上下文列表
            
        Returns:
            验证结果列表
        """
        return await self.batch_validator.validate_batch(validator, contexts)
    
    def _record_performance_improvement(self, validator_name: str, execution_time: float) -> None:
        """记录性能改进
        
        Args:
            validator_name: 验证器名称
            execution_time: 执行时间
        """
        if validator_name not in self.performance_stats["performance_improvements"]:
            self.performance_stats["performance_improvements"][validator_name] = {
                "total_optimized": 0,
                "total_time": 0.0,
                "avg_time": 0.0
            }
        
        stats = self.performance_stats["performance_improvements"][validator_name]
        stats["total_optimized"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["total_optimized"]
        
        self.performance_stats["optimized_validations"] += 1
    
    async def prewarm_common_validators(self, validator_factory: Callable[[str, Dict[str, Any]], Optional[IValidator]]) -> None:
        """预热常用验证器
        
        Args:
            validator_factory: 验证器工厂函数
        """
        common_validators = [
            ("security", {"enable_xss_protection": True}),
            ("size", {"max_request_size": 1048576}),
            ("format", {"validate_required_fields": True}),
        ]
        
        prewarm_tasks = []
        for validator_type, config in common_validators:
            task = self.prewarmer.prewarm_validator(validator_type, validator_factory, config)
            prewarm_tasks.append(task)
        
        results = await asyncio.gather(*prewarm_tasks, return_exceptions=True)
        successful_prewarms = sum(1 for result in results if result is True)
        
        print(f"✅ 预热完成: {successful_prewarms}/{len(common_validators)} 个验证器")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息
        
        Returns:
            优化统计信息字典
        """
        return {
            "performance_stats": dict(self.performance_stats),
            "prewarming_stats": self.prewarmer.get_prewarming_stats(),
            "concurrency_stats": self.concurrency_controller.get_concurrency_stats(),
            "batch_stats": self.batch_validator.get_batch_stats(),
            "memory_stats": self.memory_optimizer.get_memory_stats()
        }
    
    def optimize_for_production(self) -> None:
        """为生产环境优化配置"""
        print("🚀 应用生产环境优化配置...")
        
        # 增加并发限制
        self.concurrency_controller.max_concurrent_validations = 200
        self.concurrency_controller.global_semaphore = Semaphore(200)
        
        # 增加预热验证器数量
        self.prewarmer.max_prewarmed = 100
        
        # 增加批量大小
        self.batch_validator.max_batch_size = 20
        
        print("✅ 生产环境优化配置已应用")
    
    def optimize_for_development(self) -> None:
        """为开发环境优化配置"""
        print("🔧 应用开发环境优化配置...")
        
        # 降低并发限制以便调试
        self.concurrency_controller.max_concurrent_validations = 10
        self.concurrency_controller.global_semaphore = Semaphore(10)
        
        # 减少预热验证器数量
        self.prewarmer.max_prewarmed = 10
        
        # 减少批量大小
        self.batch_validator.max_batch_size = 3
        
        print("✅ 开发环境优化配置已应用")


def create_performance_optimizer(config: Optional[Dict[str, Any]] = None) -> PerformanceOptimizer:
    """创建性能优化器的便捷函数
    
    Args:
        config: 优化器配置
        
    Returns:
        性能优化器实例
    """
    return PerformanceOptimizer(config)


# 全局性能优化器实例
_global_optimizer: Optional[PerformanceOptimizer] = None
_optimizer_lock = Lock()


def get_global_optimizer() -> PerformanceOptimizer:
    """获取全局性能优化器
    
    Returns:
        全局性能优化器实例
    """
    global _global_optimizer
    
    with _optimizer_lock:
        if _global_optimizer is None:
            _global_optimizer = create_performance_optimizer()
        return _global_optimizer


async def optimize_validator_execution(validator: IValidator, context: ValidationContext) -> ValidationResult:
    """优化验证器执行的便捷函数
    
    Args:
        validator: 验证器实例
        context: 验证上下文
        
    Returns:
        验证结果
    """
    optimizer = get_global_optimizer()
    return await optimizer.optimized_validate(validator, context)
