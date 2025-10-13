# 日志和错误处理系统文档

## 概览

GTPlanner 使用增强的日志和错误处理系统，提供：

- ✅ 结构化日志（支持 JSON 格式）
- ✅ 多级别日志输出（控制台、文件、JSON 文件）
- ✅ 日志轮转（按大小或时间）
- ✅ 彩色控制台输出
- ✅ 统一的自定义异常类
- ✅ 统一的错误响应格式
- ✅ Sentry 集成（可选）
- ✅ 请求追踪（Request ID）

## 快速开始

### 1. 基础日志记录

```python
from utils.enhanced_logger import get_logger

logger = get_logger(__name__)

logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 2. 使用自定义异常

```python
from utils.custom_exceptions import ValidationError, SessionNotFoundError

# 验证错误
if not user_input:
    raise ValidationError(
        message="User input is required",
        field="user_input"
    )

# Session 不存在
if not session_exists:
    raise SessionNotFoundError(session_id="sess123")
```

### 3. 异常处理

```python
from utils.custom_exceptions import LLMAPIError

try:
    result = await call_llm_api()
except Exception as e:
    raise LLMAPIError(
        message="LLM API调用失败",
        provider="OpenAI",
        original_exception=e
    )
```

## 配置

### 环境变量

```bash
# 日志配置
LOG_LEVEL=INFO                  # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_CONSOLE=true                # 是否输出到控制台
LOG_FILE=true                   # 是否输出到文件
LOG_JSON=false                  # 是否使用JSON格式
LOG_STRUCTURED=false            # 是否使用structlog（需要安装）
LOG_DIR=logs                    # 日志目录
LOG_MAX_SIZE=10485760          # 日志文件最大大小（字节，默认10MB）
LOG_BACKUP_COUNT=5             # 保留的备份文件数
LOG_ROTATION=size              # 轮转方式: size 或 time

# Sentry配置（可选）
SENTRY_DSN=https://xxx@sentry.io/xxx
ENV=development                # 环境: development, staging, production
APP_VERSION=1.0.0             # 应用版本

# CORS配置
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 代码配置

```python
from utils.enhanced_logger import setup_global_logger

setup_global_logger(
    app_name="gtplanner",
    log_level="INFO",
    enable_console=True,
    enable_file=True,
    enable_json=False,
    max_file_size=10 * 1024 * 1024,  # 10MB
    backup_count=5,
    enable_rotation="size"  # "size" 或 "time"
)
```

## 日志系统

### 日志级别

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 详细的调试信息 | 变量值、函数调用 |
| INFO | 一般信息 | 请求开始、处理完成 |
| WARNING | 警告信息 | 配置缺失、性能问题 |
| ERROR | 错误信息 | API调用失败、数据错误 |
| CRITICAL | 严重错误 | 系统崩溃、数据损坏 |

### 日志输出目标

1. **控制台输出**（开发环境推荐）
   - 彩色输出，易于阅读
   - 实时查看日志

2. **文件输出**（生产环境推荐）
   - `logs/gtplanner.log` - 所有日志
   - `logs/gtplanner_error.log` - 仅错误日志
   - `logs/gtplanner_json.log` - JSON格式日志

3. **JSON 格式**（日志分析系统）
   - 结构化数据，便于解析
   - 适合 ELK、Splunk 等系统

### 上下文日志

```python
from utils.enhanced_logger import get_logger

# 带上下文的日志记录器
logger = get_logger(
    __name__,
    session_id="sess123",
    user_id="user456",
    request_id="req789"
)

logger.info("处理请求")  # 自动包含 session_id, user_id, request_id
```

### 日志轮转

**按大小轮转**（默认）：
```python
enable_rotation="size"
max_file_size=10 * 1024 * 1024  # 10MB
backup_count=5  # 保留5个备份
```

**按时间轮转**：
```python
enable_rotation="time"  # 每天轮转
backup_count=30  # 保留30天
```

