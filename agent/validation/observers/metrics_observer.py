"""
指标观察者

基于观察者模式的指标收集实现，提供：
- 验证成功率统计
- 验证器执行时间统计
- 错误类型分布统计
- 缓存命中率统计
- 指标数据导出
"""

import time
import json
from typing import Dict, Any, Optional, List
from collections import defaultdict, Counter
from threading import Lock
from ..core.interfaces import IValidationObserver, IValidationMetrics
from ..core.validation_context import ValidationContext
from ..core.validation_result import ValidationResult, ValidationStatus


class ValidationMetricsCollector(IValidationMetrics):
    """验证指标收集器 - 实现IValidationMetrics接口"""
    
    def __init__(self):
        self._lock = Lock()
        
        # 验证器指标
        self.validator_times: Dict[str, List[float]] = defaultdict(list)
        self.validator_results: Dict[str, Counter] = defaultdict(Counter)
        self.validator_cache_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"hits": 0, "misses": 0})
        
        # 全局指标
        self.total_validations = 0
        self.successful_validations = 0
        self.failed_validations = 0
        self.total_execution_time = 0.0
        
        # 错误统计
        self.error_codes: Counter = Counter()
        self.error_severities: Counter = Counter()
        self.error_validators: Counter = Counter()
        
        # 端点统计
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_time": 0.0,
            "avg_time": 0.0
        })
        
        # 时间统计
        self.start_time = time.time()
        self.last_reset_time = time.time()
    
    def record_validation_time(self, validator_name: str, duration: float) -> None:
        """记录验证执行时间
        
        Args:
            validator_name: 验证器名称
            duration: 执行时间（秒）
        """
        with self._lock:
            self.validator_times[validator_name].append(duration)
            
            # 限制历史记录数量（保留最近1000次）
            if len(self.validator_times[validator_name]) > 1000:
                self.validator_times[validator_name] = self.validator_times[validator_name][-1000:]
    
    def record_validation_result(self, validator_name: str, success: bool) -> None:
        """记录验证结果
        
        Args:
            validator_name: 验证器名称
            success: 验证是否成功
        """
        with self._lock:
            status = "success" if success else "failure"
            self.validator_results[validator_name][status] += 1
    
    def record_cache_hit(self, validator_name: str, hit: bool) -> None:
        """记录缓存命中情况
        
        Args:
            validator_name: 验证器名称
            hit: 是否命中缓存
        """
        with self._lock:
            if hit:
                self.validator_cache_stats[validator_name]["hits"] += 1
            else:
                self.validator_cache_stats[validator_name]["misses"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标数据
        
        Returns:
            指标数据字典
        """
        with self._lock:
            current_time = time.time()
            uptime = current_time - self.start_time
            
            # 计算验证器平均时间
            validator_avg_times = {}
            for validator_name, times in self.validator_times.items():
                if times:
                    validator_avg_times[validator_name] = sum(times) / len(times)
            
            # 计算验证器成功率
            validator_success_rates = {}
            for validator_name, results in self.validator_results.items():
                total = results["success"] + results["failure"]
                if total > 0:
                    validator_success_rates[validator_name] = results["success"] / total
            
            # 计算缓存命中率
            validator_cache_rates = {}
            for validator_name, stats in self.validator_cache_stats.items():
                total = stats["hits"] + stats["misses"]
                if total > 0:
                    validator_cache_rates[validator_name] = stats["hits"] / total
            
            return {
                # 全局指标
                "uptime_seconds": uptime,
                "total_validations": self.total_validations,
                "successful_validations": self.successful_validations,
                "failed_validations": self.failed_validations,
                "overall_success_rate": self.successful_validations / self.total_validations if self.total_validations > 0 else 0,
                "total_execution_time": self.total_execution_time,
                "average_execution_time": self.total_execution_time / self.total_validations if self.total_validations > 0 else 0,
                
                # 验证器指标
                "validator_avg_times": validator_avg_times,
                "validator_success_rates": validator_success_rates,
                "validator_cache_rates": validator_cache_rates,
                "validator_execution_counts": {
                    name: len(times) for name, times in self.validator_times.items()
                },
                
                # 错误统计
                "error_codes": dict(self.error_codes.most_common(10)),
                "error_severities": dict(self.error_severities),
                "error_validators": dict(self.error_validators.most_common(10)),
                
                # 端点统计
                "endpoint_stats": dict(self.endpoint_stats),
                
                # 时间信息
                "collection_start_time": self.start_time,
                "last_reset_time": self.last_reset_time,
                "metrics_collected_at": current_time
            }
    
    def reset_metrics(self) -> None:
        """重置所有指标数据"""
        with self._lock:
            self.validator_times.clear()
            self.validator_results.clear()
            self.validator_cache_stats.clear()
            
            self.total_validations = 0
            self.successful_validations = 0
            self.failed_validations = 0
            self.total_execution_time = 0.0
            
            self.error_codes.clear()
            self.error_severities.clear()
            self.error_validators.clear()
            
            self.endpoint_stats.clear()
            
            self.last_reset_time = time.time()
    
    def record_endpoint_validation(self, endpoint: str, success: bool, execution_time: float) -> None:
        """记录端点验证统计
        
        Args:
            endpoint: 端点路径
            success: 验证是否成功
            execution_time: 执行时间
        """
        with self._lock:
            stats = self.endpoint_stats[endpoint]
            stats["total_requests"] += 1
            stats["total_time"] += execution_time
            
            if success:
                stats["successful_requests"] += 1
            else:
                stats["failed_requests"] += 1
            
            # 更新平均时间
            stats["avg_time"] = stats["total_time"] / stats["total_requests"]


class MetricsObserver(IValidationObserver):
    """指标观察者 - 收集验证过程的性能和统计指标
    
    提供企业级的指标收集功能：
    - 实时性能指标收集
    - 验证器成功率统计
    - 错误类型分布分析
    - 缓存命中率监控
    - 指标数据导出和可视化
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 指标配置
        self.enabled = self.config.get("enabled", True)
        self.include_timing = self.config.get("include_timing", True)
        self.include_success_rate = self.config.get("include_success_rate", True)
        self.include_error_details = self.config.get("include_error_details", True)
        self.export_interval = self.config.get("export_interval", 60)
        self.max_history_size = self.config.get("max_history_size", 1000)
        
        # 初始化指标收集器
        self.metrics_collector = ValidationMetricsCollector()
        
        # 最后导出时间
        self.last_export_time = time.time()
    
    async def on_validation_start(self, context: ValidationContext) -> None:
        """验证开始事件
        
        Args:
            context: 验证上下文
        """
        if not self.enabled:
            return
        
        # 记录验证开始时间（存储在上下文中）
        context.add_metadata("metrics_start_time", time.time())
    
    async def on_validation_step(self, validator_name: str, result: ValidationResult) -> None:
        """验证步骤完成事件
        
        Args:
            validator_name: 验证器名称
            result: 验证结果
        """
        if not self.enabled:
            return
        
        # 记录验证器执行时间
        if self.include_timing:
            self.metrics_collector.record_validation_time(validator_name, result.execution_time)
        
        # 记录验证器结果
        if self.include_success_rate:
            success = result.status in [ValidationStatus.SUCCESS, ValidationStatus.WARNING]
            self.metrics_collector.record_validation_result(validator_name, success)
        
        # 记录缓存统计
        cache_hits = result.metrics.cache_hits
        cache_misses = result.metrics.cache_misses
        
        if cache_hits > 0:
            self.metrics_collector.record_cache_hit(validator_name, True)
        if cache_misses > 0:
            self.metrics_collector.record_cache_hit(validator_name, False)
    
    async def on_validation_complete(self, result: ValidationResult) -> None:
        """验证完成事件
        
        Args:
            result: 最终验证结果
        """
        if not self.enabled:
            return
        
        # 更新全局统计
        self.metrics_collector.total_validations += 1
        self.metrics_collector.total_execution_time += result.execution_time
        
        if result.is_valid:
            self.metrics_collector.successful_validations += 1
        else:
            self.metrics_collector.failed_validations += 1
        
        # 记录错误统计
        if self.include_error_details and result.has_errors:
            for error in result.errors:
                self.metrics_collector.error_codes[error.code] += 1
                self.metrics_collector.error_severities[error.severity.name] += 1
                if error.validator:
                    self.metrics_collector.error_validators[error.validator] += 1
        
        # 检查是否需要导出指标
        current_time = time.time()
        if current_time - self.last_export_time >= self.export_interval:
            await self._export_metrics()
            self.last_export_time = current_time
    
    async def on_validation_error(self, error: Exception, context: Optional[ValidationContext] = None) -> None:
        """验证错误事件
        
        Args:
            error: 发生的异常
            context: 验证上下文（可能为None）
        """
        if not self.enabled:
            return
        
        # 记录系统错误
        self.metrics_collector.error_codes[f"SYSTEM_ERROR_{type(error).__name__}"] += 1
        self.metrics_collector.error_severities["CRITICAL"] += 1
        
        # 如果有上下文，记录端点错误
        if context:
            endpoint = context.request_path
            self.metrics_collector.record_endpoint_validation(endpoint, False, context.get_execution_time())
    
    async def _export_metrics(self) -> None:
        """导出指标数据"""
        try:
            metrics_data = self.metrics_collector.get_metrics()
            
            # 这里可以实现指标数据的导出逻辑
            # 例如：写入文件、发送到监控系统、更新数据库等
            
            # 简单的控制台输出（可以替换为实际的导出逻辑）
            print(f"📊 验证指标导出 - 总验证次数: {metrics_data['total_validations']}, "
                  f"成功率: {metrics_data['overall_success_rate']:.1%}, "
                  f"平均执行时间: {metrics_data['average_execution_time']:.3f}s")
            
        except Exception as e:
            print(f"Warning: Failed to export metrics: {e}")
    
    def get_observer_name(self) -> str:
        """获取观察者名称
        
        Returns:
            观察者名称
        """
        return "metrics_observer"
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标数据
        
        Returns:
            当前指标数据字典
        """
        return self.metrics_collector.get_metrics()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要
        
        Returns:
            指标摘要字典
        """
        metrics = self.metrics_collector.get_metrics()
        
        return {
            "total_validations": metrics["total_validations"],
            "success_rate": metrics["overall_success_rate"],
            "avg_execution_time": metrics["average_execution_time"],
            "top_error_codes": list(metrics["error_codes"].keys())[:5],
            "active_validators": len(metrics["validator_avg_times"]),
            "uptime_hours": metrics["uptime_seconds"] / 3600
        }
    
    def export_metrics_to_json(self) -> str:
        """导出指标为JSON格式
        
        Returns:
            JSON格式的指标数据
        """
        metrics = self.metrics_collector.get_metrics()
        return json.dumps(metrics, indent=2, ensure_ascii=False)
    
    def export_metrics_to_csv(self) -> str:
        """导出指标为CSV格式
        
        Returns:
            CSV格式的指标数据
        """
        metrics = self.metrics_collector.get_metrics()
        lines = []
        
        # 验证器性能数据
        lines.append("validator_name,avg_time,success_rate,cache_hit_rate,execution_count")
        
        for validator_name in metrics["validator_avg_times"]:
            avg_time = metrics["validator_avg_times"].get(validator_name, 0)
            success_rate = metrics["validator_success_rates"].get(validator_name, 0)
            cache_rate = metrics["validator_cache_rates"].get(validator_name, 0)
            exec_count = metrics["validator_execution_counts"].get(validator_name, 0)
            
            lines.append(f"{validator_name},{avg_time:.3f},{success_rate:.3f},{cache_rate:.3f},{exec_count}")
        
        return "\n".join(lines)
    
    async def record_success(self, context: ValidationContext, execution_time: float) -> None:
        """记录成功事件
        
        Args:
            context: 验证上下文
            execution_time: 执行时间
        """
        if self.enabled:
            endpoint = context.request_path
            self.metrics_collector.record_endpoint_validation(endpoint, True, execution_time)
    
    async def record_error(self, path: str, error: str, execution_time: float) -> None:
        """记录错误事件
        
        Args:
            path: 请求路径
            error: 错误信息
            execution_time: 执行时间
        """
        if self.enabled:
            self.metrics_collector.record_endpoint_validation(path, False, execution_time)
    
    def reset_metrics(self) -> None:
        """重置指标数据"""
        self.metrics_collector.reset_metrics()
    
    def get_validator_performance(self, validator_name: str) -> Optional[Dict[str, Any]]:
        """获取特定验证器的性能指标
        
        Args:
            validator_name: 验证器名称
            
        Returns:
            验证器性能指标，如果不存在则返回None
        """
        metrics = self.metrics_collector.get_metrics()
        
        if validator_name not in metrics["validator_avg_times"]:
            return None
        
        return {
            "name": validator_name,
            "avg_execution_time": metrics["validator_avg_times"][validator_name],
            "success_rate": metrics["validator_success_rates"].get(validator_name, 0),
            "cache_hit_rate": metrics["validator_cache_rates"].get(validator_name, 0),
            "execution_count": metrics["validator_execution_counts"].get(validator_name, 0),
            "total_time": sum(self.metrics_collector.validator_times.get(validator_name, [])),
            "recent_times": self.metrics_collector.validator_times.get(validator_name, [])[-10:]  # 最近10次
        }
    
    def get_top_error_codes(self, limit: int = 10) -> List[tuple[str, int]]:
        """获取最常见的错误代码
        
        Args:
            limit: 返回数量限制
            
        Returns:
            错误代码和次数的元组列表
        """
        return self.metrics_collector.error_codes.most_common(limit)
    
    def get_endpoint_performance(self) -> Dict[str, Dict[str, Any]]:
        """获取端点性能统计
        
        Returns:
            端点性能统计字典
        """
        return dict(self.metrics_collector.endpoint_stats)
