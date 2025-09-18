"""
验证结果模块

包含验证结果的完整数据结构，支持：
- 多级验证状态和严重程度
- 详细的错误信息和建议
- 性能指标收集
- 结果合并和聚合
- 多种输出格式
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
import datetime
from enum import Enum
import json


class ValidationStatus(Enum):
    """验证状态枚举
    
    定义验证的执行状态
    """
    SUCCESS = "success"      # 验证成功
    WARNING = "warning"      # 有警告但可继续
    ERROR = "error"          # 验证失败
    CRITICAL = "critical"    # 严重错误
    SKIPPED = "skipped"      # 跳过验证


class ValidationSeverity(Enum):
    """验证严重程度枚举
    
    定义错误和警告的严重程度
    """
    LOW = 1        # 低严重程度
    MEDIUM = 2     # 中等严重程度  
    HIGH = 3       # 高严重程度
    CRITICAL = 4   # 严重程度


class ValidationError:
    """验证错误详细信息
    
    包含错误的完整描述信息，支持多语言和建议
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        validator: Optional[str] = None,
        severity: ValidationSeverity = ValidationSeverity.MEDIUM,
        suggestion: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.field = field
        self.value = value
        self.validator = validator
        self.severity = severity
        self.suggestion = suggestion
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            错误信息的字典表示
        """
        result = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.name
        }
        
        # 只包含非空字段
        if self.field is not None:
            result["field"] = self.field
        if self.value is not None:
            result["value"] = str(self.value) if not isinstance(self.value, (str, int, float, bool)) else self.value
        if self.validator is not None:
            result["validator"] = self.validator
        if self.suggestion is not None:
            result["suggestion"] = self.suggestion
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    def is_critical(self) -> bool:
        """判断是否为严重错误
        
        Returns:
            True表示严重错误，False表示非严重错误
        """
        return self.severity == ValidationSeverity.CRITICAL
    
    def get_severity_level(self) -> int:
        """获取严重程度数值
        
        Returns:
            严重程度对应的数值
        """
        return self.severity.value
    
    @classmethod
    def create_xss_error(cls, value: str, validator: str = "security") -> 'ValidationError':
        """创建XSS检测错误
        
        Args:
            value: 检测到XSS的值
            validator: 验证器名称
            
        Returns:
            XSS错误实例
        """
        return cls(
            code="XSS_DETECTED",
            message="检测到潜在的跨站脚本攻击（XSS）代码",
            value=value,
            validator=validator,
            severity=ValidationSeverity.CRITICAL,
            suggestion="请移除HTML标签和JavaScript代码"
        )
    
    @classmethod
    def create_sql_injection_error(cls, value: str, validator: str = "security") -> 'ValidationError':
        """创建SQL注入检测错误
        
        Args:
            value: 检测到SQL注入的值
            validator: 验证器名称
            
        Returns:
            SQL注入错误实例
        """
        return cls(
            code="SQL_INJECTION_DETECTED", 
            message="检测到潜在的SQL注入攻击",
            value=value,
            validator=validator,
            severity=ValidationSeverity.CRITICAL,
            suggestion="请避免使用SQL关键字和特殊字符"
        )
    
    @classmethod
    def create_size_error(cls, current_size: int, max_size: int, field: str = None, validator: str = "size") -> 'ValidationError':
        """创建大小超限错误
        
        Args:
            current_size: 当前大小
            max_size: 最大允许大小
            field: 相关字段
            validator: 验证器名称
            
        Returns:
            大小错误实例
        """
        return cls(
            code="SIZE_LIMIT_EXCEEDED",
            message=f"大小超出限制：当前 {current_size} 字节，最大允许 {max_size} 字节",
            field=field,
            value=current_size,
            validator=validator,
            severity=ValidationSeverity.HIGH,
            suggestion=f"请将内容大小控制在 {max_size} 字节以内"
        )
    
    @classmethod
    def create_format_error(cls, field: str, expected_type: str, actual_value: Any, validator: str = "format") -> 'ValidationError':
        """创建格式错误
        
        Args:
            field: 字段名
            expected_type: 期望的类型
            actual_value: 实际值
            validator: 验证器名称
            
        Returns:
            格式错误实例
        """
        return cls(
            code="INVALID_FORMAT",
            message=f"字段 '{field}' 格式不正确，期望 {expected_type}",
            field=field,
            value=actual_value,
            validator=validator,
            severity=ValidationSeverity.HIGH,
            suggestion=f"请确保 '{field}' 字段符合 {expected_type} 格式"
        )


class ValidationMetrics:
    """验证指标数据结构
    
    收集验证过程的性能和统计指标
    """
    
    def __init__(self):
        self.total_validators = 0           # 总验证器数量
        self.executed_validators = 0        # 已执行验证器数量
        self.skipped_validators = 0         # 跳过的验证器数量
        self.failed_validators = 0          # 失败的验证器数量
        self.execution_time = 0.0           # 总执行时间（秒）
        self.cache_hits = 0                 # 缓存命中次数
        self.cache_misses = 0               # 缓存未命中次数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            指标数据的字典表示
        """
        return {
            "total_validators": self.total_validators,
            "executed_validators": self.executed_validators,
            "skipped_validators": self.skipped_validators,
            "failed_validators": self.failed_validators,
            "execution_time": round(self.execution_time, 3),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "success_rate": self.get_success_rate(),
            "cache_hit_rate": self.get_cache_hit_rate(),
            "average_execution_time": self.get_average_execution_time()
        }
    
    def get_success_rate(self) -> float:
        """计算验证成功率
        
        Returns:
            成功率（0.0-1.0）
        """
        if self.executed_validators == 0:
            return 0.0
        return (self.executed_validators - self.failed_validators) / self.executed_validators
    
    def get_cache_hit_rate(self) -> float:
        """计算缓存命中率
        
        Returns:
            缓存命中率（0.0-1.0）
        """
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return self.cache_hits / total_cache_requests
    
    def get_average_execution_time(self) -> float:
        """计算平均执行时间
        
        Returns:
            平均执行时间（秒）
        """
        if self.executed_validators == 0:
            return 0.0
        return self.execution_time / self.executed_validators
    
    def add_validator_execution(self, execution_time: float, success: bool, from_cache: bool = False) -> None:
        """添加验证器执行记录
        
        Args:
            execution_time: 执行时间
            success: 是否成功
            from_cache: 是否来自缓存
        """
        self.executed_validators += 1
        self.execution_time += execution_time
        
        if not success:
            self.failed_validators += 1
            
        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1