## 错误处理系统

### 自定义异常类

#### 验证错误

```python
from utils.custom_exceptions import ValidationError, InvalidRequestError

# 字段验证错误
raise ValidationError(
    message="无效的输入格式",
    field="user_input",
    details={"expected": "string", "got": "None"}
)

# 请求验证错误
raise InvalidRequestError(
    message="缺少必需参数",
    details={"missing_fields": ["session_id", "user_input"]}
)
```

#### 认证/授权错误

```python
from utils.custom_exceptions import (
    UnauthorizedError,
    InvalidAPIKeyError,
    RateLimitExceededError
)

# 未授权
raise UnauthorizedError()

# 无效API Key
raise InvalidAPIKeyError()

# 速率限制
raise RateLimitExceededError(
    retry_after=60,  # 60秒后重试
    details={"limit": 10, "window": "1 minute"}
)
```

#### Session错误

```python
from utils.custom_exceptions import (
    SessionNotFoundError,
    SessionExpiredError,
    InvalidSessionStateError
)

# Session不存在
raise SessionNotFoundError(session_id="sess123")

# Session过期
raise SessionExpiredError(session_id="sess123")

# 无效Session状态
raise InvalidSessionStateError(
    message="Session已被锁定",
    session_id="sess123"
)
```

#### LLM错误

```python
from utils.custom_exceptions import (
    LLMAPIError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMTokenLimitExceededError
)

# LLM API错误
raise LLMAPIError(
    message="API调用失败",
    provider="OpenAI",
    details={"model": "gpt-4", "error": "connection_error"}
)

# LLM超时
raise LLMTimeoutError(timeout=30.0)

# Token限制
raise LLMTokenLimitExceededError(
    token_count=5000,
    max_tokens=4096
)
```

#### 工具错误

```python
from utils.custom_exceptions import (
    ToolExecutionError,
    ToolNotFoundError,
    ToolTimeoutError
)

# 工具执行错误
raise ToolExecutionError(
    tool_name="search",
    message="搜索失败",
    details={"query": "test", "error": "network_error"}
)

# 工具不存在
raise ToolNotFoundError(tool_name="unknown_tool")

# 工具超时
raise ToolTimeoutError(tool_name="search", timeout=10.0)
```

### 错误响应格式

所有错误都会返回统一的 JSON 格式：

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "User input is required",
    "timestamp": "2025-01-13T10:30:00.000Z",
    "details": {
      "field": "user_input"
    },
    "request_id": "req123",
    "path": "/api/chat/agent"
  }
}
```

### 错误码列表

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 验证错误 |
| `INVALID_REQUEST` | 400 | 无效请求 |
| `UNAUTHORIZED` | 401 | 未授权 |
| `FORBIDDEN` | 403 | 禁止访问 |
| `RESOURCE_NOT_FOUND` | 404 | 资源不存在 |
| `SESSION_NOT_FOUND` | 404 | Session不存在 |
| `SESSION_EXPIRED` | 410 | Session过期 |
| `RATE_LIMIT_EXCEEDED` | 429 | 速率限制 |
| `INTERNAL_SERVER_ERROR` | 500 | 内部错误 |
| `LLM_API_ERROR` | 502 | LLM API错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |
| `LLM_TIMEOUT` | 504 | LLM超时 |

## Sentry 集成

### 安装

```bash
pip install sentry-sdk
```

### 配置

```bash
# 设置环境变量
export SENTRY_DSN="https://xxx@sentry.io/xxx"
export ENV="production"
export APP_VERSION="1.0.0"
```

### 使用

```python
from utils.sentry_integration import (
    SentryContext,
    capture_exception,
    set_user,
    add_breadcrumb
)

# 设置用户信息
set_user(
    user_id="user123",
    username="john_doe",
    email="john@example.com"
)

