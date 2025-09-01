# GTPlanner Tracing 使用指南

## 概述

GTPlanner已经集成了pocketflow-tracing，可以自动追踪所有Flow的执行过程，包括：
- Flow执行的开始和结束时间
- 每个Node的prep、exec、post阶段
- 输入和输出数据
- 错误和异常信息

## 配置

### 1. 环境变量配置

复制`.env.example`文件为`.env`，并配置以下变量：

```bash
# Langfuse配置（必需）
LANGFUSE_SECRET_KEY=your-secret-key-here
LANGFUSE_PUBLIC_KEY=your-public-key-here
LANGFUSE_HOST=https://your-langfuse-host.com

# PocketFlow Tracing配置（可选）
POCKETFLOW_TRACING_DEBUG=true
POCKETFLOW_TRACE_INPUTS=true
POCKETFLOW_TRACE_OUTPUTS=true
POCKETFLOW_TRACE_PREP=true
POCKETFLOW_TRACE_EXEC=true
POCKETFLOW_TRACE_POST=true
POCKETFLOW_TRACE_ERRORS=true

# 会话配置（可选）
POCKETFLOW_SESSION_ID=gtplanner-session
POCKETFLOW_USER_ID=gtplanner-user
```

### 2. Langfuse设置

1. 注册Langfuse账号：https://langfuse.com
2. 创建新项目
3. 获取Secret Key、Public Key和Host URL
4. 将这些信息填入`.env`文件

## 已启用Tracing的Flow

以下Flow已经启用了自动tracing：

### 1. ShortPlanningFlow
- **文件**: `agent/subflows/short_planning/flows/short_planning_flow.py`
- **Flow名称**: `ShortPlanningFlow`
- **功能**: 短规划生成流程

### 2. ResearchFlow
- **文件**: `agent/subflows/research/flows/research_flow.py`
- **Flow名称**: `ResearchFlow`
- **功能**: 研究调研流程

### 3. ArchitectureFlow
- **文件**: `agent/subflows/architecture/flows/architecture_flow.py`
- **Flow名称**: `ArchitectureFlow`
- **功能**: 架构设计流程

## 使用方式

### 自动Tracing

所有已启用tracing的Flow会自动记录执行信息，无需额外代码：

```python
from agent.subflows.short_planning.flows.short_planning_flow import ShortPlanningFlow

# 创建Flow实例
flow = ShortPlanningFlow()

# 准备共享数据
shared = {
    "structured_requirements": {
        "project_name": "用户管理系统",
        "main_functionality": "用户管理和权限控制",
        "technical_requirements": ["Python", "Flask", "SQLite"]
    }
}

# 运行Flow（自动进行tracing）
result = await flow.run_async(shared)
```

### 查看Trace

1. 运行Flow后，登录Langfuse仪表板
2. 在项目中查看最新的trace
3. 可以看到完整的执行轨迹，包括：
   - Flow级别的执行时间
   - 每个Node的详细执行信息
   - 输入输出数据
   - 错误信息（如果有）

## 为新Flow添加Tracing

如果要为新的Flow添加tracing，按以下步骤操作：

### 1. 导入tracing模块

```python
from pocketflow import AsyncFlow
from pocketflow_tracing import trace_flow
```

### 2. 创建带tracing的Flow类

```python
@trace_flow(flow_name="YourFlowName")
class TracedYourFlow(AsyncFlow):
    """带有tracing的自定义流程"""
    
    async def prep_async(self, shared):
        """流程级准备"""
        print("🚀 启动自定义流程...")
        shared["flow_start_time"] = __import__('asyncio').get_event_loop().time()
        
        return {
            "flow_id": "your_flow",
            "start_time": shared["flow_start_time"]
        }
    
    async def post_async(self, shared, prep_result, exec_result):
        """流程级后处理"""
        flow_duration = __import__('asyncio').get_event_loop().time() - prep_result["start_time"]
        
        shared["flow_metadata"] = {
            "flow_id": prep_result["flow_id"],
            "duration": flow_duration,
            "status": "completed"
        }
        
        print(f"✅ 自定义流程完成，耗时: {flow_duration:.2f}秒")
        return exec_result
```

### 3. 在创建函数中使用带tracing的Flow

```python
def create_your_flow():
    # 创建节点
    node1 = YourNode1()
    node2 = YourNode2()
    
    # 连接节点
    node1 >> node2
    
    # 创建带tracing的Flow
    flow = TracedYourFlow()
    flow.start_node = node1
    return flow
```

## 最佳实践

### 1. Flow命名
- 使用描述性的Flow名称
- 保持命名一致性
- 避免特殊字符

### 2. 数据记录
- 在prep_async中记录流程开始时间
- 在post_async中计算和记录执行时长
- 记录关键的流程元数据

### 3. 错误处理
- tracing会自动记录异常
- 在共享状态中记录自定义错误信息
- 使用描述性的错误消息

### 4. 性能考虑
- tracing会增加少量开销
- 在生产环境中可以通过环境变量控制tracing级别
- 避免记录过大的数据对象

## 故障排除

### 1. Tracing不工作
- 检查Langfuse配置是否正确
- 确认网络连接到Langfuse服务
- 查看控制台错误信息

### 2. 数据不显示
- 确认Flow使用了@trace_flow装饰器
- 检查Flow是否正确继承了AsyncFlow
- 验证环境变量配置

### 3. 性能问题
- 减少trace的数据量
- 调整POCKETFLOW_TRACE_*配置
- 考虑在开发环境启用详细tracing

## 示例

查看`examples/tracing_example.py`文件，了解完整的tracing使用示例。

## 相关文档

- [PocketFlow Tracing文档](https://redreamality.com/blog/pocketflow-tracing)
- [Langfuse文档](https://langfuse.com/docs)
- [GTPlanner架构文档](docs/system-architecture.md)
