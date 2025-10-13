# 🚀 错误处理和日志系统 - 快速开始

## ⚡ 5分钟上手指南

### 步骤 1: 安装可选依赖（推荐）

```bash
# Sentry 错误追踪（生产环境推荐）
pip install sentry-sdk

# structlog 结构化日志（可选）
pip install structlog

# JSON 日志格式化（可选）
pip install python-json-logger
```

### 步骤 2: 配置环境变量

```bash
# 创建 .env 文件
cat > .env << EOF
# 日志配置
LOG_LEVEL=INFO
LOG_CONSOLE=true
LOG_FILE=true
LOG_JSON=false

# Sentry配置（可选）
# SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
# ENV=development
EOF
```

### 步骤 3: 在代码中使用

#### 3.1 基础日志记录

```python
from utils.enhanced_logger import get_logger

logger = get_logger(__name__)

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("处理开始")
logger.warning("配置缺失，使用默认值")
logger.error("处理失败", exc_info=True)
```

#### 3.2 使用自定义异常

```python
from utils.custom_exceptions import ValidationError, LLMAPIError

# 验证错误
if not user_input:
    raise ValidationError(
        message="用户输入不能为空",
        field="user_input"
    )

# LLM API 错误
try:
    result = await call_llm()
except Exception as e:
    raise LLMAPIError(
        message="LLM调用失败",
        provider="OpenAI",
        original_exception=e
    )
```

#### 3.3 FastAPI 集成

```python
from fastapi import FastAPI
from utils.error_handlers import setup_error_handlers
from utils.enhanced_logger import setup_global_logger

# 设置日志
setup_global_logger(
    app_name="my_app",
    log_level="INFO",
    enable_console=True
)

app = FastAPI()

# 设置错误处理（自动捕获所有异常）
setup_error_handlers(app)

# 现在你的 API 会自动返回统一格式的错误响应
@app.post("/api/process")
async def process(data: dict):
    if not data.get("input"):
        raise ValidationError("输入不能为空", field="input")
    return {"result": "success"}
```

### 步骤 4: 运行测试

```bash
# 运行测试验证功能
pytest tests/test_error_handling.py -v

# 查看日志文件
tail -f logs/gtplanner.log
```

## 📝 常用代码片段

### 1. 带上下文的日志

```python
from utils.enhanced_logger import get_logger

# 创建带上下文的日志记录器
logger = get_logger(
    __name__,
    session_id="sess123",
    user_id="user456"
)

# 所有日志会自动包含 session_id 和 user_id
logger.info("用户操作", extra={"action": "create_plan"})
```

### 2. 异常处理最佳实践

```python
from utils.enhanced_logger import get_logger
from utils.custom_exceptions import (
    ValidationError,
    LLMAPIError,
    ToolExecutionError
)

logger = get_logger(__name__)

async def process_request(user_input: str, session_id: str):
    """完整的错误处理示例"""
    
    try:
        # 1. 验证输入
        if not user_input or len(user_input) < 10:
            raise ValidationError(
                message="输入太短",
                field="user_input",
                details={"min_length": 10}
            )
        
        # 2. 处理业务逻辑
        logger.info(f"开始处理: {session_id}")
        result = await process(user_input)
        
        # 3. 记录成功
        logger.info(f"处理完成: {session_id}")
        return result
        
    except ValidationError as e:
        # 验证错误 - 用户错误
        logger.warning(f"验证失败: {e.message}")
        raise
        
    except LLMAPIError as e:
        # LLM错误 - 系统错误
        logger.error(f"LLM错误: {e.message}", exc_info=True)
        raise
        
    except Exception as e:
        # 未知错误
        logger.critical(f"未知错误: {e}", exc_info=True)
        raise
```

### 3. Sentry 集成

