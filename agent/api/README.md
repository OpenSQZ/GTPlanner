# GTPlanner API 模块

这个模块提供了完整的 SSE (Server-Sent Events) 流式响应 API 功能，支持实时工具调用状态更新和前端集成。

## 功能特性

- **流式响应**: 支持 Server-Sent Events (SSE) 实时数据流
- **工具调用监控**: 实时显示工具调用状态和进度
- **多语言支持**: 支持中文、英文、日文、西班牙文、法文
- **会话管理**: 完整的会话生命周期管理
- **错误处理**: 优雅的错误处理和状态报告
- **元数据支持**: 可选的详细元数据信息

## 核心组件

### SSEGTPlanner

主要的 API 类，提供流式响应处理能力。

#### 主要方法

- `process_request_stream()`: 处理请求并生成流式响应
- `get_api_status()`: 获取 API 状态信息
- `get_session_status()`: 获取特定会话状态

#### 流式事件类型

- `conversation_start`: 对话开始
- `assistant_message_start`: 助手消息开始
- `assistant_message_chunk`: 助手消息片段
- `assistant_message_end`: 助手消息结束
- `tool_call_start`: 工具调用开始
- `tool_call_progress`: 工具调用进度
- `tool_call_end`: 工具调用结束
- `processing_status`: 处理状态
- `error`: 错误事件
- `conversation_end`: 对话结束

## 使用示例

### 基本用法

```python
from agent.api import SSEGTPlanner

# 创建 API 实例
api = SSEGTPlanner(verbose=True)

# 处理流式请求
async def handle_stream(data: str):
    print(f"收到数据: {data}")

result = await api.process_request_stream(
    agent_context=context_data,
    language="zh",
    response_writer=handle_stream,
    include_metadata=True
)
```

### 与 FastAPI 集成

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from agent.api import SSEGTPlanner

app = FastAPI()
api = SSEGTPlanner()

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate_sse():
        async def write_data(data: str):
            yield data
        
        await api.process_request_stream(
            agent_context=request.context,
            language=request.language,
            response_writer=write_data
        )
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream"
    )
```

## 配置选项

- `verbose`: 启用详细日志输出
- `include_metadata`: 包含详细元数据信息
- `buffer_events`: 缓冲事件（暂未实现）
- `heartbeat_interval`: 心跳间隔时间（秒）

## 错误处理

API 提供完整的错误处理机制：

1. **会话级错误**: 捕获并报告处理过程中的错误
2. **事件级错误**: 处理单个事件发送失败
3. **自动清理**: 自动清理异常会话和资源

## 性能优化

- **异步处理**: 完全异步的事件处理
- **会话管理**: 智能的会话生命周期管理
- **资源清理**: 自动清理过期会话和资源
- **内存优化**: 避免内存泄漏和资源积累

## 扩展性

API 设计支持以下扩展：

- **自定义事件类型**: 添加新的流式事件类型
- **自定义回调**: 实现自定义的流式回调处理
- **中间件支持**: 添加请求/响应中间件
- **监控集成**: 集成监控和指标收集