# 添加面包屑
add_breadcrumb(
    message="用户开始会话",
    category="user_action",
    data={"session_id": "sess123"}
)

# 使用上下文管理器
with SentryContext(
    transaction_name="process_request",
    operation="planning",
    tags={"language": "zh"},
    context={"session": {"id": "sess123"}}
):
    # 业务逻辑
    process_request()

# 手动捕获异常
try:
    dangerous_operation()
except Exception as e:
    capture_exception(
        e,
        context={"operation": "dangerous_operation"},
        tags={"severity": "high"}
    )
```

## 最佳实践

### 1. 日志记录

✅ **推荐做法**：

```python
# 使用适当的日志级别
logger.debug(f"变量值: {value}")  # 调试信息
logger.info(f"处理完成: {result}")  # 一般信息
logger.warning(f"配置缺失，使用默认值")  # 警告
logger.error(f"API调用失败: {error}")  # 错误
logger.critical(f"系统崩溃: {error}")  # 严重错误

# 使用extra添加结构化数据
logger.info(
    "请求处理完成",
    extra={
        "session_id": session_id,
        "processing_time": 1.5,
        "status": "success"
    }
)

# 记录异常堆栈
logger.error("处理失败", exc_info=True)
```

❌ **避免做法**：

```python
# 不要在INFO级别记录太多细节
logger.info(f"详细数据: {huge_data_structure}")

# 不要使用字符串拼接
logger.info("User " + user_id + " started session")  # 应该用f-string

# 不要忽略异常
except Exception:
    pass  # 至少要记录日志
```

### 2. 异常处理

✅ **推荐做法**：

```python
# 使用具体的异常类型
try:
    result = await process()
except LLMAPIError as e:
    logger.error(f"LLM错误: {e.message}")
    # 处理LLM特定错误
except ToolExecutionError as e:
    logger.error(f"工具错误: {e.message}")
    # 处理工具特定错误

# 保留原始异常
try:
    result = external_api_call()
except Exception as e:
    raise LLMAPIError(
        message="API调用失败",
        original_exception=e  # 保留原始异常
    )

# 提供详细的错误信息
raise ValidationError(
    message="用户输入过短",
    field="user_input",
    details={
        "min_length": 10,
        "actual_length": len(user_input)
    }
)
```

❌ **避免做法**：

```python
# 不要吞掉异常
except Exception:
    pass

# 不要使用通用Exception
raise Exception("Something went wrong")  # 应该用具体异常

# 不要丢失异常上下文
except Exception as e:
    raise ValueError("New error")  # 应该保留原始异常
```

### 3. 生产环境配置

```bash
# 生产环境推荐配置
LOG_LEVEL=INFO  # 或WARNING
LOG_CONSOLE=false  # 关闭控制台输出
LOG_FILE=true
LOG_JSON=true  # 使用JSON格式
LOG_ROTATION=time  # 按天轮转
SENTRY_DSN=https://xxx  # 启用Sentry
ENV=production
```

## 故障排查

### 问题：日志文件过大

**解决方案**：
```bash
# 减小文件大小限制
LOG_MAX_SIZE=5242880  # 5MB

# 减少备份数量
LOG_BACKUP_COUNT=3

# 使用时间轮转
LOG_ROTATION=time
```

### 问题：日志太多

**解决方案**：
```bash
# 提高日志级别
LOG_LEVEL=WARNING  # 只记录警告和错误

# 关闭某些模块的日志
# 在代码中：
logging.getLogger("uvicorn").setLevel(logging.WARNING)
```

### 问题：找不到日志文件

**检查**：
```bash
# 检查日志目录
ls -la logs/

# 检查权限
chmod 755 logs/

# 检查配置
echo $LOG_DIR
```

## 示例代码

完整示例请查看：`utils/logging_examples.py`

## 相关文档

- [API规范文档](api-specification.md)
- [系统架构文档](system-architecture.md)
- [多语言支持文档](multilingual-guide.md)