```python
from utils.sentry_integration import (
    SentryContext,
    capture_exception,
    set_user
)

# 设置用户信息
set_user(user_id="user123", username="john")

# 使用上下文管理器
with SentryContext(
    transaction_name="process_planning",
    tags={"language": "zh", "user_type": "premium"}
):
    # 你的业务逻辑
    result = process_planning_request()

# 手动捕获异常
try:
    risky_operation()
except Exception as e:
    capture_exception(
        e,
        context={"operation": "risky"},
        tags={"severity": "high"}
    )
    raise
```

## 🎯 不同场景的配置

### 开发环境

```bash
LOG_LEVEL=DEBUG              # 详细日志
LOG_CONSOLE=true            # 控制台输出
LOG_FILE=false              # 不需要文件
LOG_JSON=false              # 可读格式
ENV=development
```

### 生产环境

```bash
LOG_LEVEL=WARNING           # 只记录警告和错误
LOG_CONSOLE=false           # 关闭控制台
LOG_FILE=true               # 启用文件
LOG_JSON=true               # JSON格式便于分析
LOG_ROTATION=time           # 按天轮转
SENTRY_DSN=https://...      # 启用Sentry
ENV=production
```

### 测试环境

```bash
LOG_LEVEL=INFO
LOG_CONSOLE=true
LOG_FILE=true
LOG_JSON=false
ENV=test
```

## 📊 查看日志

```bash
# 实时查看所有日志
tail -f logs/gtplanner.log

# 只看错误日志
tail -f logs/gtplanner_error.log

# 查看 JSON 日志（需要 jq）
tail -f logs/gtplanner_json.log | jq

# 搜索特定内容
grep "ERROR" logs/gtplanner.log

# 查看最近的100行
tail -n 100 logs/gtplanner.log
```

## 🔍 调试技巧

### 1. 临时提高日志级别

```python
import logging

# 临时设置为 DEBUG 级别
logging.getLogger("your_module").setLevel(logging.DEBUG)
```

### 2. 查看错误统计

```python
from utils.error_handlers import error_tracker

# 获取错误统计
stats = error_tracker.get_stats()
print(stats)
# {'VALIDATION_ERROR': 5, 'LLM_API_ERROR': 2}
```

### 3. 自定义日志格式

```python
from utils.enhanced_logger import LoggerConfig

config = LoggerConfig(
    app_name="custom_app",
    log_level="DEBUG",
    enable_console=True,
    enable_json=True  # 同时输出 JSON 格式
)

logger = config.configure()
```

## ⚠️ 常见问题

### Q: 日志文件太大怎么办？

**A:** 启用日志轮转
```bash
LOG_ROTATION=time        # 按天轮转
LOG_BACKUP_COUNT=7      # 保留7天
```

### Q: 如何只记录错误？

**A:** 提高日志级别
```bash
LOG_LEVEL=ERROR
```

### Q: Sentry 是必需的吗？

**A:** 不是，Sentry 是可选的。如果不设置 `SENTRY_DSN`，系统会自动跳过 Sentry 初始化。

### Q: 如何在不同模块使用不同日志级别？

**A:** 
```python
import logging

# 设置特定模块的日志级别
logging.getLogger("module_name").setLevel(logging.WARNING)
```

## 📚 更多资源

- 📖 [完整文档](docs/logging-and-error-handling.md)
- 💻 [示例代码](utils/logging_examples.py)
- 🧪 [测试用例](tests/test_error_handling.py)
- 📋 [优化总结](ERROR_HANDLING_UPGRADE.md)

## ✅ 检查清单

在部署前确保：

- [ ] 已设置 `LOG_LEVEL` 环境变量
- [ ] 生产环境设置 `ENV=production`
- [ ] 配置了 `ALLOWED_ORIGINS`（CORS安全）
- [ ] （可选）配置了 `SENTRY_DSN`
- [ ] 日志目录有写入权限
- [ ] 运行了测试验证功能

## 🎉 开始使用

现在你已经准备好使用增强的错误处理和日志系统了！

```bash
# 启动应用
python fastapi_main.py

# 或使用 uvicorn
uvicorn fastapi_main:app --host 0.0.0.0 --port 11211
```

访问 http://localhost:11211/docs 查看 API 文档，所有错误都会以统一格式返回！

