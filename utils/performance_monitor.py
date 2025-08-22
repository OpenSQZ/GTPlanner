"""
性能监控系统 - Performance Monitoring System

这个模块是GTPlanner项目的性能监控增强功能，主要解决原有系统缺乏性能监控、
难以优化的问题。

主要功能：
1. 函数执行时间监控，识别性能瓶颈
2. 内存使用情况跟踪，防止内存泄漏
3. 性能指标收集和分析，支持优化决策
4. 性能报告生成和导出，便于性能分析

技术原理：
- 装饰器模式：自动拦截函数执行，收集性能数据
- 内存监控：使用psutil库监控系统资源使用
- 数据统计：收集、存储和分析性能指标
- 报告生成：支持多种格式的性能报告导出

与GTPlanner的集成作用：
- 识别系统性能瓶颈
- 支持性能优化决策
- 提供性能基准测试
- 便于系统调优和扩展
"""

import functools
import json
import csv
import time
import psutil
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
import statistics

# 性能指标数据类
# 记录单个函数执行的详细性能信息
@dataclass
class PerformanceMetric:
    """
    性能指标数据结构
    
    记录函数执行的详细性能信息，包括：
    1. 执行时间：函数运行耗时
    2. 内存使用：执行前后的内存变化
    3. 执行状态：成功或失败
    4. 时间戳：执行的具体时间
    
    与GTPlanner的集成价值：
    - 为性能优化提供数据基础
    - 支持性能基准测试
    - 便于性能问题定位
    """
    
    function_name: str                    # 函数名称
    execution_time: float                 # 执行时间（秒）
    memory_before: float                  # 执行前内存使用（MB）
    memory_after: float                   # 执行后内存使用（MB）
    memory_delta: float                   # 内存变化量（MB）
    timestamp: datetime                   # 执行时间戳
    success: bool                         # 执行是否成功
    error_message: Optional[str] = None   # 错误信息（如果执行失败）
    additional_data: Dict[str, Any] = field(default_factory=dict)  # 额外数据

# 性能统计信息数据类
# 汇总多个性能指标，提供统计视图
@dataclass
class PerformanceStats:
    """
    性能统计信息
    
    汇总多个性能指标，提供统计视图，包括：
    1. 执行次数统计
    2. 时间分布统计
    3. 内存使用统计
    4. 成功率统计
    
    与GTPlanner的集成价值：
    - 提供性能趋势分析
    - 支持性能基准比较
    - 便于性能优化决策
    """
    
    function_name: str                    # 函数名称
    total_calls: int                      # 总调用次数
    successful_calls: int                 # 成功调用次数
    failed_calls: int                     # 失败调用次数
    success_rate: float                   # 成功率
    avg_execution_time: float             # 平均执行时间
    min_execution_time: float             # 最小执行时间
    max_execution_time: float             # 最大执行时间
    std_execution_time: float             # 执行时间标准差
    avg_memory_delta: float               # 平均内存变化
    total_memory_used: float              # 总内存使用量
    last_execution: Optional[datetime]    # 最后执行时间

