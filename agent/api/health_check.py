"""
健康检查API

为GTPlanner提供全面的健康检查功能，包括：
- 系统状态检查
- 数据库连接检查
- 外部服务检查
- 性能指标检查
- 依赖服务检查
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.performance_monitor import get_global_monitor, get_performance_report
from utils.enhanced_error_handler import get_global_error_handler, get_error_statistics
from utils.advanced_cache import get_global_cache
from agent.persistence.connection_pool import get_global_connection_pool
from utils.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    response_time: float
    timestamp: datetime


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    message: str
    timestamp: str
    response_time: float
    checks: Dict[str, Any]
    performance: Dict[str, Any]
    errors: Dict[str, Any]


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks: Dict[str, callable] = {
            "database": self._check_database,
            "cache": self._check_cache,
            "llm_api": self._check_llm_api,
            "performance": self._check_performance,
            "memory": self._check_memory,
            "disk_space": self._check_disk_space,
        }
    
    async def _check_database(self) -> HealthCheckResult:
        """检查数据库连接"""
        start_time = time.time()
        
        try:
            pool = get_global_connection_pool()
            stats = pool.get_stats()
            
            # 检查连接池状态
            if stats.total_connections == 0:
                return HealthCheckResult(
                    status=HealthStatus.CRITICAL,
                    message="数据库连接池为空",
                    details={"stats": stats.__dict__},
                    response_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # 检查活跃连接
            if stats.active_connections >= stats.total_connections * 0.9:
                return HealthCheckResult(
                    status=HealthStatus.WARNING,
                    message="数据库连接使用率过高",
                    details={"stats": stats.__dict__},
                    response_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="数据库连接正常",
                details={"stats": stats.__dict__},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.CRITICAL,
                message=f"数据库检查失败: {e}",
                details={"error": str(e)},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    async def _check_cache(self) -> HealthCheckResult:
        """检查缓存状态"""
        start_time = time.time()
        
        try:
            cache = get_global_cache()
            stats = cache.get_stats()
            
            if not stats:
                return HealthCheckResult(
                    status=HealthStatus.WARNING,
                    message="缓存统计信息不可用",
                    details={},
                    response_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # 检查缓存命中率
            if stats.hit_rate < 0.5:
                return HealthCheckResult(
                    status=HealthStatus.WARNING,
                    message="缓存命中率较低",
                    details={"stats": stats.__dict__},
                    response_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="缓存状态正常",
                details={"stats": stats.__dict__},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.WARNING,
                message=f"缓存检查失败: {e}",
                details={"error": str(e)},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    async def _check_llm_api(self) -> HealthCheckResult:
        """检查LLM API连接"""
        start_time = time.time()
        
        try:
            client = OpenAIClient()
            
            # 简单的API调用测试
            response = await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                timeout=10
            )
            
            if response and response.choices:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message="LLM API连接正常",
                    details={"response_length": len(response.choices[0].message.content)},
                    response_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.WARNING,
                    message="LLM API响应异常",
                    details={"response": str(response)},
                    response_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.CRITICAL,
                message=f"LLM API连接失败: {e}",
                details={"error": str(e)},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    async def _check_performance(self) -> HealthCheckResult:
        """检查性能指标"""
        start_time = time.time()
        
        try:
            monitor = get_global_monitor()
            metrics = monitor.get_metrics()
            
            # 检查响应时间
            if metrics.avg_response_time > 5.0:
                return HealthCheckResult(
                    status=HealthStatus.WARNING,
                    message="平均响应时间过长",
                    details={"metrics": metrics.__dict__},
                    response_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # 检查错误率
            if metrics.total_requests > 0:
                error_rate = metrics.failed_requests / metrics.total_requests
                if error_rate > 0.1:
                    return HealthCheckResult(
                        status=HealthStatus.WARNING,
                        message="错误率过高",
                        details={"metrics": metrics.__dict__, "error_rate": error_rate},
                        response_time=time.time() - start_time,
                        timestamp=datetime.now()
                    )
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="性能指标正常",
                details={"metrics": metrics.__dict__},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.WARNING,
                message=f"性能检查失败: {e}",
                details={"error": str(e)},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    async def _check_memory(self) -> HealthCheckResult:
        """检查内存使用"""
        start_time = time.time()
        
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # 检查内存使用
            if memory_mb > 1000:  # 超过1GB
                return HealthCheckResult(
                    status=HealthStatus.WARNING,
                    message="内存使用过高",
                    details={"memory_mb": memory_mb},
                    response_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="内存使用正常",
                details={"memory_mb": memory_mb},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.WARNING,
                message=f"内存检查失败: {e}",
                details={"error": str(e)},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    async def _check_disk_space(self) -> HealthCheckResult:
        """检查磁盘空间"""
        start_time = time.time()
        
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024 ** 3)
            
            # 检查可用空间
            if free_gb < 1:  # 少于1GB
                return HealthCheckResult(
                    status=HealthStatus.WARNING,
                    message="磁盘空间不足",
                    details={"free_gb": free_gb},
                    response_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="磁盘空间充足",
                details={"free_gb": free_gb},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.WARNING,
                message=f"磁盘空间检查失败: {e}",
                details={"error": str(e)},
                response_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """运行所有健康检查"""
        results = {}
        
        for check_name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[check_name] = result
            except Exception as e:
                results[check_name] = HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    message=f"检查失败: {e}",
                    details={"error": str(e)},
                    response_time=0.0,
                    timestamp=datetime.now()
                )
        
        return results
    
    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """获取整体状态"""
        statuses = [result.status for result in results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.HEALTHY


# 创建路由器
router = APIRouter(prefix="/health", tags=["health"])

# 全局健康检查器
_health_checker = HealthChecker()


@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """基础健康检查"""
    start_time = time.time()
    
    try:
        # 运行所有检查
        results = await _health_checker.run_all_checks()
        
        # 获取整体状态
        overall_status = _health_checker.get_overall_status(results)
        
        # 获取性能报告
        performance_report = get_performance_report()
        
        # 获取错误统计
        error_stats = get_error_statistics()
        
        response_time = time.time() - start_time
        
        return HealthCheckResponse(
            status=overall_status.value,
            message=f"系统状态: {overall_status.value}",
            timestamp=datetime.now().isoformat(),
            response_time=response_time,
            checks={
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "response_time": result.response_time,
                    "details": result.details
                }
                for name, result in results.items()
            },
            performance=performance_report,
            errors=error_stats
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {e}")


@router.get("/quick")
async def quick_health_check():
    """快速健康检查"""
    start_time = time.time()
    
    try:
        # 只检查关键组件
        critical_checks = ["database", "performance"]
        results = {}
        
        for check_name in critical_checks:
            if check_name in _health_checker.checks:
                result = await _health_checker.checks[check_name]()
                results[check_name] = result
        
        overall_status = _health_checker.get_overall_status(results)
        response_time = time.time() - start_time
        
        return {
            "status": overall_status.value,
            "message": f"快速检查完成: {overall_status.value}",
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"快速健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"快速健康检查失败: {e}")


@router.get("/detailed")
async def detailed_health_check():
    """详细健康检查"""
    start_time = time.time()
    
    try:
        # 运行所有检查
        results = await _health_checker.run_all_checks()
        
        # 获取整体状态
        overall_status = _health_checker.get_overall_status(results)
        
        # 获取详细性能报告
        performance_report = get_performance_report()
        
        # 获取详细错误统计
        error_stats = get_error_statistics()
        
        # 获取缓存统计
        cache_stats = get_global_cache().get_stats()
        
        # 获取数据库统计
        db_stats = get_global_connection_pool().get_stats()
        
        response_time = time.time() - start_time
        
        return {
            "status": overall_status.value,
            "message": f"详细检查完成: {overall_status.value}",
            "timestamp": datetime.now().isoformat(),
            "response_time": response_time,
            "checks": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "response_time": result.response_time,
                    "details": result.details
                }
                for name, result in results.items()
            },
            "performance": performance_report,
            "errors": error_stats,
            "cache": cache_stats.__dict__ if cache_stats else {},
            "database": db_stats.__dict__
        }
        
    except Exception as e:
        logger.error(f"详细健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"详细健康检查失败: {e}")


@router.get("/metrics")
async def get_metrics():
    """获取性能指标"""
    try:
        performance_report = get_performance_report()
        error_stats = get_error_statistics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "performance": performance_report,
            "errors": error_stats
        }
        
    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取指标失败: {e}")
