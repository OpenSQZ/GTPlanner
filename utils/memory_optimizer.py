"""
内存优化器

为GTPlanner提供全面的内存优化功能，包括：
- 内存使用监控
- 智能垃圾回收
- 内存泄漏检测
- 数据结构优化
- 内存压缩
- 内存池管理
"""

import gc
import sys
import psutil
import threading
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import weakref
import tracemalloc

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """内存统计信息"""
    total_memory_mb: float = 0.0
    used_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    memory_percentage: float = 0.0
    process_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    gc_objects: int = 0
    gc_collections: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MemoryLeak:
    """内存泄漏信息"""
    object_type: str
    count: int
    size_bytes: int
    growth_rate: float
    first_detected: datetime
    last_updated: datetime


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, enable_tracemalloc: bool = True):
        self.enable_tracemalloc = enable_tracemalloc
        self.memory_history: List[MemoryStats] = []
        self.leak_detection_threshold = 0.1  # 10%增长阈值
        self.monitoring_interval = 30.0  # 30秒
        
        # 内存泄漏检测
        self.object_counts: Dict[str, int] = defaultdict(int)
        self.previous_counts: Dict[str, int] = {}
        self.detected_leaks: Dict[str, MemoryLeak] = {}
        
        # 监控线程
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # 启动内存跟踪
        if self.enable_tracemalloc:
            tracemalloc.start()
        
        logger.info("内存监控器初始化完成")
    
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
        logger.info("内存监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if self._monitoring_thread:
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5.0)
            logger.info("内存监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while not self._stop_monitoring.is_set():
            try:
                self._collect_memory_stats()
                self._detect_memory_leaks()
                self._stop_monitoring.wait(self.monitoring_interval)
            except Exception as e:
                logger.error(f"内存监控循环出错: {e}")
                time.sleep(5.0)
    
    def _collect_memory_stats(self):
        """收集内存统计信息"""
        try:
            # 系统内存信息
            memory_info = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # 垃圾回收信息
            gc_stats = gc.get_stats()
            total_collections = sum(stat['collections'] for stat in gc_stats)
            
            stats = MemoryStats(
                total_memory_mb=memory_info.total / (1024 * 1024),
                used_memory_mb=memory_info.used / (1024 * 1024),
                available_memory_mb=memory_info.available / (1024 * 1024),
                memory_percentage=memory_info.percent,
                process_memory_mb=process_memory.rss / (1024 * 1024),
                gc_objects=len(gc.get_objects()),
                gc_collections=total_collections
            )
            
            # 更新峰值内存
            if self.memory_history:
                stats.peak_memory_mb = max(
                    self.memory_history[-1].peak_memory_mb,
                    stats.process_memory_mb
                )
            else:
                stats.peak_memory_mb = stats.process_memory_mb
            
            self.memory_history.append(stats)
            
            # 限制历史记录大小
            if len(self.memory_history) > 100:
                self.memory_history = self.memory_history[-50:]
            
        except Exception as e:
            logger.error(f"收集内存统计信息失败: {e}")
    
    def _detect_memory_leaks(self):
        """检测内存泄漏"""
        try:
            # 统计对象数量
            current_counts = defaultdict(int)
            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                current_counts[obj_type] += 1
            
            # 检测增长
            for obj_type, current_count in current_counts.items():
                if obj_type in self.previous_counts:
                    previous_count = self.previous_counts[obj_type]
                    if current_count > previous_count:
                        growth_rate = (current_count - previous_count) / previous_count
                        
                        if growth_rate > self.leak_detection_threshold:
                            # 检测到潜在泄漏
                            if obj_type in self.detected_leaks:
                                leak = self.detected_leaks[obj_type]
                                leak.count = current_count
                                leak.growth_rate = growth_rate
                                leak.last_updated = datetime.now()
                            else:
                                self.detected_leaks[obj_type] = MemoryLeak(
                                    object_type=obj_type,
                                    count=current_count,
                                    size_bytes=0,  # 需要更复杂的计算
                                    growth_rate=growth_rate,
                                    first_detected=datetime.now(),
                                    last_updated=datetime.now()
                                )
                                
                                logger.warning(f"检测到潜在内存泄漏: {obj_type}, 增长率: {growth_rate:.2%}")
            
            self.previous_counts = current_counts.copy()
            
        except Exception as e:
            logger.error(f"内存泄漏检测失败: {e}")
    
    def get_current_stats(self) -> MemoryStats:
        """获取当前内存统计"""
        if self.memory_history:
            return self.memory_history[-1]
        else:
            self._collect_memory_stats()
            return self.memory_history[-1] if self.memory_history else MemoryStats()
    
    def get_memory_trend(self) -> Dict[str, Any]:
        """获取内存趋势"""
        if len(self.memory_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent_stats = self.memory_history[-10:]  # 最近10次记录
        if len(recent_stats) < 2:
            return {"trend": "insufficient_data"}
        
        # 计算趋势
        memory_values = [stat.process_memory_mb for stat in recent_stats]
        trend_slope = (memory_values[-1] - memory_values[0]) / len(memory_values)
        
        if trend_slope > 1.0:  # 增长超过1MB
            trend = "increasing"
        elif trend_slope < -1.0:  # 减少超过1MB
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "slope": trend_slope,
            "current_memory": memory_values[-1],
            "peak_memory": max(memory_values),
            "min_memory": min(memory_values)
        }
    
    def get_detected_leaks(self) -> Dict[str, MemoryLeak]:
        """获取检测到的内存泄漏"""
        return self.detected_leaks.copy()


class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self, monitor: Optional[MemoryMonitor] = None):
        self.monitor = monitor or MemoryMonitor()
        self.optimization_callbacks: List[Callable] = []
        self.memory_threshold_mb = 500  # 500MB阈值
        
        logger.info("内存优化器初始化完成")
    
    def add_optimization_callback(self, callback: Callable):
        """添加优化回调函数"""
        self.optimization_callbacks.append(callback)
    
    def optimize_memory(self) -> Dict[str, Any]:
        """执行内存优化"""
        optimization_result = {
            "before_memory": 0.0,
            "after_memory": 0.0,
            "freed_memory": 0.0,
            "optimizations_applied": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 记录优化前内存
            before_stats = self.monitor.get_current_stats()
            optimization_result["before_memory"] = before_stats.process_memory_mb
            
            # 执行垃圾回收
            gc_result = self._force_garbage_collection()
            optimization_result["optimizations_applied"].append("garbage_collection")
            optimization_result["gc_collections"] = gc_result
            
            # 执行自定义优化回调
            for callback in self.optimization_callbacks:
                try:
                    callback()
                    optimization_result["optimizations_applied"].append(f"callback_{callback.__name__}")
                except Exception as e:
                    logger.error(f"优化回调执行失败: {e}")
            
            # 记录优化后内存
            after_stats = self.monitor.get_current_stats()
            optimization_result["after_memory"] = after_stats.process_memory_mb
            optimization_result["freed_memory"] = before_stats.process_memory_mb - after_stats.process_memory_mb
            
            logger.info(f"内存优化完成，释放内存: {optimization_result['freed_memory']:.2f}MB")
            
        except Exception as e:
            logger.error(f"内存优化失败: {e}")
            optimization_result["error"] = str(e)
        
        return optimization_result
    
    def _force_garbage_collection(self) -> int:
        """强制垃圾回收"""
        before_collections = sum(stat['collections'] for stat in gc.get_stats())
        
        # 执行多轮垃圾回收
        for generation in range(3):
            collected = gc.collect(generation)
            logger.debug(f"第{generation}代垃圾回收，回收对象: {collected}")
        
        after_collections = sum(stat['collections'] for stat in gc.get_stats())
        return after_collections - before_collections
    
    def should_optimize(self) -> bool:
        """判断是否需要优化"""
        stats = self.monitor.get_current_stats()
        return stats.process_memory_mb > self.memory_threshold_mb
    
    def auto_optimize_if_needed(self) -> Optional[Dict[str, Any]]:
        """如果需要则自动优化"""
        if self.should_optimize():
            logger.info("内存使用超过阈值，执行自动优化")
            return self.optimize_memory()
        return None


class MemoryPool:
    """内存池管理器"""
    
    def __init__(self, pool_size: int = 100):
        self.pool_size = pool_size
        self.pools: Dict[str, List[Any]] = defaultdict(list)
        self.pool_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        
        logger.info(f"内存池管理器初始化完成，池大小: {pool_size}")
    
    def get_object(self, object_type: str, factory_func: Callable) -> Any:
        """从池中获取对象"""
        with self.pool_locks[object_type]:
            if self.pools[object_type]:
                obj = self.pools[object_type].pop()
                logger.debug(f"从池中获取对象: {object_type}")
                return obj
            else:
                obj = factory_func()
                logger.debug(f"创建新对象: {object_type}")
                return obj
    
    def return_object(self, object_type: str, obj: Any):
        """将对象返回到池中"""
        with self.pool_locks[object_type]:
            if len(self.pools[object_type]) < self.pool_size:
                self.pools[object_type].append(obj)
                logger.debug(f"对象返回到池: {object_type}")
            else:
                logger.debug(f"池已满，丢弃对象: {object_type}")


class WeakReferenceManager:
    """弱引用管理器"""
    
    def __init__(self):
        self.weak_refs: List[weakref.ref] = []
        self.callbacks: List[Callable] = []
    
    def add_weak_ref(self, obj: Any, callback: Optional[Callable] = None):
        """添加弱引用"""
        def cleanup(ref):
            if callback:
                callback(ref)
            logger.debug(f"弱引用对象被清理: {ref}")
        
        weak_ref = weakref.ref(obj, cleanup)
        self.weak_refs.append(weak_ref)
        if callback:
            self.callbacks.append(callback)
    
    def cleanup_dead_refs(self):
        """清理死引用"""
        alive_refs = []
        for ref in self.weak_refs:
            if ref() is not None:
                alive_refs.append(ref)
        
        dead_count = len(self.weak_refs) - len(alive_refs)
        self.weak_refs = alive_refs
        
        if dead_count > 0:
            logger.debug(f"清理了 {dead_count} 个死引用")


# 全局实例
_global_memory_monitor: Optional[MemoryMonitor] = None
_global_memory_optimizer: Optional[MemoryOptimizer] = None
_global_memory_pool: Optional[MemoryPool] = None
_global_weak_ref_manager: Optional[WeakReferenceManager] = None


def get_global_memory_monitor() -> MemoryMonitor:
    """获取全局内存监控器"""
    global _global_memory_monitor
    if _global_memory_monitor is None:
        _global_memory_monitor = MemoryMonitor()
        _global_memory_monitor.start_monitoring()
    return _global_memory_monitor


def get_global_memory_optimizer() -> MemoryOptimizer:
    """获取全局内存优化器"""
    global _global_memory_optimizer
    if _global_memory_optimizer is None:
        _global_memory_optimizer = MemoryOptimizer()
    return _global_memory_optimizer


def get_global_memory_pool() -> MemoryPool:
    """获取全局内存池"""
    global _global_memory_pool
    if _global_memory_pool is None:
        _global_memory_pool = MemoryPool()
    return _global_memory_pool


def get_global_weak_ref_manager() -> WeakReferenceManager:
    """获取全局弱引用管理器"""
    global _global_weak_ref_manager
    if _global_weak_ref_manager is None:
        _global_weak_ref_manager = WeakReferenceManager()
    return _global_weak_ref_manager


# 便捷函数
def get_memory_stats() -> MemoryStats:
    """获取内存统计信息"""
    monitor = get_global_memory_monitor()
    return monitor.get_current_stats()


def optimize_memory() -> Dict[str, Any]:
    """执行内存优化"""
    optimizer = get_global_memory_optimizer()
    return optimizer.optimize_memory()


def get_memory_report() -> Dict[str, Any]:
    """获取内存报告"""
    monitor = get_global_memory_monitor()
    optimizer = get_global_memory_optimizer()
    
    return {
        "current_stats": monitor.get_current_stats().__dict__,
        "memory_trend": monitor.get_memory_trend(),
        "detected_leaks": {
            leak_type: {
                "count": leak.count,
                "growth_rate": leak.growth_rate,
                "first_detected": leak.first_detected.isoformat(),
                "last_updated": leak.last_updated.isoformat()
            }
            for leak_type, leak in monitor.get_detected_leaks().items()
        },
        "should_optimize": optimizer.should_optimize(),
        "timestamp": datetime.now().isoformat()
    }