class PerformanceMonitor:
    """
    性能监控器
    
    这是GTPlanner性能监控系统的核心类，提供：
    1. 自动性能数据收集
    2. 性能指标统计分析
    3. 性能报告生成
    4. 性能数据导出
    
    主要特性：
    - 装饰器接口：简单易用的性能监控
    - 内存监控：实时跟踪内存使用情况
    - 统计分析：提供详细的性能统计信息
    - 报告导出：支持多种格式的性能报告
    
    与GTPlanner的集成价值：
    - 识别系统性能瓶颈
    - 支持性能优化决策
    - 提供性能基准测试
    - 便于系统调优和扩展
    """
    
    def __init__(self, max_metrics: int = 10000):
        """
        初始化性能监控器
        
        Args:
            max_metrics: 最大存储的性能指标数量，防止内存无限增长
        """
        self.max_metrics = max_metrics
        self.metrics: List[PerformanceMetric] = []
        self.function_stats: Dict[str, PerformanceStats] = {}
        self.monitoring_enabled = True
        
        # 初始化进程监控
        self.process = psutil.Process()
    
    def monitor_function(self, func: Callable) -> Callable:
        """
        性能监控装饰器
        
        自动监控函数的执行性能，收集详细的性能指标。
        
        使用方式：
        @performance_monitor.monitor_function
        def expensive_function():
            # 函数体
            pass
        
        与GTPlanner的集成价值：
        - 自动性能数据收集
        - 支持性能瓶颈识别
        - 便于性能优化决策
        
        Args:
            func: 要监控的函数
            
        Returns:
            包装后的函数，自动收集性能数据
        """
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.monitoring_enabled:
                return func(*args, **kwargs)
            
            # 记录开始时间和内存
            start_time = time.time()
            memory_before = self._get_memory_usage()
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 记录成功执行的性能指标
                self._record_metric(
                    func_name=func.__name__,
                    execution_time=time.time() - start_time,
                    memory_before=memory_before,
                    memory_after=self._get_memory_usage(),
                    success=True
                )
                
                return result
                
            except Exception as e:
                # 记录失败执行的性能指标
                self._record_metric(
                    func_name=func.__name__,
                    execution_time=time.time() - start_time,
                    memory_before=memory_before,
                    memory_after=self._get_memory_usage(),
                    success=False,
                    error_message=str(e)
                )
                
                # 重新抛出异常
                raise
        
        return wrapper
    
    def _get_memory_usage(self) -> float:
        """
        获取当前内存使用量
        
        使用psutil库获取当前进程的内存使用情况。
        
        Returns:
            内存使用量（MB）
        """
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024  # 转换为MB
        except Exception:
            return 0.0
    
    def _record_metric(self, func_name: str, execution_time: float,
                       memory_before: float, memory_after: float,
                       success: bool, error_message: str = None,
                       additional_data: Dict[str, Any] = None):
        """
        记录性能指标
        
        创建并存储性能指标对象，同时更新统计信息。
        
        Args:
            func_name: 函数名称
            execution_time: 执行时间
            memory_before: 执行前内存使用
            memory_after: 执行后内存使用
            success: 执行是否成功
            error_message: 错误信息
            additional_data: 额外数据
        """
        # 创建性能指标对象
        metric = PerformanceMetric(
            function_name=func_name,
            execution_time=execution_time,
            memory_before=memory_before,
            memory_after=memory_after,
            memory_delta=memory_after - memory_before,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message,
            additional_data=additional_data or {}
        )
        
        # 添加到指标列表
        self.metrics.append(metric)
        
        # 限制指标数量，防止内存无限增长
        if len(self.metrics) > self.max_metrics:
            self.metrics.pop(0)
        
        # 更新统计信息
        self._update_stats(metric)
    
    def _update_stats(self, metric: PerformanceMetric):
        """
        更新统计信息
        
        根据新的性能指标更新函数的统计信息。
        
        Args:
            metric: 性能指标对象
        """
        func_name = metric.function_name
        
        if func_name not in self.function_stats:
            # 初始化新的函数统计
            self.function_stats[func_name] = PerformanceStats(
                function_name=func_name,
                total_calls=0,
                successful_calls=0,
                failed_calls=0,
                success_rate=0.0,
                avg_execution_time=0.0,
                min_execution_time=float('inf'),
                max_execution_time=0.0,
                std_execution_time=0.0,
                avg_memory_delta=0.0,
                total_memory_used=0.0,
                last_execution=None
            )
        
        stats = self.function_stats[func_name]
        
        # 更新基本统计
        stats.total_calls += 1
        if metric.success:
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1
        
        stats.success_rate = stats.successful_calls / stats.total_calls
        stats.last_execution = metric.timestamp
        
        # 更新执行时间统计
        if metric.execution_time < stats.min_execution_time:
            stats.min_execution_time = metric.execution_time
        if metric.execution_time > stats.max_execution_time:
            stats.max_execution_time = metric.execution_time
        
        # 计算平均执行时间
        total_time = stats.avg_execution_time * (stats.total_calls - 1) + metric.execution_time
        stats.avg_execution_time = total_time / stats.total_calls
        
        # 更新内存统计
        total_memory = stats.avg_memory_delta * (stats.total_calls - 1) + metric.memory_delta
        stats.avg_memory_delta = total_memory / stats.total_calls
        stats.total_memory_used += abs(metric.memory_delta)
    
    def get_function_stats(self, func_name: str) -> Optional[PerformanceStats]:
        """
        获取指定函数的性能统计
        
        Args:
            func_name: 函数名称
            
        Returns:
            函数的性能统计信息，如果不存在则返回None
        """
        return self.function_stats.get(func_name)
    
    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """
        获取所有函数的性能统计
        
        Returns:
            所有函数的性能统计信息字典
        """
        return self.function_stats.copy()
    
    def get_recent_metrics(self, func_name: str = None, limit: int = 100) -> List[PerformanceMetric]:
        """
        获取最近的性能指标
        
        Args:
            func_name: 函数名称，如果为None则返回所有函数的指标
            limit: 返回的指标数量限制
            
        Returns:
            最近的性能指标列表
        """
        if func_name:
            # 过滤指定函数的指标
            filtered_metrics = [m for m in self.metrics if m.function_name == func_name]
            return filtered_metrics[-limit:]
        else:
            # 返回所有函数的指标
            return self.metrics[-limit:]
    
    def calculate_performance_trends(self, func_name: str, 
                                   time_window: int = 3600) -> Dict[str, Any]:
        """
        计算性能趋势
        
        分析指定函数在时间窗口内的性能变化趋势。
        
        Args:
            func_name: 函数名称
            time_window: 时间窗口（秒）
            
        Returns:
            性能趋势分析结果
        """
        current_time = datetime.now()
        window_start = current_time.timestamp() - time_window
        
        # 过滤时间窗口内的指标
        recent_metrics = [
            m for m in self.metrics
            if m.function_name == func_name and m.timestamp.timestamp() >= window_start
        ]
        
        if not recent_metrics:
            return {
                'function_name': func_name,
                'time_window': time_window,
                'metrics_count': 0,
                'trend': 'insufficient_data'
            }
        
        # 计算趋势
        execution_times = [m.execution_time for m in recent_metrics]
        memory_deltas = [m.memory_delta for m in recent_metrics]
        
        # 时间趋势（简单线性回归）
        time_trend = self._calculate_trend(execution_times)
        memory_trend = self._calculate_trend(memory_deltas)
        
        return {
            'function_name': func_name,
            'time_window': time_window,
            'metrics_count': len(recent_metrics),
            'execution_time_trend': time_trend,
            'memory_trend': memory_trend,
            'avg_execution_time': statistics.mean(execution_times),
            'avg_memory_delta': statistics.mean(memory_deltas)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """
        计算数值趋势
        
        使用简单的统计方法判断数值的变化趋势。
        
        Args:
            values: 数值列表
            
        Returns:
            趋势描述：'improving', 'stable', 'degrading'
        """
        if len(values) < 2:
            return 'stable'
        
        # 计算变化率
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return 'stable'
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if first_avg == 0:
            return 'stable'
        
        change_rate = (second_avg - first_avg) / first_avg
        
        if change_rate < -0.1:  # 改善超过10%
            return 'improving'
        elif change_rate > 0.1:  # 恶化超过10%
            return 'degrading'
        else:
            return 'stable'
    
    def generate_report(self, format: str = "json") -> str:
        """
        生成性能报告
        
        生成指定格式的性能报告，支持JSON和CSV格式。
        
        Args:
            format: 报告格式，支持'json'和'csv'
            
        Returns:
            格式化的性能报告字符串
        """
        if format.lower() == "csv":
            return self._generate_csv_report()
        else:
            return self._generate_json_report()
    
    def _generate_json_report(self) -> str:
        """
        生成JSON格式的性能报告
        
        Returns:
            JSON格式的性能报告
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_functions': len(self.function_stats),
                'total_metrics': len(self.metrics),
                'monitoring_enabled': self.monitoring_enabled
            },
            'function_stats': {
                name: asdict(stats) for name, stats in self.function_stats.items()
            },
            'recent_metrics': [
                {
                    'function_name': m.function_name,
                    'execution_time': m.execution_time,
                    'memory_delta': m.memory_delta,
                    'success': m.success,
                    'timestamp': m.timestamp.isoformat()
                }
                for m in self.metrics[-100:]  # 最近100条指标
            ]
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def _generate_csv_report(self) -> str:
        """
        生成CSV格式的性能报告
        
        Returns:
            CSV格式的性能报告
        """
        if not self.metrics:
            return "No performance metrics available"
        
        # 创建CSV输出
        output = []
        
        # 添加函数统计信息
        output.append("Function Statistics")
        output.append("Function Name,Total Calls,Success Rate,Avg Execution Time,Avg Memory Delta")
        
        for stats in self.function_stats.values():
            output.append(f"{stats.function_name},{stats.total_calls},{stats.success_rate:.2f},"
                        f"{stats.avg_execution_time:.4f},{stats.avg_memory_delta:.2f}")
        
        # 添加最近指标
        output.append("\nRecent Performance Metrics")
        output.append("Function Name,Execution Time,Memory Delta,Success,Timestamp")
        
        for metric in self.metrics[-100:]:
            output.append(f"{metric.function_name},{metric.execution_time:.4f},"
                        f"{metric.memory_delta:.2f},{metric.success},{metric.timestamp}")
        
        return "\n".join(output)
    
    def export_metrics(self, filepath: str, format: str = "json"):
        """
        导出性能指标到文件
        
        将性能指标导出到指定文件，支持JSON和CSV格式。
        
        Args:
            filepath: 输出文件路径
            format: 导出格式，支持'json'和'csv'
        """
        if format.lower() == "csv":
            self._export_csv(filepath)
        else:
            self._export_json(filepath)
    
    def _export_json(self, filepath: str):
        """
        导出JSON格式的性能指标
        
        Args:
            filepath: 输出文件路径
        """
        report = self._generate_json_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
    
    def _export_csv(self, filepath: str):
        """
        导出CSV格式的性能指标
        
        Args:
            filepath: 输出文件路径
        """
        if not self.metrics:
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入函数统计
            writer.writerow(['Function Statistics'])
            writer.writerow(['Function Name', 'Total Calls', 'Success Rate', 
                           'Avg Execution Time', 'Avg Memory Delta'])
            
            for stats in self.function_stats.values():
                writer.writerow([
                    stats.function_name,
                    stats.total_calls,
                    f"{stats.success_rate:.2f}",
                    f"{stats.avg_execution_time:.4f}",
                    f"{stats.avg_memory_delta:.2f}"
                ])
            
            # 写入性能指标
            writer.writerow([])
            writer.writerow(['Performance Metrics'])
            writer.writerow(['Function Name', 'Execution Time', 'Memory Delta', 
                           'Success', 'Timestamp', 'Error Message'])
            
            for metric in self.metrics:
                writer.writerow([
                    metric.function_name,
                    f"{metric.execution_time:.4f}",
                    f"{metric.memory_delta:.2f}",
                    metric.success,
                    metric.timestamp.isoformat(),
                    metric.error_message or ''
                ])
    
    def clear_metrics(self):
        """
        清空所有性能指标
        
        用于测试或维护，清理所有性能数据。
        """
        self.metrics.clear()
        self.function_stats.clear()
    
    def enable_monitoring(self):
        """启用性能监控"""
        self.monitoring_enabled = True
    
    def disable_monitoring(self):
        """禁用性能监控"""
        self.monitoring_enabled = False
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        
        获取当前系统的资源使用情况。
        
        Returns:
            系统信息字典
        """
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'process_memory': self._get_memory_usage(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception:
            return {
                'error': 'Failed to get system info',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """
        获取整体性能统计
        
        汇总所有函数的性能数据，提供系统级别的性能概览。
        
        Returns:
            包含整体性能统计的字典
        """
        if not self.metrics:
            return {"error": "没有性能数据"}
        
        total_calls = sum(stats.total_calls for stats in self.function_stats.values())
        total_success = sum(stats.successful_calls for stats in self.function_stats.values())
        total_failed = sum(stats.failed_calls for stats in self.function_stats.values())
        
        # 计算整体执行时间统计
        all_execution_times = [m.execution_time for m in self.metrics]
        avg_execution_time = sum(all_execution_times) / len(all_execution_times) if all_execution_times else 0
        min_execution_time = min(all_execution_times) if all_execution_times else 0
        max_execution_time = max(all_execution_times) if all_execution_times else 0
        
        # 计算整体内存使用统计
        all_memory_deltas = [m.memory_delta for m in self.metrics]
        avg_memory_delta = sum(all_memory_deltas) / len(all_memory_deltas) if all_memory_deltas else 0
        total_memory_used = sum(all_memory_deltas)
        
        return {
            "total_calls": total_calls,
            "total_success": total_success,
            "total_failed": total_failed,
            "overall_success_rate": total_success / total_calls if total_calls > 0 else 0,
            "avg_execution_time": avg_execution_time,
            "min_execution_time": min_execution_time,
            "max_execution_time": max_execution_time,
            "avg_memory_delta": avg_memory_delta,
            "total_memory_used": total_memory_used,
            "monitored_functions": len(self.function_stats),
            "oldest_metric": min(m.timestamp for m in self.metrics) if self.metrics else None,
            "newest_metric": max(m.timestamp for m in self.metrics) if self.metrics else None
        }

# 全局性能监控器实例
# 提供便捷的全局访问接口
performance_monitor = PerformanceMonitor()

# 便捷的装饰器函数
# 简化性能监控的使用
def monitor_performance(func: Callable) -> Callable:
    """
    性能监控装饰器（便捷版本）
    
    使用全局性能监控器监控函数性能。
    
    使用方式：
    @monitor_performance
    def expensive_function():
        # 函数体
        pass
    
    与GTPlanner的集成价值：
    - 简单的性能监控接口
    - 自动性能数据收集
    - 支持性能优化决策
    """
    return performance_monitor.monitor_function(func)
