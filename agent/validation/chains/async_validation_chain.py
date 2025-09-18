"""
异步验证链实现

基于责任链模式的异步验证链，支持：
- 串行验证执行
- 并行验证执行  
- 验证器优先级排序
- 快速失败模式支持
- 验证路径追踪
- 异常处理和恢复
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Set
from ..core.interfaces import IValidator, IValidationChain
from ..core.validation_context import ValidationContext, ValidationMode
from ..core.validation_result import ValidationResult, ValidationStatus, ValidationError, ValidationSeverity


class ValidationTimer:
    """验证计时器 - 上下文管理器"""
    
    def __init__(self):
        self.start_time = 0.0
        self.elapsed_time = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_time = time.time() - self.start_time


class AsyncValidationChain(IValidationChain):
    """异步验证链 - 支持并行和串行执行
    
    这是责任链模式的核心实现，支持：
    - 验证器的动态添加和移除
    - 按优先级自动排序
    - 串行和并行两种执行模式
    - 不同的验证模式（严格、宽松、快速失败等）
    - 完整的错误处理和恢复
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.validators: List[IValidator] = []
        self.parallel_groups: Dict[str, List[IValidator]] = {}
        self._sorted = False
    
    def add_validator(self, validator: IValidator) -> 'AsyncValidationChain':
        """添加验证器到链中
        
        Args:
            validator: 要添加的验证器
            
        Returns:
            返回自身，支持链式调用
        """
        if validator not in self.validators:
            self.validators.append(validator)
            self._sorted = False  # 标记需要重新排序
        return self
    
    def remove_validator(self, validator_name: str) -> 'AsyncValidationChain':
        """从链中移除验证器
        
        Args:
            validator_name: 要移除的验证器名称
            
        Returns:
            返回自身，支持链式调用
        """
        self.validators = [v for v in self.validators if v.get_validator_name() != validator_name]
        self._sorted = False
        return self
    
    def add_parallel_group(self, group_name: str, validators: List[IValidator]) -> 'AsyncValidationChain':
        """添加并行执行组
        
        Args:
            group_name: 组名
            validators: 验证器列表
            
        Returns:
            返回自身，支持链式调用
        """
        self.parallel_groups[group_name] = validators
        return self
    
    def _ensure_sorted(self) -> None:
        """确保验证器按优先级排序"""
        if not self._sorted:
            self.validators.sort(key=lambda v: v.get_priority().value)
            self._sorted = True
    
    async def validate(self, context: ValidationContext) -> ValidationResult:
        """串行执行验证链
        
        按优先级顺序依次执行所有验证器，支持快速失败模式。
        
        Args:
            context: 验证上下文
            
        Returns:
            合并后的验证结果
        """
        result = ValidationResult(ValidationStatus.SUCCESS)
        result.request_id = context.request_id
        
        # 确保验证器按优先级排序
        self._ensure_sorted()
        
        with ValidationTimer() as timer:
            for validator in self.validators:
                validator_name = validator.get_validator_name()
                
                # 检查是否跳过此验证器
                if context.should_skip_validator(validator_name):
                    result.add_validator_result(validator_name, ValidationStatus.SKIPPED)
                    continue
                
                # 更新验证路径
                context.add_to_path(validator_name)
                
                try:
                    # 执行验证器
                    validator_start_time = time.time()
                    validator_result = await validator.validate(context)
                    validator_execution_time = time.time() - validator_start_time
                    
                    # 合并结果
                    result = result.merge(validator_result)
                    
                    # 记录验证器执行结果
                    if validator_name not in result.validator_results:
                        result.add_validator_result(
                            validator_name, 
                            validator_result.status, 
                            validator_execution_time
                        )
                    
                    # 快速失败模式检查
                    if (context.validation_mode == ValidationMode.FAIL_FAST and 
                        not validator_result.is_valid):
                        break
                        
                except Exception as e:
                    # 验证器执行异常处理
                    validator_execution_time = time.time() - validator_start_time
                    
                    error = ValidationError(
                        code="VALIDATOR_EXECUTION_ERROR",
                        message=f"验证器 {validator_name} 执行失败: {str(e)}",
                        validator=validator_name,
                        severity=ValidationSeverity.HIGH,
                        suggestion="请检查验证器配置或联系系统管理员",
                        metadata={"exception_type": type(e).__name__, "exception_message": str(e)}
                    )
                    result.add_error(error)
                    result.add_validator_result(validator_name, ValidationStatus.ERROR, validator_execution_time)
                    
                    # 根据验证模式决定是否继续
                    if context.validation_mode == ValidationMode.FAIL_FAST:
                        break
        
        # 更新总体指标
        result.metrics.execution_time = timer.elapsed_time
        result.complete()
        
        return result
    
    async def validate_parallel(self, context: ValidationContext) -> ValidationResult:
        """并行执行验证链
        
        并行执行所有验证器，可以显著提升性能。
        
        Args:
            context: 验证上下文
            
        Returns:
            合并后的验证结果
        """
        result = ValidationResult(ValidationStatus.SUCCESS)
        result.request_id = context.request_id
        
        # 确保验证器按优先级排序
        self._ensure_sorted()
        
        with ValidationTimer() as timer:
            # 过滤出需要执行的验证器
            active_validators = []
            for validator in self.validators:
                validator_name = validator.get_validator_name()
                if context.should_skip_validator(validator_name):
                    result.add_validator_result(validator_name, ValidationStatus.SKIPPED)
                    continue
                active_validators.append(validator)
            
            if not active_validators:
                # 没有需要执行的验证器
                result.metrics.execution_time = timer.elapsed_time
                result.complete()
                return result
            
            # 创建验证任务
            tasks = []
            for validator in active_validators:
                task = self._create_validation_task(validator, context)
                tasks.append(task)
            
            # 并行执行所有验证任务
            if tasks:
                validator_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理验证结果
                for i, validator_result in enumerate(validator_results):
                    validator = active_validators[i]
                    validator_name = validator.get_validator_name()
                    
                    # 更新验证路径
                    context.add_to_path(validator_name)
                    
                    if isinstance(validator_result, Exception):
                        # 验证器执行异常
                        error = ValidationError(
                            code="VALIDATOR_EXECUTION_ERROR",
                            message=f"验证器 {validator_name} 执行失败: {str(validator_result)}",
                            validator=validator_name,
                            severity=ValidationSeverity.HIGH,
                            suggestion="请检查验证器配置或联系系统管理员",
                            metadata={
                                "exception_type": type(validator_result).__name__,
                                "exception_message": str(validator_result)
                            }
                        )
                        result.add_error(error)
                        result.add_validator_result(validator_name, ValidationStatus.ERROR)
                    else:
                        # 正常的验证结果
                        result = result.merge(validator_result)
                        if validator_name not in result.validator_results:
                            result.add_validator_result(validator_name, validator_result.status)
        
        # 更新总体指标
        result.metrics.execution_time = timer.elapsed_time
        result.complete()
        
        return result
    
    async def _create_validation_task(self, validator: IValidator, context: ValidationContext):
        """创建验证任务
        
        Args:
            validator: 验证器
            context: 验证上下文
            
        Returns:
            验证结果或异常
        """
        try:
            return await validator.validate(context)
        except Exception as e:
            # 返回异常，由调用者处理
            raise e
    
    def get_chain_name(self) -> str:
        """获取验证链名称
        
        Returns:
            验证链的标识名称
        """
        return self.name
    
    def get_validator_count(self) -> int:
        """获取验证器数量
        
        Returns:
            链中验证器的数量
        """
        return len(self.validators)
    
    def get_validator_names(self) -> List[str]:
        """获取所有验证器名称
        
        Returns:
            验证器名称列表
        """
        return [v.get_validator_name() for v in self.validators]
    
    def has_validator(self, validator_name: str) -> bool:
        """检查是否包含指定验证器
        
        Args:
            validator_name: 验证器名称
            
        Returns:
            True表示包含，False表示不包含
        """
        return validator_name in self.get_validator_names()
    
    def clear(self) -> 'AsyncValidationChain':
        """清空所有验证器
        
        Returns:
            返回自身，支持链式调用
        """
        self.validators.clear()
        self.parallel_groups.clear()
        self._sorted = False
        return self
    
    def clone(self, new_name: Optional[str] = None) -> 'AsyncValidationChain':
        """克隆验证链
        
        Args:
            new_name: 新链的名称，如果为None则使用原名称加_copy后缀
            
        Returns:
            新的验证链实例
        """
        clone_name = new_name or f"{self.name}_copy"
        cloned_chain = AsyncValidationChain(clone_name)
        
        # 复制验证器
        for validator in self.validators:
            cloned_chain.add_validator(validator)
        
        # 复制并行组
        for group_name, group_validators in self.parallel_groups.items():
            cloned_chain.add_parallel_group(group_name, group_validators.copy())
        
        return cloned_chain
    
    def get_summary(self) -> Dict[str, Any]:
        """获取验证链摘要信息
        
        Returns:
            包含链信息的字典
        """
        return {
            "name": self.name,
            "validator_count": self.get_validator_count(),
            "validator_names": self.get_validator_names(),
            "parallel_groups": list(self.parallel_groups.keys()),
            "is_sorted": self._sorted
        }
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            验证链的字符串描述
        """
        return f"AsyncValidationChain(name={self.name}, validators={self.get_validator_count()})"
    
    def __repr__(self) -> str:
        """详细字符串表示
        
        Returns:
            验证链的详细字符串描述
        """
        return (
            f"AsyncValidationChain(name={self.name}, "
            f"validators={self.get_validator_names()}, "
            f"parallel_groups={list(self.parallel_groups.keys())})"
        )
