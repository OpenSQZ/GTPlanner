"""
增强指标观察者

基于观察者模式的增强指标收集，提供：
- 实时性能指标收集
- 验证器成功率统计
- 错误类型分布分析
- 缓存命中率监控
- 指标数据导出（JSON/CSV）
- 告警阈值监控
"""

import time
import json
import csv
from io import StringIO
from typing import Dict, Any, Optional, List, Callable
from collections import defaultdict, deque
from threading import Lock
from .metrics_observer import MetricsObserver, ValidationMetricsCollector
from ..core.interfaces import IValidationObserver
from ..core.validation_context import ValidationContext
from ..core.validation_result import ValidationResult, ValidationStatus


class AlertManager:
    """告警管理器 - 监控指标阈值并触发告警"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.alert_handlers: List[Callable[[str, Dict[str, Any]], None]] = []
        self.alert_thresholds = self._load_alert_thresholds()
        self.alert_history: deque = deque(maxlen=100)  # 保留最近100个告警
        self._lock = Lock()
    
    def _load_alert_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """加载告警阈值配置
        
        Returns:
            告警阈值配置字典
        """
        return {
            "success_rate": {
                "threshold": self.config.get("success_rate_threshold", 0.95),
                "enabled": self.config.get("enable_success_rate_alert", True),
                "message": "验证成功率过低"
            },
            "avg_execution_time": {
                "threshold": self.config.get("execution_time_threshold", 0.1),
                "enabled": self.config.get("enable_execution_time_alert", True),
                "message": "验证执行时间过长"
            },
            "error_rate": {
                "threshold": self.config.get("error_rate_threshold", 0.1),
                "enabled": self.config.get("enable_error_rate_alert", True),
                "message": "错误率过高"
            },
            "cache_hit_rate": {
                "threshold": self.config.get("cache_hit_rate_threshold", 0.7),
                "enabled": self.config.get("enable_cache_hit_rate_alert", True),
                "message": "缓存命中率过低"
            }
        }
    
    def add_alert_handler(self, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """添加告警处理器
        
        Args:
            handler: 告警处理函数
        """
        self.alert_handlers.append(handler)
    
    def check_metrics(self, metrics: Dict[str, Any]) -> None:
        """检查指标并触发告警
        
        Args:
            metrics: 指标数据
        """
        current_time = time.time()
        
        # 检查成功率
        if self.alert_thresholds["success_rate"]["enabled"]:
            success_rate = metrics.get("overall_success_rate", 1.0)
            threshold = self.alert_thresholds["success_rate"]["threshold"]
            
            if success_rate < threshold:
                self._trigger_alert("success_rate", {
                    "current_value": success_rate,
                    "threshold": threshold,
                    "message": self.alert_thresholds["success_rate"]["message"]
                })
        
        # 检查执行时间
        if self.alert_thresholds["avg_execution_time"]["enabled"]:
            avg_time = metrics.get("average_execution_time", 0.0)
            threshold = self.alert_thresholds["avg_execution_time"]["threshold"]
            
            if avg_time > threshold:
                self._trigger_alert("avg_execution_time", {
                    "current_value": avg_time,
                    "threshold": threshold,
                    "message": self.alert_thresholds["avg_execution_time"]["message"]
                })
        
        # 检查错误率
        if self.alert_thresholds["error_rate"]["enabled"]:
            total_validations = metrics.get("total_validations", 0)
            failed_validations = metrics.get("failed_validations", 0)
            error_rate = failed_validations / total_validations if total_validations > 0 else 0
            threshold = self.alert_thresholds["error_rate"]["threshold"]
            
            if error_rate > threshold:
                self._trigger_alert("error_rate", {
                    "current_value": error_rate,
                    "threshold": threshold,
                    "failed_validations": failed_validations,
                    "total_validations": total_validations,
                    "message": self.alert_thresholds["error_rate"]["message"]
                })
    
    def _trigger_alert(self, alert_type: str, alert_data: Dict[str, Any]) -> None:
        """触发告警
        
        Args:
            alert_type: 告警类型
            alert_data: 告警数据
        """
        with self._lock:
            alert_info = {
                "alert_type": alert_type,
                "timestamp": time.time(),
                "data": alert_data
            }
            
            # 记录告警历史
            self.alert_history.append(alert_info)
            
            # 调用告警处理器
            for handler in self.alert_handlers:
                try:
                    handler(alert_type, alert_data)
                except Exception as e:
                    print(f"Warning: Alert handler failed: {e}")
    
    def get_alert_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取告警历史
        
        Args:
            limit: 返回数量限制
            
        Returns:
            告警历史列表
        """
        with self._lock:
            return list(self.alert_history)[-limit:]


