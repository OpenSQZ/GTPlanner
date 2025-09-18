# GTPlanner 请求验证系统 API 文档

## 📋 目录

1. [系统概览](#系统概览)
2. [核心接口](#核心接口)
3. [验证策略](#验证策略)
4. [中间件集成](#中间件集成)
5. [观察者系统](#观察者系统)
6. [适配器模式](#适配器模式)
7. [配置管理](#配置管理)
8. [错误代码参考](#错误代码参考)
9. [性能指标](#性能指标)

---

## 🎯 系统概览

GTPlanner请求验证系统是一个基于现代设计模式的企业级验证框架，提供：

- **多层安全防护**: XSS、SQL注入、恶意脚本检测
- **灵活验证策略**: 7种内置验证策略，支持自定义扩展
- **责任链执行**: 串行和并行验证执行模式
- **观察者监控**: 日志、指标、流式三维度监控
- **适配器集成**: 与Pydantic、FastAPI、SSE系统无缝集成
- **企业级特性**: 缓存、告警、趋势分析、性能优化

### 架构特点

- **8种设计模式应用**: 策略、责任链、工厂、观察者、装饰器、适配器、模板方法、建造者
- **SOLID原则遵循**: 单一职责、开闭原则、里氏替换、接口隔离、依赖倒置
- **异步优先**: 支持高并发和流式响应
- **无状态设计**: 支持水平扩展和微服务部署

---

## 🔌 核心接口

### IValidator - 验证器基础接口

```python
from agent.validation.core.interfaces import IValidator, ValidatorPriority

class CustomValidator(IValidator):
    async def validate(self, context: ValidationContext) -> ValidationResult:
        """执行验证逻辑"""
        pass
    
    def get_validator_name(self) -> str:
        """返回验证器名称"""
        return "custom_validator"
    
    def get_priority(self) -> ValidatorPriority:
        """返回验证器优先级"""
        return ValidatorPriority.MEDIUM
    
    def supports_async(self) -> bool:
        """是否支持异步验证"""
        return True
```

### IValidationStrategy - 验证策略接口

```python
from agent.validation.core.interfaces import IValidationStrategy

class CustomValidationStrategy(IValidationStrategy):
    async def execute(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        """执行验证策略"""
        pass
    
    def get_strategy_name(self) -> str:
        """返回策略名称"""
        return "custom_strategy"
```

### IValidationChain - 验证链接口

```python
from agent.validation.chains.async_validation_chain import AsyncValidationChain

# 创建验证链
chain = AsyncValidationChain("my_chain")

# 添加验证器
chain.add_validator(my_validator)

# 执行验证
result = await chain.validate(context)          # 串行执行
result = await chain.validate_parallel(context) # 并行执行
```

---

## 🛡️ 验证策略

### 1. SecurityValidationStrategy - 安全验证

检测XSS攻击、SQL注入、恶意脚本等安全威胁。

```python
from agent.validation.strategies.security_validator import SecurityValidationStrategy

config = {
    "enable_xss_protection": True,
    "enable_sql_injection_detection": True,
    "enable_sensitive_data_detection": True,
    "enable_script_detection": True
}

strategy = SecurityValidationStrategy(config)
result = await strategy.execute(user_input, {})
```

**检测能力:**
- XSS攻击: `<script>`, `javascript:`, `on*=` 事件处理器
- SQL注入: `UNION SELECT`, `'; DROP TABLE`, 逻辑注入
- 恶意脚本: `eval()`, `setTimeout()`, DOM操作
- 敏感信息: 邮箱、信用卡、身份证等

### 2. SizeValidationStrategy - 大小验证

控制请求大小、内容长度、JSON深度等。

```python
from agent.validation.strategies.size_validator import SizeValidationStrategy

config = {
    "max_request_size": 1048576,      # 1MB
    "max_string_length": 10000,       # 10K字符
    "max_json_depth": 10,             # JSON嵌套深度
    "max_array_length": 1000,         # 数组长度
    "max_dialogue_history_length": 50 # 对话历史长度
}

strategy = SizeValidationStrategy(config)
result = await strategy.execute(request_data, {})
```

### 3. FormatValidationStrategy - 格式验证

验证JSON格式、必需字段、数据类型等。

```python
from agent.validation.strategies.format_validator import FormatValidationStrategy

config = {
    "require_json_content_type": True,
    "validate_json_syntax": True,
    "validate_required_fields": True,
    "strict_field_types": True
}

strategy = FormatValidationStrategy(config)
result = await strategy.execute(json_data, {})
```

**验证内容:**
- AgentContext必需字段: `session_id`, `dialogue_history`, `tool_execution_results`, `session_metadata`
- 消息格式: `role`, `content`, `timestamp`
- 字段类型严格检查
- 时间戳ISO 8601格式验证

### 4. ContentValidationStrategy - 内容验证

检查内容质量、垃圾信息、重复内容等。

```python
from agent.validation.strategies.content_validator import ContentValidationStrategy

config = {
    "max_message_length": 10000,
    "enable_spam_detection": True,
    "max_repetition_ratio": 0.8,
    "min_content_length": 1
}

strategy = ContentValidationStrategy(config)
result = await strategy.execute(content_data, {})
```

### 5. LanguageValidationStrategy - 多语言验证

验证语言支持、一致性检查、自动检测。

```python
from agent.validation.strategies.language_validator import LanguageValidationStrategy

config = {
    "supported_languages": ["en", "zh", "es", "fr", "ja"],
    "auto_detect_language": True,
    "validate_language_consistency": True,
    "fallback_to_default": True
}

strategy = LanguageValidationStrategy(config)
result = await strategy.execute(multilingual_data, {})
```

### 6. RateLimitValidationStrategy - 频率限制

基于滑动窗口的多维度频率控制。

```python
from agent.validation.strategies.rate_limit_validator import RateLimitValidationStrategy

config = {
    "requests_per_minute": 60,
    "requests_per_hour": 1000,
    "burst_size": 10,
    "enable_ip_based_limiting": True,
    "enable_user_based_limiting": True
}

strategy = RateLimitValidationStrategy(config)
result = await strategy.execute(data, {
    "client_ip": "192.168.1.100",
    "user_id": "user123"
})
```

### 7. SessionValidationStrategy - 会话验证

验证会话ID格式、有效性、一致性。

```python
from agent.validation.strategies.session_validator import SessionValidationStrategy

config = {
    "validate_session_id_format": True,
    "check_session_expiry": False,
    "require_valid_session": False,
    "max_session_inactivity": 3600
}

strategy = SessionValidationStrategy(config)
result = await strategy.execute(session_data, {})
```

---

## ⚙️ 中间件集成

### ValidationMiddleware - 核心验证中间件

```python
from fastapi import FastAPI
from agent.validation.middleware.validation_middleware import ValidationMiddleware
from agent.validation.factories.config_factory import ConfigFactory

app = FastAPI()

# 创建验证配置
config_factory = ConfigFactory()
validation_config = config_factory.create_from_template("standard")

# 添加验证中间件
app.add_middleware(ValidationMiddleware, config=validation_config)
```

### 中间件配置

```python
middleware_config = {
    "enabled": True,
    "mode": "strict",  # strict, lenient, fail_fast, continue
    "enable_parallel_validation": True,
    "enable_streaming_validation": False,
    "excluded_paths": ["/health", "/metrics", "/static"],
    "included_paths": ["/api"],
    "endpoints": {
        "/api/chat/agent": ["security", "rate_limit", "size", "format", "content", "language", "session"],
        "/api/mcp/*": ["security", "rate_limit", "format", "content"],
        "/health": ["size"]
    }
}
```

---

## 👁️ 观察者系统

### LoggingObserver - 日志观察者

```python
from agent.validation.observers.logging_observer import LoggingObserver

config = {
    "enabled": True,
    "level": "INFO",
    "include_request_details": True,
    "include_validation_path": True,
    "log_successful_validations": False,
    "log_failed_validations": True,
    "mask_sensitive_data": True
}

observer = LoggingObserver(config)
middleware.add_observer(observer)
```

### MetricsObserver - 指标观察者

```python
from agent.validation.observers.metrics_observer import MetricsObserver

config = {
    "enabled": True,
    "include_timing": True,
    "include_success_rate": True,
    "include_error_details": True,
    "export_interval": 60
}

observer = MetricsObserver(config)
middleware.add_observer(observer)

# 获取指标数据
metrics = observer.get_current_metrics()
summary = observer.get_metrics_summary()
```

### StreamingObserver - 流式观察者

```python
from agent.validation.observers.streaming_observer import StreamingObserver

# 在请求处理中动态添加
if hasattr(request.state, 'streaming_session'):
    streaming_observer = StreamingObserver(request.state.streaming_session)
    middleware.add_observer(streaming_observer)
```

---

## 🔌 适配器模式

### PydanticValidationAdapter - Pydantic集成

```python
from agent.validation.adapters.pydantic_adapter import (
    AgentContextPydanticAdapter, validate_with_agent_context
)

# 验证AgentContext数据
adapter = AgentContextPydanticAdapter()
result = await adapter.validate_agent_context(agent_data)

# 便捷函数
result = await validate_with_agent_context(agent_data)
```

### FastAPIValidationAdapter - FastAPI集成

```python
from agent.validation.adapters.fastapi_adapter import (
    FastAPIValidationAdapter, setup_fastapi_validation
)

# 快速设置
setup_fastapi_validation(app, validation_config)

# 手动设置
adapter = FastAPIValidationAdapter(config)
context = await adapter.create_context_from_request(request)
response = adapter.create_http_response(result, context)
```

### SSEValidationAdapter - SSE流式集成

```python
from agent.validation.adapters.sse_adapter import SSEValidationAdapter

adapter = SSEValidationAdapter({
    "enable_progress_updates": True,
    "enable_error_notifications": True,
    "include_detailed_info": False
})

# 创建增强流式会话
enhanced_session = adapter.create_enhanced_streaming_session(base_session)

# 发送验证事件
await adapter.send_validation_start_event(enhanced_session, context)
await adapter.send_validation_progress_event(enhanced_session, "security", result, 3, 0)
```

---

## ⚙️ 配置管理

### settings.toml 配置结构

```toml
[default.validation]
# 全局配置
enabled = true
mode = "strict"
max_request_size = 1048576
enable_parallel_validation = true

# 验证器优先级
[default.validation.priorities]
security = "critical"
format = "high"
content = "medium"

# 端点验证链配置
[default.validation.endpoints]
"/api/chat/agent" = ["security", "rate_limit", "size", "format", "content", "language", "session"]

# 验证器具体配置
[[default.validation.validators]]
name = "security"
type = "security"
enabled = true
priority = "critical"
[default.validation.validators.config]
enable_xss_protection = true
enable_sql_injection_detection = true
```

### 配置工厂使用

```python
from agent.validation.factories.config_factory import ConfigFactory

# 创建配置工厂
factory = ConfigFactory()

# 从模板创建配置
config = factory.create_from_template("standard", {
    "max_request_size": 2097152,  # 覆盖为2MB
    "mode": "lenient"
})

# 验证配置
validation_result = factory.validate_config(config)
if not validation_result.is_valid:
    print("配置错误:", validation_result.errors)
```

---

## 🚨 错误代码参考

### 安全相关错误

| 错误代码 | 描述 | 严重程度 | 建议 |
|---------|------|----------|------|
| `XSS_DETECTED` | 检测到XSS攻击 | CRITICAL | 移除HTML标签和JavaScript代码 |
| `SQL_INJECTION_DETECTED` | 检测到SQL注入 | CRITICAL | 避免使用SQL关键字和特殊字符 |
| `MALICIOUS_SCRIPT_DETECTED` | 检测到恶意脚本 | HIGH | 移除JavaScript函数调用 |
| `SENSITIVE_DATA_DETECTED` | 检测到敏感信息 | HIGH | 避免包含敏感个人信息 |

### 大小相关错误

| 错误代码 | 描述 | 严重程度 | 建议 |
|---------|------|----------|------|
| `SIZE_LIMIT_EXCEEDED` | 请求大小超限 | HIGH | 减少请求数据大小 |
| `STRING_LENGTH_EXCEEDED` | 字符串长度超限 | MEDIUM | 减少文本内容长度 |
| `JSON_DEPTH_EXCEEDED` | JSON嵌套过深 | HIGH | 减少JSON嵌套层级 |
| `ARRAY_LENGTH_EXCEEDED` | 数组长度超限 | HIGH | 减少数组元素数量 |

### 格式相关错误

| 错误代码 | 描述 | 严重程度 | 建议 |
|---------|------|----------|------|
| `MISSING_REQUIRED_FIELDS` | 缺少必需字段 | HIGH | 提供所有必需字段 |
| `INVALID_FORMAT` | 格式无效 | HIGH | 检查字段格式和类型 |
| `INVALID_MESSAGE_ROLE` | 消息角色无效 | MEDIUM | 使用有效的消息角色 |
| `INVALID_TIMESTAMP_FORMAT` | 时间戳格式无效 | MEDIUM | 使用ISO 8601格式 |

### 频率限制错误

| 错误代码 | 描述 | 严重程度 | 建议 |
|---------|------|----------|------|
| `RATE_LIMIT_BURST` | 突发频率超限 | HIGH | 等待10秒后重试 |
| `RATE_LIMIT_MINUTE` | 分钟频率超限 | HIGH | 等待1分钟后重试 |
| `RATE_LIMIT_HOUR` | 小时频率超限 | HIGH | 等待1小时后重试 |

### 会话相关错误

| 错误代码 | 描述 | 严重程度 | 建议 |
|---------|------|----------|------|
| `MISSING_SESSION_ID` | 缺少会话ID | HIGH | 提供有效的会话ID |
| `INVALID_SESSION_ID_FORMAT` | 会话ID格式无效 | MEDIUM | 使用有效的会话ID格式 |
| `SESSION_EXPIRED` | 会话已过期 | MEDIUM | 创建新会话 |

---

## 📊 性能指标

### 指标类型

1. **验证性能指标**
   - 总验证次数
   - 验证成功率
   - 平均执行时间
   - 验证器执行统计

2. **缓存性能指标**
   - 缓存命中率
   - 缓存大小
   - 缓存清理统计

3. **错误统计指标**
   - 错误类型分布
   - 错误严重程度统计
   - 验证器错误统计

4. **端点性能指标**
   - 端点验证统计
   - 端点平均响应时间
   - 端点错误率

### 指标获取

```python
from agent.validation.observers.metrics_observer import MetricsObserver

observer = MetricsObserver({"enabled": True})

# 获取当前指标
metrics = observer.get_current_metrics()

# 获取指标摘要
summary = observer.get_metrics_summary()

# 导出指标
json_export = observer.export_metrics_to_json()
csv_export = observer.export_metrics_to_csv()
```

---

## 🔧 使用示例

### 基本使用

```python
from fastapi import FastAPI
from agent.validation.adapters.fastapi_adapter import setup_fastapi_validation

app = FastAPI()

# 快速设置验证系统
setup_fastapi_validation(app, {
    "mode": "strict",
    "endpoints": {
        "/api/chat/agent": ["security", "size", "format", "content"]
    }
})

@app.post("/api/chat/agent")
async def chat_agent(request: AgentContextRequest):
    # 请求会自动通过验证中间件验证
    # 验证结果可以从 request.state.validation_result 获取
    return {"message": "处理成功"}
```

### 自定义验证器

```python
from agent.validation.core.base_validator import BaseValidator
from agent.validation.core.interfaces import ValidatorPriority

class BusinessRuleValidator(BaseValidator):
    async def _do_validate(self, context: ValidationContext) -> ValidationResult:
        # 实现业务规则验证逻辑
        data = context.request_data
        
        # 示例：检查业务规则
        if isinstance(data, dict) and "business_rule" in data:
            if not self._check_business_rule(data["business_rule"]):
                error = ValidationError(
                    code="BUSINESS_RULE_VIOLATION",
                    message="违反业务规则",
                    suggestion="请检查业务规则配置"
                )
                return ValidationResult.create_error(error)
        
        return ValidationResult.create_success()
    
    def _check_business_rule(self, rule_data):
        # 业务规则检查逻辑
        return True
    
    def get_validator_name(self) -> str:
        return "business_rule"
    
    def get_priority(self) -> ValidatorPriority:
        return ValidatorPriority.MEDIUM

# 注册自定义验证器
from agent.validation.core.validation_registry import register_validator
register_validator("business_rule", BusinessRuleValidator)
```

### 高级配置

```python
from agent.validation.factories.chain_factory import ValidationChainFactory
from agent.validation.chains.chain_builder import ValidationChainBuilder

# 使用链构建器
builder = ValidationChainBuilder("custom_chain")

# 条件添加验证器
builder.when(lambda config: config.get("enable_security", True)).add_validator_by_name(
    "security", validator_factory.create_validator, {"enable_xss_protection": True}
)

# 为特定端点构建
endpoint_chain = builder.for_endpoint("/api/custom").with_security("strict").build()

# 使用工厂创建
factory = ValidationChainFactory(config)
chain = factory.create_chain_for_endpoint("/api/chat/agent")
```

---

## 📈 监控和告警

### 增强指标观察者

```python
from agent.validation.observers.enhanced_metrics_observer import EnhancedMetricsObserver

config = {
    "enable_alerts": True,
    "enable_trend_analysis": True,
    "alerts": {
        "success_rate_threshold": 0.95,
        "execution_time_threshold": 0.1,
        "error_rate_threshold": 0.05
    }
}

observer = EnhancedMetricsObserver(config)

# 获取监控面板数据
dashboard_data = observer.export_metrics_dashboard_data()

# 生成性能报告
performance_report = observer.export_performance_report()
```

### 自定义告警处理

```python
def custom_alert_handler(alert_type: str, alert_data: Dict[str, Any]):
    """自定义告警处理器"""
    if alert_type == "success_rate":
        # 发送邮件、短信或推送通知
        send_notification(f"验证成功率告警: {alert_data['current_value']:.1%}")

observer.alert_manager.add_alert_handler(custom_alert_handler)
```

---

## 🚀 性能优化

### 性能优化器

```python
from agent.validation.utils.performance_optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer({
    "max_concurrent_validations": 100,
    "max_prewarmed_validators": 50,
    "max_batch_size": 10
})

# 优化验证执行
result = await optimizer.optimized_validate(validator, context)

# 批量验证
results = await optimizer.optimized_batch_validate(validator, contexts)

# 预热常用验证器
await optimizer.prewarm_common_validators(validator_factory.create_validator)
```

### 缓存优化

```python
from agent.validation.utils.cache_manager import ValidationCacheManager

cache_manager = ValidationCacheManager({
    "enabled": True,
    "backend": "memory",
    "max_size": 1000,
    "use_partitioned_cache": True,
    "partition_count": 16
})

# 缓存验证结果
await cache_manager.set("cache_key", validation_result, ttl=300)
cached_result = await cache_manager.get("cache_key")
```

---

## 🔍 调试和故障排除

### 启用调试模式

```toml
[default.validation]
mode = "lenient"  # 宽松模式，显示更多警告

[default.validation.logging]
level = "DEBUG"
include_request_details = true
include_validation_path = true
log_successful_validations = true
```

### 获取验证状态

```python
# 访问验证状态端点
GET /api/validation/status

# 获取验证指标
GET /api/validation/metrics
```

### 常见问题排查

1. **验证失败但原因不明**
   - 检查 `request.state.validation_result.errors`
   - 查看验证路径 `request.state.validation_context.validation_path`
   - 启用详细日志记录

2. **性能问题**
   - 检查并行验证是否启用
   - 查看缓存命中率
   - 使用性能优化器

3. **配置问题**
   - 使用 `ConfigFactory.validate_config()` 验证配置
   - 检查验证器依赖关系
   - 查看注册表状态

---

## 🎯 最佳实践

### 1. 安全配置

```python
# 生产环境安全配置
security_config = {
    "enable_xss_protection": True,
    "enable_sql_injection_detection": True,
    "enable_sensitive_data_detection": True,
    "enable_script_detection": True
}

# 严格的大小限制
size_config = {
    "max_request_size": 1048576,  # 1MB
    "max_message_length": 10000,
    "max_dialogue_history_length": 50
}
```

### 2. 性能配置

```python
# 高性能配置
performance_config = {
    "enable_parallel_validation": True,
    "enable_caching": True,
    "cache_ttl": 300,
    "max_concurrent_validations": 200
}
```

### 3. 监控配置

```python
# 完整监控配置
monitoring_config = {
    "enable_metrics": True,
    "enable_alerts": True,
    "enable_trend_analysis": True,
    "success_rate_threshold": 0.95,
    "execution_time_threshold": 0.1
}
```

---

## 📚 API参考

完整的API参考请查看各模块的docstring文档：

- `agent.validation.core.*` - 核心接口和数据结构
- `agent.validation.strategies.*` - 验证策略实现
- `agent.validation.chains.*` - 责任链和构建器
- `agent.validation.factories.*` - 工厂模式实现
- `agent.validation.middleware.*` - FastAPI中间件
- `agent.validation.observers.*` - 观察者模式实现
- `agent.validation.adapters.*` - 适配器模式实现
- `agent.validation.utils.*` - 工具类和辅助函数

---

*本文档版本: 1.0.0*  
*最后更新: 2025年9月*  
*GTPlanner 团队*
