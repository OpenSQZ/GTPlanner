"""
性能监控系统

为GTPlanner提供全面的性能监控和指标收集功能，包括：
- 请求响应时间监控
- 内存使用监控
- 数据库操作监控
- 缓存性能监控
- 异步任务监控
- 健康检查指标
"""

import asyncio
import time
import psutil
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import asynccontextmanager, contextmanager
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    # 请求指标
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float('inf')
    
    # 内存指标
    memory_usage_mb: float = 0.0
    peak_memory_mb: float = 0.0
    
    # 数据库指标
    db_queries: int = 0
    db_query_time: float = 0.0
    avg_db_query_time: float = 0.0
    
    # 缓存指标
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    
    # 异步任务指标
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    # 时间戳
    last_updated: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, enable_detailed_monitoring: bool = True):
        """
        初始化性能监控器
        
        Args:
            enable_detailed_monitoring: 是否启用详细监控
        """
        self.enable_detailed_monitoring = enable_detailed_monitoring
        self.metrics = PerformanceMetrics()
        
        # 响应时间历史记录
        self.response_times = deque(maxlen=1000)
        
        # 监控线程
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # 监控间隔
        self.monitoring_interval = 5.0  # 5秒
        
        # 回调函数
        self.metrics_callbacks: List[Callable[[PerformanceMetrics], None]] = []
        
        logger.info("性能监控系统初始化完成")
    
    def start_monitoring(self):
        """开始监控"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return
        
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if self._monitoring_thread:
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5.0)
            logger.info("性能监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while not self._stop_monitoring.is_set():
            try:
                self._update_metrics()
                self._notify_callbacks()
                
                # 等待下次监控
                self._stop_monitoring.wait(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(1.0)
    
    def _update_metrics(self):
        """更新指标"""
        # 更新内存使用
        process = psutil.Process()
        memory_info = process.memory_info()
        current_memory_mb = memory_info.rss / (1024 * 1024)
        
        self.metrics.memory_usage_mb = current_memory_mb
        if current_memory_mb > self.metrics.peak_memory_mb:
            self.metrics.peak_memory_mb = current_memory_mb
        
        # 更新响应时间统计
        if self.response_times:
            self.metrics.avg_response_time = sum(self.response_times) / len(self.response_times)
            self.metrics.max_response_time = max(self.response_times)
            self.metrics.min_response_time = min(self.response_times)
        
        # 更新缓存命中率
        total_cache_requests = self.metrics.cache_hits + self.metrics.cache_misses
        if total_cache_requests > 0:
            self.metrics.cache_hit_rate = self.metrics.cache_hits / total_cache_requests
        
        # 更新数据库平均查询时间
        if self.metrics.db_queries > 0:
            self.metrics.avg_db_query_time = self.metrics.db_query_time / self.metrics.db_queries
        
        self.metrics.last_updated = datetime.now()
    
    def _notify_callbacks(self):
        """通知回调函数"""
        for callback in self.metrics_callbacks:
            try:
                callback(self.metrics)
            except Exception as e:
                logger.error(f"指标回调出错: {e}")
    
    def add_metrics_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """添加指标回调函数"""
        self.metrics_callbacks.append(callback)
    
    def record_request(self, response_time: float, success: bool = True):
        """记录请求"""
        self.metrics.total_requests += 1
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        self.response_times.append(response_time)
    
    def record_db_query(self, query_time: float):
        """记录数据库查询"""
        self.metrics.db_queries += 1
        self.metrics.db_query_time += query_time
    
    def record_cache_hit(self):
        """记录缓存命中"""
        self.metrics.cache_hits += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        self.metrics.cache_misses += 1
    
    def record_task_start(self):
        """记录任务开始"""
        self.metrics.active_tasks += 1
    
    def record_task_complete(self, success: bool = True):
        """记录任务完成"""
        if self.metrics.active_tasks > 0:
            self.metrics.active_tasks -= 1
        
        if success:
            self.metrics.completed_tasks += 1
        else:
            self.metrics.failed_tasks += 1
    
    def get_metrics(self) -> PerformanceMetrics:
        """获取当前指标"""
        self._update_metrics()
        return self.metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        metrics = self.get_metrics()
        
        # 计算健康分数
        health_score = 100
        
        # 响应时间健康度
        if metrics.avg_response_time > 5.0:  # 超过5秒
            health_score -= 20
        elif metrics.avg_response_time > 2.0:  # 超过2秒
            health_score -= 10
        
        # 内存使用健康度
        if metrics.memory_usage_mb > 1000:  # 超过1GB
            health_score -= 20
        elif metrics.memory_usage_mb > 500:  # 超过500MB
            health_score -= 10
        
        # 错误率健康度
        if metrics.total_requests > 0:
            error_rate = metrics.failed_requests / metrics.total_requests
            if error_rate > 0.1:  # 错误率超过10%
                health_score -= 30
            elif error_rate > 0.05:  # 错误率超过5%
                health_score -= 15
        
        # 缓存命中率健康度
        if metrics.cache_hit_rate < 0.5:  # 命中率低于50%
            health_score -= 10
        
        health_score = max(0, health_score)
        
        return {
            "status": "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical",
            "score": health_score,
            "metrics": {
                "total_requests": metrics.total_requests,
                "success_rate": metrics.successful_requests / max(1, metrics.total_requests),
                "avg_response_time": metrics.avg_response_time,
                "memory_usage_mb": metrics.memory_usage_mb,
                "cache_hit_rate": metrics.cache_hit_rate,
                "active_tasks": metrics.active_tasks
            },
            "timestamp": metrics.last_updated.isoformat()
        }


# 全局监控器实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_global_monitor() -> PerformanceMonitor:
    """获取全局监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
        _global_monitor.start_monitoring()
    return _global_monitor