class TrendAnalyzer:
    """趋势分析器 - 分析指标趋势和变化"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self._lock = Lock()
    
    def record_metric(self, metric_name: str, value: float, timestamp: Optional[float] = None) -> None:
        """记录指标值
        
        Args:
            metric_name: 指标名称
            value: 指标值
            timestamp: 时间戳，如果为None则使用当前时间
        """
        with self._lock:
            timestamp = timestamp or time.time()
            self.metric_history[metric_name].append((timestamp, value))
    
    def get_trend(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """获取指标趋势
        
        Args:
            metric_name: 指标名称
            
        Returns:
            趋势分析结果，如果数据不足则返回None
        """
        with self._lock:
            history = self.metric_history.get(metric_name)
            if not history or len(history) < 2:
                return None
            
            values = [value for _, value in history]
            timestamps = [ts for ts, _ in history]
            
            # 计算基本统计
            current_value = values[-1]
            previous_value = values[-2] if len(values) > 1 else current_value
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            
            # 计算变化率
            change_rate = (current_value - previous_value) / previous_value if previous_value != 0 else 0
            
            # 计算趋势方向
            if len(values) >= 5:
                recent_avg = sum(values[-5:]) / 5
                older_avg = sum(values[:-5]) / (len(values) - 5) if len(values) > 5 else avg_value
                trend_direction = "上升" if recent_avg > older_avg else "下降" if recent_avg < older_avg else "平稳"
            else:
                trend_direction = "数据不足"
            
            return {
                "metric_name": metric_name,
                "current_value": current_value,
                "previous_value": previous_value,
                "average_value": avg_value,
                "min_value": min_value,
                "max_value": max_value,
                "change_rate": change_rate,
                "trend_direction": trend_direction,
                "data_points": len(values),
                "time_span": timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0
            }
    
    def get_all_trends(self) -> Dict[str, Dict[str, Any]]:
        """获取所有指标的趋势
        
        Returns:
            所有指标趋势的字典
        """
        trends = {}
        for metric_name in self.metric_history.keys():
            trend = self.get_trend(metric_name)
            if trend:
                trends[metric_name] = trend
        return trends


class EnhancedMetricsObserver(MetricsObserver):
    """增强指标观察者 - 扩展基础指标观察者的功能
    
    在基础指标观察者的基础上增加：
    - 告警阈值监控
    - 趋势分析
    - 高级指标导出
    - 自定义指标收集
    - 实时监控面板数据
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 增强功能配置
        self.enable_alerts = self.config.get("enable_alerts", True)
        self.enable_trend_analysis = self.config.get("enable_trend_analysis", True)
        self.enable_custom_metrics = self.config.get("enable_custom_metrics", True)
        
        # 初始化增强组件
        if self.enable_alerts:
            self.alert_manager = AlertManager(self.config.get("alerts", {}))
            self.alert_manager.add_alert_handler(self._default_alert_handler)
        else:
            self.alert_manager = None
        
        if self.enable_trend_analysis:
            self.trend_analyzer = TrendAnalyzer(self.config.get("trend_window_size", 100))
        else:
            self.trend_analyzer = None
        
        # 自定义指标
        self.custom_metrics: Dict[str, Any] = {}
        self._custom_metrics_lock = Lock()
        
        print("EnhancedMetricsObserver initialized with advanced features")
    
    async def on_validation_complete(self, result: ValidationResult) -> None:
        """验证完成事件 - 扩展基础功能
        
        Args:
            result: 最终验证结果
        """
        # 调用父类方法
        await super().on_validation_complete(result)
        
        # 增强功能
        current_metrics = self.get_current_metrics()
        
        # 记录趋势数据
        if self.trend_analyzer:
            self.trend_analyzer.record_metric("success_rate", current_metrics["overall_success_rate"])
            self.trend_analyzer.record_metric("execution_time", result.execution_time)
            self.trend_analyzer.record_metric("validator_count", result.metrics.executed_validators)
        
        # 检查告警阈值
        if self.alert_manager:
            self.alert_manager.check_metrics(current_metrics)
        
        # 记录自定义指标
        if self.enable_custom_metrics:
            await self._record_custom_metrics(result)
    
    async def _record_custom_metrics(self, result: ValidationResult) -> None:
        """记录自定义指标
        
        Args:
            result: 验证结果
        """
        with self._custom_metrics_lock:
            # 记录验证器组合使用情况
            validator_combination = "|".join(sorted(result.execution_order))
            if "validator_combinations" not in self.custom_metrics:
                self.custom_metrics["validator_combinations"] = defaultdict(int)
            self.custom_metrics["validator_combinations"][validator_combination] += 1
            
            # 记录错误组合
            if result.has_errors:
                error_combination = "|".join(sorted([error.code for error in result.errors]))
                if "error_combinations" not in self.custom_metrics:
                    self.custom_metrics["error_combinations"] = defaultdict(int)
                self.custom_metrics["error_combinations"][error_combination] += 1
            
            # 记录时间分布
            time_bucket = self._get_time_bucket(result.execution_time)
            if "execution_time_distribution" not in self.custom_metrics:
                self.custom_metrics["execution_time_distribution"] = defaultdict(int)
            self.custom_metrics["execution_time_distribution"][time_bucket] += 1
    
    def _get_time_bucket(self, execution_time: float) -> str:
        """获取执行时间分桶
        
        Args:
            execution_time: 执行时间
            
        Returns:
            时间分桶字符串
        """
        if execution_time < 0.01:
            return "0-10ms"
        elif execution_time < 0.05:
            return "10-50ms"
        elif execution_time < 0.1:
            return "50-100ms"
        elif execution_time < 0.5:
            return "100-500ms"
        else:
            return "500ms+"
    
    def _default_alert_handler(self, alert_type: str, alert_data: Dict[str, Any]) -> None:
        """默认告警处理器
        
        Args:
            alert_type: 告警类型
            alert_data: 告警数据
        """
        print(f"🚨 验证系统告警 - {alert_type}: {alert_data['message']}")
        print(f"   当前值: {alert_data['current_value']}, 阈值: {alert_data['threshold']}")
    
    def get_enhanced_metrics(self) -> Dict[str, Any]:
        """获取增强指标数据
        
        Returns:
            增强指标数据字典
        """
        # 获取基础指标
        base_metrics = self.get_current_metrics()
        
        # 添加趋势分析
        if self.trend_analyzer:
            base_metrics["trends"] = self.trend_analyzer.get_all_trends()
        
        # 添加告警信息
        if self.alert_manager:
            base_metrics["alerts"] = {
                "recent_alerts": self.alert_manager.get_alert_history(5),
                "alert_thresholds": self.alert_manager.alert_thresholds
            }
        
        # 添加自定义指标
        if self.enable_custom_metrics:
            with self._custom_metrics_lock:
                base_metrics["custom_metrics"] = dict(self.custom_metrics)
        
        return base_metrics
    
    def export_enhanced_metrics_to_json(self, include_trends: bool = True, include_alerts: bool = True) -> str:
        """导出增强指标为JSON
        
        Args:
            include_trends: 是否包含趋势数据
            include_alerts: 是否包含告警数据
            
        Returns:
            JSON格式的指标数据
        """
        metrics = self.get_enhanced_metrics()
        
        if not include_trends and "trends" in metrics:
            del metrics["trends"]
        
        if not include_alerts and "alerts" in metrics:
            del metrics["alerts"]
        
        return json.dumps(metrics, indent=2, ensure_ascii=False)
    
    def export_metrics_dashboard_data(self) -> Dict[str, Any]:
        """导出监控面板数据
        
        Returns:
            适合监控面板的数据格式
        """
        metrics = self.get_enhanced_metrics()
        
        # 构建面板数据
        dashboard_data = {
            "overview": {
                "total_validations": metrics.get("total_validations", 0),
                "success_rate": metrics.get("overall_success_rate", 0),
                "avg_execution_time": metrics.get("average_execution_time", 0),
                "uptime_hours": metrics.get("uptime_seconds", 0) / 3600
            },
            "validators": {
                "performance": metrics.get("validator_avg_times", {}),
                "success_rates": metrics.get("validator_success_rates", {}),
                "cache_rates": metrics.get("validator_cache_rates", {}),
                "execution_counts": metrics.get("validator_execution_counts", {})
            },
            "errors": {
                "top_error_codes": metrics.get("error_codes", {}),
                "error_severities": metrics.get("error_severities", {}),
                "error_validators": metrics.get("error_validators", {})
            },
            "endpoints": metrics.get("endpoint_stats", {}),
            "trends": metrics.get("trends", {}),
            "alerts": metrics.get("alerts", {})
        }
        
        return dashboard_data
    
    def export_performance_report(self) -> str:
        """导出性能报告
        
        Returns:
            性能报告字符串
        """
        metrics = self.get_enhanced_metrics()
        
        report_lines = [
            "GTPlanner 验证系统性能报告",
            "=" * 50,
            "",
            "📊 总体统计:",
            f"  总验证次数: {metrics.get('total_validations', 0):,}",
            f"  成功率: {metrics.get('overall_success_rate', 0):.1%}",
            f"  平均执行时间: {metrics.get('average_execution_time', 0):.3f}s",
            f"  运行时间: {metrics.get('uptime_seconds', 0) / 3600:.1f} 小时",
            ""
        ]
        
        # 验证器性能
        validator_times = metrics.get("validator_avg_times", {})
        if validator_times:
            report_lines.extend([
                "⚡ 验证器性能:",
                *[f"  {name}: {time:.3f}s" for name, time in sorted(validator_times.items(), key=lambda x: x[1], reverse=True)],
                ""
            ])
        
        # 错误统计
        error_codes = metrics.get("error_codes", {})
        if error_codes:
            report_lines.extend([
                "🚨 常见错误:",
                *[f"  {code}: {count} 次" for code, count in sorted(error_codes.items(), key=lambda x: x[1], reverse=True)[:5]],
                ""
            ])
        
        # 趋势信息
        trends = metrics.get("trends", {})
        if trends:
            report_lines.extend([
                "📈 趋势分析:",
                *[f"  {name}: {trend['trend_direction']} (当前: {trend['current_value']:.3f})" 
                  for name, trend in trends.items()],
                ""
            ])
        
        # 告警信息
        alerts = metrics.get("alerts", {})
        recent_alerts = alerts.get("recent_alerts", [])
        if recent_alerts:
            report_lines.extend([
                "🚨 最近告警:",
                *[f"  {alert['alert_type']}: {alert['data']['message']}" for alert in recent_alerts[-3:]],
                ""
            ])
        
        return "\n".join(report_lines)
    
    def get_observer_name(self) -> str:
        """获取观察者名称
        
        Returns:
            观察者名称
        """
        return "enhanced_metrics_observer"


