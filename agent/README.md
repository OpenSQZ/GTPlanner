# GTPlanner Agent 模块

此文档介绍GTPlanner 的Agent模块。 Agent 模块是GTPlanner的核心模块，负责整体调度。

## 项目结构

```
agent/
├── __init__.py                 # 模块主入口
├── gtplanner.py               # GTPlanner主控制器
├── context_types.py           # 无状态数据类型定义
├── pocketflow_factory.py      # PocketFlow数据转换工厂
├── llm_utils.py               # LLM调用工具
├── README.md                  # 项目说明文档
├── tracing_guide.md           # Tracing使用指南
├── nodes/                     # 原子能力节点
│   ├── __init__.py
│   ├── node_search.py         # 搜索引擎节点
│   ├── node_url.py            # URL解析节点
│   ├── node_compress.py       # 上下文压缩节点
│   └── node_output.py         # 输出文档节点
├── subflows/                  # 专业Agent子流程
│   ├── __init__.py
│   ├── architecture/          # 架构设计Agent子流程
│   ├── research/              # 研究调研Agent子流程
│   └── short_planning/        # 短规划Agent子流程
├── flows/                     # 主控制流程
│   ├── __init__.py
│   └── react_orchestrator_refactored/  # ReAct主控制器（重构版）
├── function_calling/          # Function Calling工具包装
│   ├── __init__.py
│   └── agent_tools.py         # Agent工具定义
└── utils/                     # 工具函数
    ├── URL_to_Markdown.py     # URL转Markdown工具
    └── search.py              # 搜索相关工具
```

## 核心组件

### 1. 无状态数据类型 (context_types.py)
- 定义Agent层无状态数据结构
- 支持序列化/反序列化
- 确保数据传递的类型安全

### 2. PocketFlow工厂 (pocketflow_factory.py)
- 负责数据格式转换
- 从AgentContext创建shared字典
- 从shared字典提取AgentResult

### 3. 原子能力节点 (nodes/)
每个节点实现特定的原子操作，基于pocketflow.Node：
- **node_search.py**: 执行网络搜索并返回结果
- **node_url.py**: 解析网页内容并提取信息
- **node_compress.py**: 压缩长文本保留关键信息
- **node_output.py**: 生成最终的文档文件

### 4. 专业Agent子流程 (subflows/)
每个子流程协调相关节点完成复杂业务逻辑：
- **architecture/**: 架构设计和文档生成流程
- **research/**: 信息研究和综合流程
- **short_planning/**: 短规划生成和确认流程

### 5. 主控制流程 (flows/)
- **react_orchestrator_refactored/**: 实现ReAct循环（思考-行动-观察）的重构版本

### 6. Function Calling工具 (function_calling/)
- **agent_tools.py**: Agent工具定义和包装，提供统一的工具调用接口

### 7. LLM工具 (llm_utils.py)
- 提供统一的LLM调用接口和管理功能

## 设计原则

### 1. 原子性操作
- 每个节点只处理单一职责
- 节点内部不接收数组，所有批处理在Flow层面完成
- 确保节点的可复用性和可测试性

### 2. 数据流驱动
- 通过共享状态在组件间传递数据
- 明确的数据转换和验证机制
- 支持数据血缘追踪

### 3. 错误处理
- 多层次的错误处理和恢复机制
- 支持重试、降级和熔断
- 详细的错误日志和监控

### 4. 扩展性设计
- 模块化架构便于扩展新功能
- 支持水平扩展和性能优化
- 插件化的节点和流程设计

## 使用示例

### 基本使用
```python
from agent import GTPlanner

# 创建GTPlanner实例
planner = GTPlanner()

# 处理用户需求
result = planner.process_user_request("我需要设计一个用户管理系统")

if result["success"]:
    print("处理成功!")
    print(f"会话ID: {result['session_id']}")
else:
    print(f"处理失败: {result['error']}")
```

### 获取处理结果
```python
# 获取结构化需求
requirements = planner.get_requirements()

# 获取研究发现
research = planner.get_research_findings()

# 获取架构设计
architecture = planner.get_architecture_draft()

# 获取完整状态
state = planner.get_state()
```

### 状态管理
```python
# 保存状态
planner.save_state("session_state.json")

# 重置状态
planner.reset()
```

## 开发指南

### 添加新节点
1. 在`nodes/`目录下创建新的节点文件
2. 继承`pocketflow.Node`类
3. 实现`prep()`, `exec()`, `post()`方法
4. 在`nodes/__init__.py`中导出

### 添加新子流程
1. 在`subflows/`目录下创建新的流程文件
2. 继承`pocketflow.Flow`类
3. 组合相关节点实现业务逻辑
4. 在`subflows/__init__.py`中导出

### 扩展数据类型
1. 在`context_types.py`中添加新的数据结构
2. 更新相关的数据类
3. 确保序列化和反序列化支持

## 依赖要求

- Python 3.8+
- pocketflow
- 其他依赖见requirements.txt

## 测试

```bash
# 运行单元测试
python -m pytest tests/

# 运行集成测试
python -m pytest tests/integration/

# 运行性能测试
python -m pytest tests/performance/
```