# 装饰器和上下文管理器
@contextmanager
def monitor_request(monitor: Optional[PerformanceMonitor] = None):
    """监控请求的上下文管理器"""
    monitor = monitor or get_global_monitor()
    start_time = time.time()
    
    try:
        yield
        response_time = time.time() - start_time
        monitor.record_request(response_time, success=True)
    except Exception:
        response_time = time.time() - start_time
        monitor.record_request(response_time, success=False)
        raise


@asynccontextmanager
async def monitor_async_request(monitor: Optional[PerformanceMonitor] = None):
    """监控异步请求的上下文管理器"""
    monitor = monitor or get_global_monitor()
    start_time = time.time()
    
    try:
        yield
        response_time = time.time() - start_time
        monitor.record_request(response_time, success=True)
    except Exception:
        response_time = time.time() - start_time
        monitor.record_request(response_time, success=False)
        raise


@contextmanager
def monitor_db_query(monitor: Optional[PerformanceMonitor] = None):
    """监控数据库查询的上下文管理器"""
    monitor = monitor or get_global_monitor()
    start_time = time.time()
    
    try:
        yield
        query_time = time.time() - start_time
        monitor.record_db_query(query_time)
    except Exception:
        query_time = time.time() - start_time
        monitor.record_db_query(query_time)
        raise


@asynccontextmanager
async def monitor_async_task(monitor: Optional[PerformanceMonitor] = None):
    """监控异步任务的上下文管理器"""
    monitor = monitor or get_global_monitor()
    monitor.record_task_start()
    
    try:
        yield
        monitor.record_task_complete(success=True)
    except Exception:
        monitor.record_task_complete(success=False)
        raise


def monitor_function(monitor: Optional[PerformanceMonitor] = None):
    """函数监控装饰器"""
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                async with monitor_async_request(monitor):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with monitor_request(monitor):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator


class PerformanceReporter:
    """性能报告器"""
    
    def __init__(self, monitor: Optional[PerformanceMonitor] = None):
        self.monitor = monitor or get_global_monitor()
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        metrics = self.monitor.get_metrics()
        health = self.monitor.get_health_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health": health,
            "performance_metrics": {
                "requests": {
                    "total": metrics.total_requests,
                    "successful": metrics.successful_requests,
                    "failed": metrics.failed_requests,
                    "success_rate": metrics.successful_requests / max(1, metrics.total_requests)
                },
                "response_times": {
                    "average": metrics.avg_response_time,
                    "maximum": metrics.max_response_time,
                    "minimum": metrics.min_response_time if metrics.min_response_time != float('inf') else 0
                },
                "memory": {
                    "current_mb": metrics.memory_usage_mb,
                    "peak_mb": metrics.peak_memory_mb
                },
                "database": {
                    "queries": metrics.db_queries,
                    "total_time": metrics.db_query_time,
                    "average_time": metrics.avg_db_query_time
                },
                "cache": {
                    "hits": metrics.cache_hits,
                    "misses": metrics.cache_misses,
                    "hit_rate": metrics.cache_hit_rate
                },
                "tasks": {
                    "active": metrics.active_tasks,
                    "completed": metrics.completed_tasks,
                    "failed": metrics.failed_tasks
                }
            }
        }
    
    def log_performance_summary(self):
        """记录性能摘要"""
        report = self.generate_report()
        health = report["health"]
        
        logger.info(f"性能摘要 - 状态: {health['status']}, 分数: {health['score']}")
        logger.info(f"请求: {report['performance_metrics']['requests']['total']} "
                   f"(成功率: {report['performance_metrics']['requests']['success_rate']:.2%})")
        logger.info(f"平均响应时间: {report['performance_metrics']['response_times']['average']:.3f}s")
        logger.info(f"内存使用: {report['performance_metrics']['memory']['current_mb']:.1f}MB")
        logger.info(f"缓存命中率: {report['performance_metrics']['cache']['hit_rate']:.2%}")


# 便捷函数
def get_performance_report() -> Dict[str, Any]:
    """获取性能报告"""
    reporter = PerformanceReporter()
    return reporter.generate_report()


def log_performance_summary():
    """记录性能摘要"""
    reporter = PerformanceReporter()
    reporter.log_performance_summary()