def create_enhanced_metrics_observer(config: Optional[Dict[str, Any]] = None) -> EnhancedMetricsObserver:
    """创建增强指标观察者的便捷函数
    
    Args:
        config: 观察者配置
        
    Returns:
        增强指标观察者实例
    """
    return EnhancedMetricsObserver(config)


def setup_default_alerts(observer: EnhancedMetricsObserver) -> None:
    """设置默认告警配置
    
    Args:
        observer: 增强指标观察者实例
    """
    if not observer.alert_manager:
        return
    
    def console_alert_handler(alert_type: str, alert_data: Dict[str, Any]) -> None:
        """控制台告警处理器"""
        print(f"🚨 [ALERT] {alert_type.upper()}: {alert_data['message']}")
        print(f"   当前值: {alert_data['current_value']}, 阈值: {alert_data['threshold']}")
    
    def log_alert_handler(alert_type: str, alert_data: Dict[str, Any]) -> None:
        """日志告警处理器"""
        try:
            from utils.logger_config import get_logger
            logger = get_logger("validation.alerts")
            logger.warning(f"验证系统告警 - {alert_type}: {alert_data}")
        except ImportError:
            pass
    
    # 添加告警处理器
    observer.alert_manager.add_alert_handler(console_alert_handler)
    observer.alert_manager.add_alert_handler(log_alert_handler)
    
    print("✅ 默认告警处理器已设置")
