# GTPlanner 请求验证系统使用指南

## 📋 目录

1. [快速开始](#快速开始)
2. [基础配置](#基础配置)
3. [验证策略配置](#验证策略配置)
4. [中间件集成](#中间件集成)
5. [监控和调试](#监控和调试)
6. [故障排除](#故障排除)
7. [性能调优](#性能调优)
8. [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 1. 基本集成

最简单的方式是使用预配置的快速设置：

```python
from fastapi import FastAPI
from agent.validation.adapters.fastapi_adapter import setup_fastapi_validation

app = FastAPI()

# 一键设置验证系统
setup_fastapi_validation(app)

@app.post("/api/chat/agent")
async def chat_agent(request: AgentContextRequest):
    # 请求会自动通过验证
    return {"status": "success"}
```

### 2. 检查验证状态

验证系统会自动创建状态端点：

```bash
# 检查验证系统状态
curl http://localhost:8000/api/validation/status

# 获取验证指标
curl http://localhost:8000/api/validation/metrics
```

### 3. 验证结果获取

在路由处理器中获取验证结果：

```python
@app.post("/api/chat/agent")
async def chat_agent(request: Request):
    # 获取验证结果
    validation_result = getattr(request.state, 'validation_result', None)
    validation_context = getattr(request.state, 'validation_context', None)
    
    if validation_result:
        print(f"验证状态: {validation_result.status.value}")
        print(f"执行时间: {validation_result.execution_time:.3f}s")
    
    return {"message": "处理成功"}
```

---

## ⚙️ 基础配置

### 1. settings.toml 配置

在 `settings.toml` 中添加验证配置：

```toml
[default.validation]
# 基本配置
enabled = true
mode = "strict"  # strict, lenient, fail_fast, continue
max_request_size = 1048576  # 1MB
max_message_length = 10000

# 功能开关
enable_rate_limiting = true
enable_caching = true
enable_metrics = true
enable_parallel_validation = true

# 路径配置
excluded_paths = ["/health", "/metrics", "/static"]
included_paths = ["/api"]
```

### 2. 环境变量配置

支持通过环境变量覆盖配置：

```bash
# 基本配置
export GTPLANNER_VALIDATION_ENABLED=true
export GTPLANNER_VALIDATION_MODE=strict
export GTPLANNER_VALIDATION_MAX_REQUEST_SIZE=2097152

# 频率限制
export GTPLANNER_VALIDATION_REQUESTS_PER_MINUTE=100
export GTPLANNER_VALIDATION_ENABLE_RATE_LIMITING=true
```

### 3. 程序化配置

```python
from agent.validation.factories.config_factory import ConfigFactory

# 创建自定义配置
config_factory = ConfigFactory()
custom_config = config_factory.create_from_template("standard", {
    "max_request_size": 2097152,  # 2MB
    "mode": "lenient",
    "validators": [
        {
            "name": "security",
            "type": "security",
            "enabled": True,
            "config": {
                "enable_xss_protection": True,
                "enable_sql_injection_detection": True
            }
        }
    ]
})

# 验证配置
validation_result = config_factory.validate_config(custom_config)
if validation_result.is_valid:
    print("配置有效")
else:
    print("配置错误:", validation_result.errors)
```

---

## 🛡️ 验证策略配置

### 1. 安全验证配置

```toml
[[default.validation.validators]]
name = "security"
type = "security"
enabled = true
priority = "critical"

[default.validation.validators.config]
enable_xss_protection = true
enable_sql_injection_detection = true
enable_sensitive_data_detection = false  # 生产环境建议启用
enable_script_detection = true
```

**安全级别建议:**
- **开发环境**: 启用XSS和SQL注入检测
- **测试环境**: 启用所有安全检测
- **生产环境**: 启用所有安全检测 + 敏感信息检测

### 2. 大小限制配置

```toml
[[default.validation.validators]]
name = "size"
type = "size"
enabled = true
priority = "high"

[default.validation.validators.config]
max_request_size = 1048576        # 1MB - 根据业务需求调整
max_content_length = 1048576      # 1MB
max_json_depth = 10               # JSON嵌套深度
max_array_length = 1000           # 数组最大长度
max_string_length = 10000         # 字符串最大长度
max_dialogue_history_length = 50  # 对话历史长度
```

**大小限制建议:**
- **聊天API**: `max_message_length: 10000`, `max_dialogue_history_length: 50`
- **文件上传**: `max_request_size: 10485760` (10MB)
- **批量API**: `max_array_length: 1000`

### 3. 频率限制配置

```toml
[[default.validation.validators]]
name = "rate_limit"
type = "rate_limit"
enabled = true
priority = "high"

[default.validation.validators.config]
requests_per_minute = 60          # 每分钟请求限制
requests_per_hour = 1000          # 每小时请求限制
burst_size = 10                   # 突发请求大小
enable_ip_based_limiting = true   # IP级别限制
enable_user_based_limiting = true # 用户级别限制
```

**频率限制建议:**
- **免费用户**: `requests_per_minute: 30`
- **付费用户**: `requests_per_minute: 100`
- **企业用户**: `requests_per_minute: 300`

---

## 🔗 中间件集成

### 1. 手动中间件配置

```python
from fastapi import FastAPI
from agent.validation.middleware.validation_middleware import ValidationMiddleware
from agent.validation.middleware.error_middleware import ErrorHandlingMiddleware
from agent.validation.observers.logging_observer import LoggingObserver
from agent.validation.observers.metrics_observer import MetricsObserver

app = FastAPI()

# 创建验证配置
validation_config = {
    "enabled": True,
    "mode": "strict",
    "endpoints": {
        "/api/chat/agent": ["security", "rate_limit", "size", "format", "content"]
    }
}

# 添加错误处理中间件（先添加，后执行）
app.add_middleware(ErrorHandlingMiddleware, config={
    "include_error_details": True,
    "mask_sensitive_data": True
})

# 添加验证中间件
validation_middleware = ValidationMiddleware(app, validation_config)

# 添加观察者
validation_middleware.add_observer(LoggingObserver({"enabled": True}))
validation_middleware.add_observer(MetricsObserver({"enabled": True}))

app.add_middleware(type(validation_middleware), instance=validation_middleware)
```

### 2. 中间件执行顺序

**推荐的中间件顺序（从外到内）:**

1. **CORS中间件** - 处理跨域请求
2. **ErrorHandlingMiddleware** - 错误处理中间件
3. **ValidationMiddleware** - 验证中间件
4. **其他业务中间件**
5. **路由处理器**

```python
# 正确的添加顺序
app.add_middleware(CORSMiddleware, ...)           # 最外层
app.add_middleware(ErrorHandlingMiddleware, ...)  # 错误处理
app.add_middleware(ValidationMiddleware, ...)     # 验证处理
```

### 3. 流式验证集成

```python
from agent.validation.observers.streaming_observer import StreamingObserver

@app.post("/api/chat/agent")
async def chat_agent_stream(request: Request):
    # 获取流式会话
    streaming_session = getattr(request.state, 'streaming_session', None)
    
    if streaming_session:
        # 创建流式验证观察者
        streaming_observer = StreamingObserver(streaming_session)
        
        # 如果有验证中间件，添加观察者
        if hasattr(request.state, 'validation_middleware'):
            request.state.validation_middleware.add_observer(streaming_observer)
    
    # 处理流式响应
    return StreamingResponse(...)
```

---

## 📊 监控和调试

### 1. 启用详细日志

```toml
[default.validation.logging]
enabled = true
level = "DEBUG"
include_request_details = true
include_validation_path = true
include_performance_metrics = true
log_successful_validations = true  # 开发环境启用
log_failed_validations = true
```

### 2. 指标监控

```python
from agent.validation.observers.metrics_observer import MetricsObserver

# 创建指标观察者
metrics_observer = MetricsObserver({
    "enabled": True,
    "include_timing": True,
    "include_success_rate": True,
    "export_interval": 60
})

# 获取实时指标
metrics = metrics_observer.get_current_metrics()
print(f"验证成功率: {metrics['overall_success_rate']:.1%}")
print(f"平均执行时间: {metrics['average_execution_time']:.3f}s")

# 获取验证器性能
for validator_name in metrics['validator_avg_times']:
    performance = metrics_observer.get_validator_performance(validator_name)
    print(f"{validator_name}: {performance['avg_execution_time']:.3f}s")
```

### 3. 增强监控

```python
from agent.validation.observers.enhanced_metrics_observer import EnhancedMetricsObserver

# 创建增强指标观察者
enhanced_observer = EnhancedMetricsObserver({
    "enable_alerts": True,
    "enable_trend_analysis": True,
    "alerts": {
        "success_rate_threshold": 0.95,
        "execution_time_threshold": 0.1
    }
})

# 获取监控面板数据
dashboard_data = enhanced_observer.export_metrics_dashboard_data()

# 生成性能报告
report = enhanced_observer.export_performance_report()
print(report)
```

---

## 🔍 故障排除

### 常见问题和解决方案

#### 1. 验证失败但不知道原因

**问题**: API请求被拒绝，但错误信息不够详细

**解决方案**:
```python
# 1. 检查验证结果
@app.post("/api/test")
async def test_endpoint(request: Request):
    validation_result = getattr(request.state, 'validation_result', None)
    if validation_result and not validation_result.is_valid:
        for error in validation_result.errors:
            print(f"错误: {error.code} - {error.message}")
            if error.suggestion:
                print(f"建议: {error.suggestion}")

# 2. 启用详细日志
config = {
    "logging": {
        "level": "DEBUG",
        "include_request_details": True,
        "log_failed_validations": True
    }
}

# 3. 查看验证路径
validation_context = getattr(request.state, 'validation_context', None)
if validation_context:
    print(f"验证路径: {validation_context.validation_path}")
```

#### 2. 性能问题

**问题**: 验证执行时间过长

**解决方案**:
```python
# 1. 启用并行验证
config = {
    "enable_parallel_validation": True,
    "enable_caching": True
}

# 2. 使用性能优化器
from agent.validation.utils.performance_optimizer import get_global_optimizer

optimizer = get_global_optimizer()
await optimizer.prewarm_common_validators(validator_factory.create_validator)

# 3. 检查缓存命中率
metrics = metrics_observer.get_current_metrics()
cache_rates = metrics.get("validator_cache_rates", {})
for validator, rate in cache_rates.items():
    if rate < 0.5:
        print(f"警告: {validator} 缓存命中率过低: {rate:.1%}")
```

#### 3. 内存使用过高

**问题**: 验证系统占用内存过多

**解决方案**:
```python
# 1. 调整缓存大小
cache_config = {
    "max_size": 500,  # 减少缓存大小
    "cleanup_interval": 30,  # 增加清理频率
    "use_partitioned_cache": True
}

# 2. 限制并发验证
concurrency_config = {
    "max_concurrent_validations": 50,  # 减少并发数
    "max_concurrent_per_validator": 5
}

# 3. 定期清理缓存
cache_manager = ValidationCacheManager(cache_config)
await cache_manager.clear()  # 手动清理
```

#### 4. 频率限制误报

**问题**: 正常用户被频率限制误杀

**解决方案**:
```python
# 1. 调整频率限制配置
rate_limit_config = {
    "requests_per_minute": 120,  # 增加限制
    "burst_size": 20,           # 增加突发大小
    "enable_user_based_limiting": True  # 启用用户级别限制
}

# 2. 检查IP限制统计
rate_limiter = RateLimitValidationStrategy(rate_limit_config)
stats = rate_limiter.ip_limiter.get_stats("192.168.1.100")
print(f"IP统计: {stats}")

# 3. 白名单配置（自定义实现）
whitelist_ips = ["192.168.1.0/24", "10.0.0.0/8"]
```

#### 5. 验证器执行异常

**问题**: 特定验证器经常执行失败

**解决方案**:
```python
# 1. 检查验证器配置
validator_config = validation_config.get_validator_config("problematic_validator")
if validator_config:
    print(f"验证器配置: {validator_config.config}")

# 2. 临时禁用问题验证器
context.skip_validators.append("problematic_validator")

# 3. 查看验证器错误统计
metrics = metrics_observer.get_current_metrics()
error_validators = metrics.get("error_validators", {})
for validator, count in error_validators.items():
    if count > 10:
        print(f"警告: {validator} 错误次数过多: {count}")
```

---

## 📈 监控和调试

### 1. 实时监控设置

```python
from agent.validation.observers.enhanced_metrics_observer import EnhancedMetricsObserver

# 创建增强监控
monitor_config = {
    "enable_alerts": True,
    "enable_trend_analysis": True,
    "alerts": {
        "success_rate_threshold": 0.95,
        "execution_time_threshold": 0.1,
        "error_rate_threshold": 0.05
    }
}

enhanced_observer = EnhancedMetricsObserver(monitor_config)

# 添加自定义告警处理
def email_alert_handler(alert_type: str, alert_data: Dict[str, Any]):
    # 发送邮件告警
    send_email(
        to="admin@company.com",
        subject=f"验证系统告警: {alert_type}",
        body=f"当前值: {alert_data['current_value']}, 阈值: {alert_data['threshold']}"
    )

enhanced_observer.alert_manager.add_alert_handler(email_alert_handler)
```

### 2. 调试模式配置

开发环境的详细调试配置：

```toml
[default.validation]
mode = "lenient"  # 宽松模式，显示更多信息

[default.validation.logging]
level = "DEBUG"
include_request_details = true
include_validation_path = true
include_performance_metrics = true
log_successful_validations = true

[default.validation.error_handling]
include_suggestions = true
include_error_codes = true
include_field_details = true
mask_sensitive_data = false  # 开发环境可以显示详细信息
```

### 3. 性能分析

```python
# 获取详细性能分析
metrics = enhanced_observer.get_enhanced_metrics()

# 验证器性能分析
for validator_name, avg_time in metrics["validator_avg_times"].items():
    if avg_time > 0.05:  # 超过50ms
        print(f"⚠️ {validator_name} 执行时间过长: {avg_time:.3f}s")
        
        # 获取详细性能数据
        performance = enhanced_observer.get_validator_performance(validator_name)
        print(f"   成功率: {performance['success_rate']:.1%}")
        print(f"   缓存命中率: {performance['cache_hit_rate']:.1%}")

# 趋势分析
trends = metrics.get("trends", {})
for metric_name, trend in trends.items():
    if trend["trend_direction"] == "上升" and "time" in metric_name:
        print(f"⚠️ {metric_name} 呈上升趋势: {trend['current_value']:.3f}")
```

---

## ⚡ 性能调优

### 1. 缓存优化

```python
# 高性能缓存配置
cache_config = {
    "enabled": True,
    "backend": "memory",
    "max_size": 2000,           # 增加缓存大小
    "default_ttl": 600,         # 增加TTL
    "use_partitioned_cache": True,
    "partition_count": 32,      # 增加分区数
    "cleanup_interval": 30      # 频繁清理
}

# 验证器级别的缓存配置
validator_configs = {
    "security": {"enable_cache": True, "cache_ttl": 300},
    "size": {"enable_cache": True, "cache_ttl": 600},
    "format": {"enable_cache": True, "cache_ttl": 900}
}
```

### 2. 并发优化

```python
# 高并发配置
concurrency_config = {
    "enable_parallel_validation": True,
    "max_concurrent_validations": 200,
    "max_concurrent_per_validator": 20
}

# 使用性能优化器
from agent.validation.utils.performance_optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer({
    "max_concurrent_validations": 200,
    "max_prewarmed_validators": 100,
    "max_batch_size": 20
})

# 应用生产环境优化
optimizer.optimize_for_production()
```

### 3. 验证链优化

```python
# 优化验证链配置
optimized_endpoints = {
    # 高频端点 - 最小验证集
    "/api/chat/agent": ["security", "size", "format"],
    
    # 管理端点 - 完整验证
    "/api/admin/*": ["security", "rate_limit", "size", "format", "content", "session"],
    
    # 健康检查 - 仅大小检查
    "/health": ["size"]
}

# 使用快速失败模式
fast_config = {
    "mode": "fail_fast",  # 遇到错误立即停止
    "enable_parallel_validation": False  # 串行执行，更快失败
}
```

---

## 🎯 最佳实践

### 1. 安全最佳实践

```python
# 生产环境安全配置
security_best_practices = {
    "security": {
        "enable_xss_protection": True,
        "enable_sql_injection_detection": True,
        "enable_sensitive_data_detection": True,
        "enable_script_detection": True
    },
    "rate_limit": {
        "requests_per_minute": 60,
        "enable_ip_based_limiting": True,
        "enable_user_based_limiting": True
    },
    "error_handling": {
        "mask_sensitive_data": True,
        "include_stack_trace": False,
        "max_error_message_length": 200
    }
}
```

### 2. 性能最佳实践

```python
# 高性能配置
performance_best_practices = {
    "validation": {
        "enable_parallel_validation": True,
        "enable_caching": True,
        "cache_ttl": 300
    },
    "cache": {
        "use_partitioned_cache": True,
        "partition_count": 16,
        "max_size": 1000
    },
    "optimization": {
        "max_concurrent_validations": 100,
        "max_prewarmed_validators": 50
    }
}
```

### 3. 监控最佳实践

```python
# 完整监控配置
monitoring_best_practices = {
    "metrics": {
        "enabled": True,
        "include_timing": True,
        "include_success_rate": True,
        "export_interval": 60
    },
    "alerts": {
        "success_rate_threshold": 0.95,
        "execution_time_threshold": 0.1,
        "error_rate_threshold": 0.05,
        "cache_hit_rate_threshold": 0.7
    },
    "logging": {
        "level": "INFO",
        "log_failed_validations": True,
        "log_successful_validations": False  # 生产环境关闭
    }
}
```

### 4. 部署最佳实践

```python
# 分环境配置
environments = {
    "development": {
        "mode": "lenient",
        "log_level": "DEBUG",
        "mask_sensitive_data": False,
        "max_concurrent_validations": 10
    },
    "testing": {
        "mode": "strict",
        "log_level": "INFO", 
        "mask_sensitive_data": True,
        "max_concurrent_validations": 50
    },
    "production": {
        "mode": "strict",
        "log_level": "WARNING",
        "mask_sensitive_data": True,
        "max_concurrent_validations": 200,
        "enable_alerts": True
    }
}
```

---

## 🔧 自定义扩展

### 1. 创建自定义验证器

```python
from agent.validation.core.base_validator import BaseValidator
from agent.validation.core.interfaces import ValidatorPriority

class BusinessRuleValidator(BaseValidator):
    """业务规则验证器示例"""
    
    async def _do_validate(self, context: ValidationContext) -> ValidationResult:
        data = context.request_data
        
        # 实现业务规则检查
        if not self._check_business_rules(data):
            error = ValidationError(
                code="BUSINESS_RULE_VIOLATION",
                message="违反业务规则",
                suggestion="请检查业务规则要求"
            )
            return ValidationResult.create_error(error)
        
        return ValidationResult.create_success()
    
    def _check_business_rules(self, data):
        # 具体的业务规则逻辑
        return True
    
    def get_validator_name(self) -> str:
        return "business_rule"
    
    def get_priority(self) -> ValidatorPriority:
        return ValidatorPriority.MEDIUM

# 注册自定义验证器
from agent.validation.core.validation_registry import register_validator
register_validator("business_rule", BusinessRuleValidator)
```

### 2. 创建自定义观察者

```python
from agent.validation.core.interfaces import IValidationObserver

class CustomMetricsObserver(IValidationObserver):
    """自定义指标观察者"""
    
    async def on_validation_start(self, context: ValidationContext) -> None:
        # 记录验证开始
        pass
    
    async def on_validation_complete(self, result: ValidationResult) -> None:
        # 发送到外部监控系统
        send_to_monitoring_system({
            "validation_count": 1,
            "success": result.is_valid,
            "execution_time": result.execution_time
        })
    
    async def on_validation_error(self, error: Exception, context: Optional[ValidationContext] = None) -> None:
        # 发送错误告警
        send_alert(f"验证系统错误: {error}")
    
    def get_observer_name(self) -> str:
        return "custom_metrics"
```

### 3. 创建自定义适配器

```python
from agent.validation.core.interfaces import IValidationStrategy

class DatabaseValidationAdapter(IValidationStrategy):
    """数据库验证适配器示例"""
    
    async def execute(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        # 连接数据库验证
        if await self._check_database_constraints(data):
            return ValidationResult.create_success()
        else:
            error = ValidationError(
                code="DATABASE_CONSTRAINT_VIOLATION",
                message="违反数据库约束",
                suggestion="请检查数据完整性"
            )
            return ValidationResult.create_error(error)
    
    async def _check_database_constraints(self, data):
        # 数据库约束检查逻辑
        return True
    
    def get_strategy_name(self) -> str:
        return "database_adapter"
```

---

## 📊 监控面板集成

### 获取监控数据

```python
from agent.validation.observers.enhanced_metrics_observer import EnhancedMetricsObserver

@app.get("/api/validation/dashboard")
async def get_validation_dashboard():
    """获取验证系统监控面板数据"""
    
    # 获取增强指标观察者实例
    enhanced_observer = get_enhanced_metrics_observer()
    
    # 导出监控面板数据
    dashboard_data = enhanced_observer.export_metrics_dashboard_data()
    
    return {
        "status": "success",
        "data": dashboard_data,
        "timestamp": time.time()
    }
```

### 监控面板数据结构

```json
{
  "overview": {
    "total_validations": 12345,
    "success_rate": 0.987,
    "avg_execution_time": 0.045,
    "uptime_hours": 72.5
  },
  "validators": {
    "performance": {
      "security": 0.023,
      "size": 0.012,
      "format": 0.008
    },
    "success_rates": {
      "security": 0.99,
      "size": 0.98,
      "format": 0.995
    }
  },
  "errors": {
    "top_error_codes": {
      "XSS_DETECTED": 15,
      "SIZE_LIMIT_EXCEEDED": 8,
      "MISSING_REQUIRED_FIELDS": 5
    }
  },
  "trends": {
    "success_rate": {
      "trend_direction": "上升",
      "current_value": 0.987
    }
  }
}
```

---

## 🔄 集成示例

### 完整的FastAPI集成示例

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agent.validation.adapters.fastapi_adapter import setup_fastapi_validation
from agent.validation.observers.enhanced_metrics_observer import EnhancedMetricsObserver

app = FastAPI(title="GTPlanner API with Validation")

# 1. 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 设置验证系统
validation_config = {
    "enabled": True,
    "mode": "strict",
    "enable_parallel_validation": True,
    "endpoints": {
        "/api/chat/agent": ["security", "rate_limit", "size", "format", "content", "session"],
        "/api/tools/*": ["security", "rate_limit", "size", "format"],
        "/health": ["size"]
    }
}

setup_fastapi_validation(app, validation_config)

# 3. 添加验证状态路由
@app.get("/api/validation/health")
async def validation_health():
    """验证系统健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "features": ["security", "rate_limiting", "caching", "metrics"]
    }

# 4. 主要API端点
@app.post("/api/chat/agent")
async def chat_agent(request: Request):
    """聊天代理端点 - 自动验证"""
    
    # 获取验证结果
    validation_result = getattr(request.state, 'validation_result', None)
    if validation_result:
        print(f"验证状态: {validation_result.status.value}")
    
    # 处理业务逻辑
    return {"message": "验证通过，处理成功"}

# 5. 启动时预热
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    from agent.validation.utils.performance_optimizer import get_global_optimizer
    
    optimizer = get_global_optimizer()
    # 预热常用验证器
    # await optimizer.prewarm_common_validators(validator_factory)
    
    print("✅ GTPlanner验证系统启动完成")
```

---

## 📝 配置模板

### 开发环境配置

```toml
[default.validation]
enabled = true
mode = "lenient"
enable_parallel_validation = false  # 便于调试
enable_caching = false              # 避免缓存影响调试

[default.validation.logging]
level = "DEBUG"
log_successful_validations = true
include_request_details = true

[default.validation.error_handling]
mask_sensitive_data = false
include_suggestions = true
```

### 生产环境配置

```toml
[default.validation]
enabled = true
mode = "strict"
enable_parallel_validation = true
enable_caching = true
enable_metrics = true

[default.validation.logging]
level = "WARNING"
log_successful_validations = false
log_failed_validations = true

[default.validation.error_handling]
mask_sensitive_data = true
include_stack_trace = false
max_error_message_length = 200
```

---

## 🆘 紧急故障处理

### 1. 紧急禁用验证

```python
# 环境变量紧急禁用
export GTPLANNER_VALIDATION_ENABLED=false

# 或者在代码中
validation_middleware.enabled = False
```

### 2. 紧急降级配置

```toml
[default.validation]
mode = "lenient"  # 改为宽松模式
enable_rate_limiting = false  # 临时禁用频率限制

# 只保留最基本的验证
[default.validation.endpoints]
"/api/*" = ["size"]  # 只检查大小
```

### 3. 快速诊断命令

```python
# 检查验证系统状态
from agent.validation.factories.config_factory import ConfigFactory
from agent.validation.core.validation_registry import get_global_registry

config_factory = ConfigFactory()
registry = get_global_registry()

# 诊断配置
config = config_factory.create_from_template("standard")
validation_result = config_factory.validate_config(config)
print("配置状态:", validation_result.get_summary())

# 诊断注册表
registry_issues = registry.validate_registry()
print("注册表问题:", registry_issues)

# 诊断性能
from agent.validation.utils.performance_optimizer import get_global_optimizer
optimizer = get_global_optimizer()
stats = optimizer.get_optimization_stats()
print("性能统计:", stats)
```

---

*本指南版本: 1.0.0*  
*最后更新: 2025年9月*  
*如有问题，请查看故障排除部分或联系GTPlanner团队*