class ValidationResult:
    """验证结果 - 包含完整的验证信息
    
    这是验证系统的核心数据结构，包含：
    - 验证状态和错误信息
    - 性能指标和统计数据
    - 验证器执行记录
    - 时间戳和元数据
    """
    
    def __init__(
        self,
        status: ValidationStatus,
        errors: Optional[List[ValidationError]] = None,
        warnings: Optional[List[ValidationError]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        metrics: Optional[ValidationMetrics] = None,
        request_id: Optional[str] = None
    ):
        self.status = status
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
        self.metrics = metrics or ValidationMetrics()
        self.request_id = request_id
        self.validator_results: Dict[str, ValidationStatus] = {}
        self.execution_order: List[str] = []
        self.end_time: Optional[datetime.datetime] = None
    
    @property
    def is_valid(self) -> bool:
        """是否验证通过（成功或仅有警告）
        
        Returns:
            True表示验证通过，False表示验证失败
        """
        return self.status in [ValidationStatus.SUCCESS, ValidationStatus.WARNING]
    
    @property
    def has_errors(self) -> bool:
        """是否有错误
        
        Returns:
            True表示有错误，False表示无错误
        """
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """是否有警告
        
        Returns:
            True表示有警告，False表示无警告
        """
        return len(self.warnings) > 0
    
    @property
    def has_critical_errors(self) -> bool:
        """是否有严重错误
        
        Returns:
            True表示有严重错误，False表示无严重错误
        """
        return any(error.is_critical() for error in self.errors)
    
    @property
    def execution_time(self) -> float:
        """获取总执行时间（秒）
        
        Returns:
            执行时间，如果未结束则返回当前经过的时间
        """
        # 简化版本，直接返回指标中的时间
        return self.metrics.execution_time
    
    def add_error(self, error: ValidationError) -> None:
        """添加错误
        
        Args:
            error: 验证错误
        """
        self.errors.append(error)
        self._update_status_from_error(error)
    
    def add_warning(self, warning: ValidationError) -> None:
        """添加警告
        
        Args:
            warning: 验证警告
        """
        self.warnings.append(warning)
        if self.status == ValidationStatus.SUCCESS:
            self.status = ValidationStatus.WARNING
    
    def add_validator_result(self, validator_name: str, status: ValidationStatus, execution_time: float = 0.0) -> None:
        """记录验证器执行结果
        
        Args:
            validator_name: 验证器名称
            status: 验证状态
            execution_time: 执行时间
        """
        self.validator_results[validator_name] = status
        self.execution_order.append(validator_name)
        
        # 更新指标
        success = status in [ValidationStatus.SUCCESS, ValidationStatus.WARNING, ValidationStatus.SKIPPED]
        self.metrics.add_validator_execution(execution_time, success)
        
        if status == ValidationStatus.SKIPPED:
            self.metrics.skipped_validators += 1
    
    def _update_status_from_error(self, error: ValidationError) -> None:
        """根据错误更新验证状态
        
        Args:
            error: 验证错误
        """
        if error.is_critical():
            self.status = ValidationStatus.CRITICAL
        elif self.status in [ValidationStatus.SUCCESS, ValidationStatus.WARNING]:
            self.status = ValidationStatus.ERROR
    
    def complete(self) -> None:
        """标记验证完成
        
        设置结束时间并更新指标
        """
        # self.end_time = datetime.datetime.now()
        self.metrics.execution_time = self.execution_time
    
    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """合并验证结果
        
        Args:
            other: 另一个验证结果
            
        Returns:
            合并后的验证结果
        """
        # 确定合并后的状态（取最严重的状态）
        status_priority = {
            ValidationStatus.CRITICAL: 4,
            ValidationStatus.ERROR: 3,
            ValidationStatus.WARNING: 2,
            ValidationStatus.SUCCESS: 1,
            ValidationStatus.SKIPPED: 0
        }
        
        merged_status = max(
            self.status, other.status,
            key=lambda x: status_priority[x]
        )
        
        # 合并指标
        merged_metrics = ValidationMetrics()
        merged_metrics.total_validators = self.metrics.total_validators + other.metrics.total_validators
        merged_metrics.executed_validators = self.metrics.executed_validators + other.metrics.executed_validators
        merged_metrics.skipped_validators = self.metrics.skipped_validators + other.metrics.skipped_validators
        merged_metrics.failed_validators = self.metrics.failed_validators + other.metrics.failed_validators
        merged_metrics.execution_time = self.metrics.execution_time + other.metrics.execution_time
        merged_metrics.cache_hits = self.metrics.cache_hits + other.metrics.cache_hits
        merged_metrics.cache_misses = self.metrics.cache_misses + other.metrics.cache_misses
        
        # 创建合并后的结果
        merged = ValidationResult(
            status=merged_status,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            metadata={**self.metadata, **other.metadata},
            metrics=merged_metrics,
            request_id=self.request_id or other.request_id
        )
        
        # 手动设置其他属性
        merged.validator_results = {**self.validator_results, **other.validator_results}
        merged.execution_order = self.execution_order + other.execution_order
        
        return merged
    
    def get_errors_by_severity(self, severity: ValidationSeverity) -> List[ValidationError]:
        """按严重程度获取错误
        
        Args:
            severity: 严重程度
            
        Returns:
            指定严重程度的错误列表
        """
        return [error for error in self.errors if error.severity == severity]
    
    def get_failed_validators(self) -> List[str]:
        """获取失败的验证器列表
        
        Returns:
            失败的验证器名称列表
        """
        return [
            name for name, status in self.validator_results.items()
            if status in [ValidationStatus.ERROR, ValidationStatus.CRITICAL]
        ]
    
    def get_error_summary(self) -> Dict[str, int]:
        """获取错误摘要统计
        
        Returns:
            错误类型和数量的统计
        """
        summary = {}
        for error in self.errors:
            summary[error.code] = summary.get(error.code, 0) + 1
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            验证结果的完整字典表示
        """
        return {
            "status": self.status.value,
            "is_valid": self.is_valid,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "metadata": self.metadata,
            "metrics": self.metrics.to_dict(),
            "request_id": self.request_id,
            "validator_results": {k: v.value for k, v in self.validator_results.items()},
            "execution_order": self.execution_order,
            "execution_time": round(self.execution_time, 3),
            "has_critical_errors": self.has_critical_errors,
            "failed_validators": self.get_failed_validators(),
            "error_summary": self.get_error_summary(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }
    
    def to_http_response(self) -> Dict[str, Any]:
        """转换为HTTP响应格式
        
        Returns:
            适合HTTP响应的字典格式
        """
        if self.is_valid:
            response = {
                "success": True,
                "status": self.status.value,
                "execution_time": round(self.execution_time, 3)
            }
            
            # 只在有警告时包含警告信息
            if self.warnings:
                response["warnings"] = [warning.to_dict() for warning in self.warnings]
                
            # 只在有元数据时包含元数据
            if self.metadata:
                response["metadata"] = self.metadata
                
        else:
            response = {
                "success": False,
                "status": self.status.value,
                "errors": [error.to_dict() for error in self.errors],
                "failed_validators": self.get_failed_validators(),
                "execution_time": round(self.execution_time, 3)
            }
            
            # 包含请求ID用于问题追踪
            if self.request_id:
                response["request_id"] = self.request_id
                
            # 只在有警告时包含警告信息
            if self.warnings:
                response["warnings"] = [warning.to_dict() for warning in self.warnings]
        
        return response
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串
        
        Args:
            indent: JSON缩进
            
        Returns:
            JSON格式的字符串
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_summary(self) -> str:
        """生成结果摘要字符串
        
        Returns:
            包含关键信息的摘要字符串
        """
        return (
            f"ValidationResult(status={self.status.value}, "
            f"errors={len(self.errors)}, warnings={len(self.warnings)}, "
            f"validators={self.metrics.executed_validators}, "
            f"execution_time={self.execution_time:.3f}s, "
            f"success_rate={self.metrics.get_success_rate():.1%})"
        )
    
    @classmethod
    def create_success(cls, metadata: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> 'ValidationResult':
        """创建成功结果
        
        Args:
            metadata: 可选的元数据
            request_id: 可选的请求ID
            
        Returns:
            成功的验证结果实例
        """
        return cls(
            status=ValidationStatus.SUCCESS,
            metadata=metadata or {},
            request_id=request_id
        )
    
    @classmethod
    def create_error(
        cls, 
        error: ValidationError, 
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> 'ValidationResult':
        """创建错误结果
        
        Args:
            error: 验证错误
            metadata: 可选的元数据
            request_id: 可选的请求ID
            
        Returns:
            包含错误的验证结果实例
        """
        result = cls(
            status=ValidationStatus.ERROR,
            metadata=metadata or {},
            request_id=request_id
        )
        result.add_error(error)
        return result
    
    @classmethod
    def create_warning(
        cls,
        warning: ValidationError,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> 'ValidationResult':
        """创建警告结果
        
        Args:
            warning: 验证警告
            metadata: 可选的元数据
            request_id: 可选的请求ID
            
        Returns:
            包含警告的验证结果实例
        """
        result = cls(
            status=ValidationStatus.SUCCESS,
            metadata=metadata or {},
            request_id=request_id
        )
        result.add_warning(warning)
        return result