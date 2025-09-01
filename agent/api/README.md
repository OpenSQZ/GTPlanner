# GTPlanner SSE API

基于新的流式响应架构的GTPlanner API实现，提供HTTP Server-Sent Events (SSE) 接口来处理实时数据流传输。

## 🚀 特性

- **流式响应**: 基于SSE的实时数据传输
- **无状态设计**: 使用StatelessGTPlanner，支持高并发
- **类型安全**: 基于StreamEventType/StreamCallbackType的类型安全架构
- **智能工具调用**: 实时显示工具执行状态和进度
- **优雅错误处理**: 完整的错误处理和资源清理机制
- **灵活配置**: 支持元数据、缓冲、心跳等配置选项

## 📦 安装

确保已安装项目依赖：

```bash
pip install -r requirements.txt
```

可选：安装aiohttp用于HTTP服务器示例：

```bash
pip install aiohttp
```

## 🎯 快速开始

### 基本使用

```python
import asyncio
from agent.api import SSEGTPlanner

async def main():
    # 创建API实例
    api = SSEGTPlanner(
        include_metadata=True,
        buffer_events=False,
        verbose=True
    )
    
    # 定义SSE数据写入函数
    async def write_sse_data(data: str):
        print(f"SSE: {data}", end="")
    
    # 处理请求
    result = await api.process_simple_request(
        user_input="设计一个用户管理系统",
        response_writer=write_sse_data
    )
    
    print(f"处理结果: {result}")

asyncio.run(main())
```

### 使用便捷函数

```python
import asyncio
from agent.api import create_sse_response

async def main():
    async def write_sse_data(data: str):
        print(f"SSE: {data}", end="")
    
    result = await create_sse_response(
        user_input="解释什么是微服务架构",
        response_writer=write_sse_data,
        include_metadata=True,
        verbose=True
    )
    
    print(f"结果: {result}")

asyncio.run(main())
```

## 🔧 API 参考

### SSEGTPlanner

主要的API类，提供流式响应处理功能。

#### 构造函数

```python
SSEGTPlanner(
    include_metadata: bool = False,
    buffer_events: bool = False,
    heartbeat_interval: float = 30.0,
    verbose: bool = False
)
```

**参数:**
- `include_metadata`: 是否包含详细元数据
- `buffer_events`: 是否缓冲事件以优化传输
- `heartbeat_interval`: 心跳间隔（秒）
- `verbose`: 是否显示详细日志信息

#### 主要方法

##### process_request_stream()

```python
async def process_request_stream(
    self,
    user_input: str,
    response_writer: Callable[[str], Awaitable[None]],
    session_id: Optional[str] = None,
    **config_options
) -> Dict[str, Any]
```

处理用户请求并通过SSE流式返回结果。

**参数:**
- `user_input`: 用户输入内容
- `response_writer`: SSE数据写入函数
- `session_id`: 可选的会话ID
- `**config_options`: 额外的配置选项

**返回:** 处理结果摘要

##### process_simple_request()

```python
async def process_simple_request(
    self,
    user_input: str,
    response_writer: Callable[[str], Awaitable[None]]
) -> Dict[str, Any]
```

简化的请求处理方法。

##### get_api_status()

```python
def get_api_status(self) -> Dict[str, Any]
```

获取API状态信息。

#### 配置方法

- `enable_metadata()` / `disable_metadata()`: 启用/禁用元数据
- `enable_buffering()` / `disable_buffering()`: 启用/禁用事件缓冲
- `set_heartbeat_interval(interval: float)`: 设置心跳间隔

### 便捷函数

#### create_sse_response()

```python
async def create_sse_response(
    user_input: str,
    response_writer: Callable[[str], Awaitable[None]],
    **config_options
) -> Dict[str, Any]
```

便捷函数，创建SSE响应。

## 🌐 HTTP 服务器示例

项目包含一个完整的HTTP服务器示例，展示如何在Web应用中使用API。

### 启动示例服务器

```bash
python agent/api/example_server.py
```

服务器将在 `http://localhost:8080` 启动，提供以下端点：

- `GET /`: 演示页面
- `GET /health`: 健康检查和API状态
- `POST /api/chat`: 普通聊天API（非流式）
- `GET /api/chat/stream`: SSE流式聊天API

### API 端点

#### GET /api/chat/stream

SSE流式聊天端点。

**查询参数:**
- `user_input`: 用户输入（必需）
- `include_metadata`: 是否包含元数据（可选，默认false）

**响应:** Server-Sent Events 流

**示例:**
```bash
curl -N "http://localhost:8080/api/chat/stream?user_input=设计用户系统&include_metadata=true"
```

#### POST /api/chat

普通聊天API（非流式）。

**请求体:**
```json
{
    "user_input": "设计一个用户管理系统"
}
```

**响应:**
```json
{
    "result": {
        "success": true,
        "session_id": "...",
        "new_messages_count": 2
    },
    "sse_events": ["event: ...", "data: ..."]
}
```

## 🧪 测试

运行API测试：

```bash
python agent/api/test_agent_api.py
```

测试包括：
- 基本API功能测试
- 配置选项测试
- 错误处理测试
- 便捷函数测试
- 流式会话管理测试

## 📊 SSE 事件格式

API通过SSE发送以下类型的事件：

### 对话事件
- `conversation_start`: 对话开始
- `assistant_message_start`: 助手消息开始
- `assistant_message_chunk`: 助手消息片段
- `assistant_message_end`: 助手消息结束
- `conversation_end`: 对话结束

### 工具调用事件
- `tool_call_start`: 工具调用开始
- `tool_call_progress`: 工具调用进度
- `tool_call_end`: 工具调用结束

### 状态事件
- `processing_status`: 处理状态更新
- `error`: 错误事件
- `heartbeat`: 心跳事件

### 事件格式示例

```
event: assistant_message_chunk
data: {"event_type": "assistant_message_chunk", "timestamp": "2024-01-01T12:00:00", "session_id": "abc123", "data": {"content": "Hello"}}

event: tool_call_start
data: {"event_type": "tool_call_start", "timestamp": "2024-01-01T12:00:01", "session_id": "abc123", "data": {"tool_name": "search", "status": "starting"}}
```

## 🔄 与CLI层的对比

| 特性 | CLI层 | API层 |
|------|-------|-------|
| 会话管理 | ✅ SQLiteSessionManager | ❌ 无状态 |
| 交互式命令 | ✅ 命令处理 | ❌ 单次请求 |
| 显示输出 | ✅ Rich Console | ❌ SSE流 |
| 流式响应 | ✅ CLIStreamHandler | ✅ SSEStreamHandler |
| 核心处理器 | ✅ StatelessGTPlanner | ✅ StatelessGTPlanner |
| 错误处理 | ✅ 一致 | ✅ 一致 |
| 资源清理 | ✅ 一致 | ✅ 一致 |

## 📝 注意事项

1. **无会话管理**: API层不提供会话管理功能，每次请求都是独立的
2. **资源清理**: API会自动清理流式会话资源
3. **错误处理**: 所有错误都会通过SSE事件发送
4. **并发支持**: 基于无状态设计，支持高并发请求
5. **配置灵活**: 支持请求级别的配置覆盖

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个API。

## 📄 许可证

请参考项目根目录的许可证文件。
