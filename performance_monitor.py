"""
性能监控系统
监控系统性能指标
"""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_connections: int
    query_count: int
    cache_hit_rate: float
    avg_response_time: float


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.metrics_history: deque = deque(maxlen=history_size)
        self.query_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.active_connections = 0
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
    
    def start_monitoring(self, interval: int = 60) -> None:
        """开始性能监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("性能监控已启动")
    
    def stop_monitoring(self) -> None:
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("性能监控已停止")
    
    def _monitor_loop(self, interval: int) -> None:
        """监控循环"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                with self.lock:
                    self.metrics_history.append(metrics)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"性能监控错误: {e}")
                time.sleep(interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        
        # 缓存命中率
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        # 平均响应时间
        avg_response_time = sum(self.query_times) / len(self.query_times) if self.query_times else 0
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            disk_usage_percent=disk_usage_percent,
            active_connections=self.active_connections,
            query_count=len(self.query_times),
            cache_hit_rate=cache_hit_rate,
            avg_response_time=avg_response_time
        )
    
    def record_query_time(self, query_time: float) -> None:
        """记录查询时间"""
        with self.lock:
            self.query_times.append(query_time)
            # 只保留最近1000个查询时间
            if len(self.query_times) > 1000:
                self.query_times = self.query_times[-1000:]
    
    def record_cache_hit(self) -> None:
        """记录缓存命中"""
        with self.lock:
            self.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """记录缓存未命中"""
        with self.lock:
            self.cache_misses += 1
    
    def increment_connections(self) -> None:
        """增加连接数"""
        with self.lock:
            self.active_connections += 1
    
    def decrement_connections(self) -> None:
        """减少连接数"""
        with self.lock:
            self.active_connections = max(0, self.active_connections - 1)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标"""
        if not self.metrics_history:
            return {}
        
        latest_metrics = self.metrics_history[-1]
        return asdict(latest_metrics)
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取历史性能指标"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            recent_metrics = [
                asdict(metrics) for metrics in self.metrics_history
                if metrics.timestamp >= cutoff_time
            ]
        
        return recent_metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics_history:
            return {}
        
        with self.lock:
            metrics_list = list(self.metrics_history)
            current_query_times = list(self.query_times)
        
        if not metrics_list:
            return {}
        
        # 计算统计信息
        cpu_values = [m.cpu_percent for m in metrics_list]
        memory_values = [m.memory_percent for m in metrics_list]
        
        # 直接基于当前查询时间计算平均响应时间
        avg_response_time = sum(current_query_times) / len(current_query_times) if current_query_times else 0
        
        return {
            'cpu_avg': sum(cpu_values) / len(cpu_values),
            'cpu_max': max(cpu_values),
            'cpu_min': min(cpu_values),
            'memory_avg': sum(memory_values) / len(memory_values),
            'memory_max': max(memory_values),
            'memory_min': min(memory_values),
            'response_time_avg': avg_response_time,
            'response_time_max': max(current_query_times) if current_query_times else 0,
            'response_time_min': min(current_query_times) if current_query_times else 0,
            'total_queries': len(current_query_times),
            'cache_hit_rate': (self.cache_hits / (self.cache_hits + self.cache_misses) * 100) if (self.cache_hits + self.cache_misses) > 0 else 0,
            'active_connections': self.active_connections
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """获取性能告警"""
        alerts = []
        current_metrics = self.get_current_metrics()
        
        if not current_metrics:
            return alerts
        
        # CPU使用率告警
        if current_metrics.get('cpu_percent', 0) > 80:
            alerts.append({
                'type': 'warning',
                'metric': 'cpu_percent',
                'value': current_metrics['cpu_percent'],
                'threshold': 80,
                'message': 'CPU使用率过高'
            })
        
        # 内存使用率告警
        if current_metrics.get('memory_percent', 0) > 85:
            alerts.append({
                'type': 'warning',
                'metric': 'memory_percent',
                'value': current_metrics['memory_percent'],
                'threshold': 85,
                'message': '内存使用率过高'
            })
        
        # 磁盘使用率告警
        if current_metrics.get('disk_usage_percent', 0) > 90:
            alerts.append({
                'type': 'critical',
                'metric': 'disk_usage_percent',
                'value': current_metrics['disk_usage_percent'],
                'threshold': 90,
                'message': '磁盘使用率过高'
            })
        
        # 响应时间告警
        if current_metrics.get('avg_response_time', 0) > 5.0:
            alerts.append({
                'type': 'warning',
                'metric': 'avg_response_time',
                'value': current_metrics['avg_response_time'],
                'threshold': 5.0,
                'message': '平均响应时间过长'
            })
        
        return alerts


# 全局性能监控实例
performance_monitor = PerformanceMonitor()


def start_performance_monitoring(interval: int = 60) -> None:
    """启动性能监控的便捷函数"""
    performance_monitor.start_monitoring(interval)


def stop_performance_monitoring() -> None:
    """停止性能监控的便捷函数"""
    performance_monitor.stop_monitoring()


def get_performance_summary() -> Dict[str, Any]:
    """获取性能摘要的便捷函数"""
    return performance_monitor.get_performance_summary()


def get_performance_alerts() -> List[Dict[str, Any]]:
    """获取性能告警的便捷函数"""
    return performance_monitor.get_alerts() 