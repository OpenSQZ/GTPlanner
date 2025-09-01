# 日志系统升级总结

## 问题描述

原来的日志系统存在以下问题：
1. 只使用 `print()` 输出到控制台，没有文件日志
2. 依赖 `debug_enabled` 配置，默认为 `False`，导致日志不显示
3. 没有日志级别控制和格式化
4. 没有日志轮转功能

## 解决方案

### 1. 创建统一的日志配置系统

**文件**: `utils/logger_config.py`

- 使用 Python 标准 `logging` 库
- 支持文件和控制台输出
- 支持日志轮转（按大小）
- 可配置的日志级别和格式
- 从 `settings.toml` 读取配置

### 2. 配置文件更新

**文件**: `settings.toml`

```toml
[default.logging]
level = "INFO"
file_enabled = true
console_enabled = false  # 关闭控制台输出
max_file_size = 10485760  # 10MB
backup_count = 5

[default.openai]
debug_enabled = true
log_requests = true
log_responses = true
log_level = "INFO"
log_to_file = true
log_to_console = false  # 关闭控制台输出
```

### 3. OpenAI客户端集成

**文件**: `utils/openai_client.py`

- 移除原来的 `print()` 语句
- 使用结构化的日志记录
- 支持不同级别的日志（INFO, DEBUG, WARNING, ERROR）
- 自动隐藏敏感信息（API密钥等）

## 功能特性

### 日志级别

- **INFO**: 基本的API调用信息
- **DEBUG**: 详细的请求/响应内容（包含消息预览）
- **WARNING**: 重试和警告信息
- **ERROR**: 错误信息

### 日志格式

```
2025-08-15 15:55:35,261 - openai_client - INFO - openai_client.py:191 - OpenAI客户端初始化完成 - 模型: moonshotai/Kimi-K2-Instruct
```

格式包含：
- 时间戳
- 日志器名称
- 日志级别
- 文件名和行号
- 日志消息

### 日志轮转

- 单个日志文件最大 10MB
- 保留 5 个备份文件
- 自动压缩和清理旧日志

### 安全性

- 自动隐藏 API 密钥
- 消息内容只显示数量，详细内容仅在 DEBUG 级别显示
- 响应内容有长度限制的预览

## 使用方法

### 基本使用

```python
from utils.logger_config import get_logger

# 获取日志器
logger = get_logger("my_module")

# 记录日志
logger.info("这是一条信息")
logger.warning("这是一条警告")
logger.error("这是一条错误")
logger.debug("这是调试信息")
```

### 预定义日志器

```python
from utils.logger_config import get_openai_logger, get_api_logger, get_system_logger

# OpenAI专用日志器
openai_logger = get_openai_logger()

# API调用专用日志器
api_logger = get_api_logger()

# 系统日志器
system_logger = get_system_logger()
```

### 配置控制

通过修改 `settings.toml` 中的 `[default.logging]` 部分来控制日志行为：

- `console_enabled = false` - 禁用控制台输出
- `file_enabled = true` - 启用文件输出
- `level = "DEBUG"` - 设置为DEBUG级别查看详细信息

## 日志文件位置

日志文件保存在 `logs/` 目录下：
- 主日志文件: `gtplanner_YYYYMMDD.log`
- 备份文件: `gtplanner_YYYYMMDD.log.1`, `gtplanner_YYYYMMDD.log.2` 等

## 测试验证

系统已通过以下测试：
1. ✅ 控制台输出完全禁用
2. ✅ 日志正确写入文件
3. ✅ 不同级别的日志正确记录
4. ✅ API调用日志包含完整信息
5. ✅ 敏感信息正确隐藏
6. ✅ 日志轮转功能正常

## 架构优势

1. **独立性**: 日志系统独立于业务逻辑
2. **可配置**: 通过配置文件灵活控制
3. **性能**: 使用标准库，性能优秀
4. **安全**: 自动处理敏感信息
5. **维护性**: 结构化日志便于问题排查
