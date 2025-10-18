📐 架构设计理解
核心特点
Agent 1 (需求澄清): 轻量级、快速响应、异步执行
用户体验：像普通聊天一样流畅
无需等待：不阻塞用户交互
智能决策：自主判断是否需要触发Agent 2
Agent 2 (总结提炼): 独立触发、并行执行
触发方式1：用户手动触发（UI按钮）
触发方式2：Agent 1自动触发（判断信息足够）
输入：对话历史
输出：结构化业务逻辑摘要（需用户确认）
Agent 3 (文档撰写): 基于确认后的摘要生成文档
数据流设计
用户输入 ──┐
          ├──> Agent 1 (快速响应) ──> 对话历史累积
用户输入 ──┘                              │
                                         ├──> Agent 1判断 ──┐
                            用户点击按钮 ─┘                 │
                                                           ▼
                                                    Agent 2 (后台执行)
                                                           │
                                                           ▼
                                                   业务逻辑摘要
                                                           │
                                    用户确认 ──────────────┘
                                         │
                                         ▼
                                  Agent 3 (生成文档)
                                         │
                                         ▼
                              工具推荐 + 技术文档
🎯 代码重构计划
Phase 1: 基础架构改造 (核心层)
Task 1.1: 创建轻量级对话Agent
目标: 实现快速响应的需求澄清Agent 文件创建/修改:
agent/subflows/clarification/
├── __init__.py
├── flows/
│   ├── __init__.py
│   └── clarification_flow.py          # 新建：轻量级对话流程
└── nodes/
    ├── __init__.py
    ├── conversation_node.py            # 新建：对话节点
    └── trigger_decision_node.py        # 新建：触发决策节点
关键设计点:
conversation_node.py:
使用流式响应保证快速反馈
提示词设计：简短、引导式提问
禁用重型工具调用（search, research等）
trigger_decision_node.py:
分析对话历史完整度
判断是否触发Agent 2
返回决策：{"should_trigger_summary": bool, "reason": str}
提示词模板:
agent/prompts/templates/agents/clarification/
├── __init__.py
├── conversation_prompt.py              # 新建：对话提示词
└── decision_prompt.py                  # 新建：决策提示词
数据结构:
# agent/context_types.py 新增
@dataclass
class ClarificationResult:
    """需求澄清结果"""
    conversation_messages: List[Message]  # 对话记录
    should_trigger_summary: bool          # 是否应触发总结
    trigger_reason: Optional[str]         # 触发原因
    confidence_score: float               # 信息完整度评分
Task 1.2: 创建总结提炼Agent
目标: 将对话历史转化为结构化需求 文件创建/修改:
agent/subflows/summarization/
├── __init__.py
├── flows/
│   ├── __init__.py
│   └── summarization_flow.py          # 新建：总结流程
└── nodes/
    ├── __init__.py
    ├── extract_requirements_node.py   # 新建：提取需求节点
    └── structure_workflow_node.py     # 新建：结构化工作流节点
关键设计点:
extract_requirements_node.py:
从对话中提取关键信息
识别业务目标、约束条件、核心功能
structure_workflow_node.py:
生成子流程列表
每个子流程包含：输入、输出、操作逻辑
输出格式：简短、清晰、可衡量
提示词模板:
agent/prompts/templates/agents/summarization/
├── __init__.py
├── extraction_prompt.py               # 新建：提取提示词
└── structuring_prompt.py              # 新建：结构化提示词
数据结构:
# agent/context_types.py 新增
@dataclass
class SubProcess:
    """子流程定义"""
    step_number: int
    description: str      # 简短描述
    inputs: List[str]     # 输入数据
    outputs: List[str]    # 输出结果
    logic: str           # 操作逻辑

@dataclass
class RequirementSummary:
    """需求总结"""
    business_goal: str
    constraints: List[str]
    sub_processes: List[SubProcess]
    metadata: Dict[str, Any]
    timestamp: str
Task 1.3: 重构文档撰写Agent
目标: 基于需求总结生成技术文档 文件修改:
agent/subflows/deep_design_docs/        # 重构现有
├── flows/
│   └── deep_design_docs_flow.py       # 修改：输入改为RequirementSummary
└── nodes/
    └── document_generation_node.py     # 修改：集成工具推荐结果
关键设计点:
输入改造：从dialogue_history改为RequirementSummary
集成工具推荐：每个子流程标注推荐工具
模板可插拔：支持不同文档模板
Phase 2: 编排层改造
Task 2.1: 创建新的编排器
目标: 协调三个Agent的异步执行 文件创建:
agent/flows/async_three_agent_orchestrator/
├── __init__.py
├── async_orchestrator_flow.py         # 新建：异步编排流程
├── async_orchestrator_node.py         # 新建：异步编排节点
└── constants.py                       # 新建：常量定义
关键设计点:
class AsyncThreeAgentOrchestrator:
    async def handle_user_message(self, message: str) -> str:
        """处理用户消息 - Agent 1快速响应"""
        
    async def trigger_summarization(self, 
                                    trigger_source: str) -> RequirementSummary:
        """触发总结 - Agent 2后台执行
        trigger_source: 'user_manual' | 'agent_auto'
        """
        
    async def generate_document(self, 
                                summary: RequirementSummary) -> str:
        """生成文档 - Agent 3执行"""
Task 2.2: 修改Function Calling工具定义
目标: 适配新的Agent架构 文件修改:
agent/function_calling/agent_tools.py   # 修改：新增工具定义
新增工具:
{
    "name": "trigger_summary",
    "description": "当收集到足够的需求信息时，触发总结提炼流程",
    "parameters": {
        "reason": {"type": "string", "description": "触发原因"}
    }
}
修改/废弃工具:
short_planning → 拆分为 clarify + summarize
design → 重命名为 generate_technical_doc
Phase 3: API层改造
Task 3.1: 扩展API接口
目标: 支持异步操作和手动触发 文件修改:
agent/api/agent_api.py                 # 修改：新增端点
新增端点:
# 对话端点 (Agent 1)
POST /api/v1/chat
{
    "session_id": "xxx",
    "message": "用户消息"
}
Response: {
    "reply": "Agent回复",
    "should_summarize": false  # Agent 1的建议
}

# 总结端点 (Agent 2)
POST /api/v1/summarize
{
    "session_id": "xxx",
    "trigger_source": "user_manual"  # 或 "agent_auto"
}
Response: {
    "summary": {...},
    "status": "completed"
}

# 文档生成端点 (Agent 3)
POST /api/v1/generate-doc
{
    "session_id": "xxx",
    "summary_id": "xxx",
    "template_type": "pocketflow_design"
}
Task 3.2: 状态管理优化
目标: 支持并发执行和任务跟踪 文件创建/修改:
agent/persistence/
├── task_manager.py                    # 新建：异步任务管理
└── session_state.py                   # 修改：扩展状态字段
关键功能:
class TaskManager:
    async def create_task(self, task_type: str, session_id: str) -> str:
        """创建后台任务"""
        
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """查询任务状态"""
        
    async def get_task_result(self, task_id: str) -> Any:
        """获取任务结果"""
Phase 4: 提示词系统优化
Task 4.1: Agent 1 提示词设计
目标: 简短、引导式、快速响应 文件创建:
agent/prompts/templates/agents/clarification/conversation_prompt.py
核心要求:
# 角色定位
你是一个需求分析助手，通过简短的对话帮助用户澄清需求。

# 核心原则
1. 回复简短（1-3句话）
2. 每次只问1-2个关键问题
3. 避免技术术语
4. 快速响应，不执行耗时操作

# 判断标准
当满足以下条件时，建议触发总结：
- 明确了业务目标
- 识别了核心功能（3个以上）
- 了解了关键约束条件
Task 4.2: Agent 2 提示词设计
目标: 结构化、精准、可衡量 文件创建:
agent/prompts/templates/agents/summarization/structuring_prompt.py
核心要求:
# 输出格式
每个子流程必须包含：
1. 步骤编号和描述（最简短的语言）
2. 输入：明确的数据来源
3. 输出：可衡量的结果
4. 操作逻辑：清晰的处理步骤

# 质量标准
- 描述精准：避免模糊词汇
- 步骤完整：覆盖所有业务环节
- 逻辑清晰：因果关系明确
Phase 5: 模板系统设计
Task 5.1: 创建模板管理器
目标: 支持可插拔的文档模板 文件创建:
agent/templates/
├── __init__.py
├── template_manager.py                # 新建：模板管理器
├── base_template.py                   # 新建：模板基类
└── pocketflow/
    ├── __init__.py
    └── design_template.md             # 新建：PocketFlow设计模板
关键设计:
class TemplateManager:
    def get_template(self, 
                    template_type: str,
                    template_path: Optional[str] = None) -> BaseTemplate:
        """获取模板"""
        
    def render_template(self, 
                       template: BaseTemplate,
                       data: RequirementSummary,
                       tools: List[Dict]) -> str:
        """渲染模板"""
Task 5.2: 实现默认模板
目标: PocketFlow design.md模板 文件创建:
agent/templates/pocketflow/design_template.md
模板结构:
# {project_name} 设计文档

## 1. 需求概述
{business_goal}

## 2. 业务流程
{for each sub_process}
### {step_number}. {description}
- 输入：{inputs}
- 输出：{outputs}
- 处理逻辑：{logic}
- 推荐工具：{recommended_tools}
{/for}

## 3. 技术架构
{architecture_design}

## 4. 数据结构
{data_structures}
Phase 6: CLI和用户体验优化
Task 6.1: CLI命令扩展
目标: 支持新的交互模式 文件修改:
agent/cli/gtplanner_cli.py              # 修改：新增命令
新增命令:
# 对话模式（Agent 1）
gtplanner chat "我想做一个智能客服系统"

# 手动触发总结（Agent 2）
gtplanner summarize --session <session_id>

# 查看总结结果
gtplanner show-summary --session <session_id>

# 生成文档（Agent 3）
gtplanner generate-doc --summary <summary_id>
Task 6.2: 流式响应优化
目标: Agent 1实时输出 文件修改:
agent/streaming/stream_interface.py     # 修改：优化延迟
优化点:
降低首字节延迟
增加chunk频率
添加打字机效果控制
📋 开发任务拆分
优先级P0（核心功能）
任务ID	任务名称	预计工时	依赖	负责模块
T1.1	创建对话节点和流程	4h	无	clarification/
T1.2	创建触发决策节点	3h	T1.1	clarification/
T2.1	创建总结提炼流程	5h	无	summarization/
T2.2	实现结构化输出	4h	T2.1	summarization/
T3.1	扩展context_types数据结构	2h	无	context_types.py
T3.2	创建异步编排器	6h	T1.1, T2.1	async_orchestrator/
T4.1	设计Agent 1提示词	3h	T1.1	prompts/
T4.2	设计Agent 2提示词	3h	T2.1	prompts/
P0小计: 30小时
优先级P1（API和集成）
任务ID	任务名称	预计工时	依赖	负责模块
T5.1	扩展API端点	4h	T3.2	api/agent_api.py
T5.2	实现任务管理器	5h	T3.2	persistence/task_manager.py
T5.3	修改Function Calling工具	3h	T3.2	function_calling/
T6.1	重构文档生成Agent	6h	T2.2	deep_design_docs/
T6.2	集成工具推荐	4h	T6.1	deep_design_docs/
P1小计: 22小时
优先级P2（模板和用户体验）
任务ID	任务名称	预计工时	依赖	负责模块
T7.1	创建模板管理器	4h	无	templates/
T7.2	实现PocketFlow模板	3h	T7.1	templates/pocketflow/
T8.1	CLI命令扩展	4h	T5.1	cli/
T8.2	流式响应优化	3h	T1.1	streaming/
T9.1	编写单元测试	8h	全部	tests/
T9.2	编写集成测试	6h	T9.1	tests/integration/
P2小计: 28小时
优先级P3（文档和向后兼容）
任务ID	任务名称	预计工时	依赖	负责模块
T10.1	更新README文档	2h	全部	agent/README.md
T10.2	编写迁移指南	3h	全部	docs/migration.md
T10.3	保留旧Orchestrator（兼容）	4h	T3.2	flows/
T10.4	添加deprecation警告	2h	T10.3	全局
P3小计: 11小时
🗂️ 文件结构总览
agent/
├── context_types.py                    # 修改：新增数据结构
├── flows/
│   ├── react_orchestrator_refactored/  # 保留（标记废弃）
│   └── async_three_agent_orchestrator/ # 新建：异步编排器
│       ├── __init__.py
│       ├── async_orchestrator_flow.py
│       ├── async_orchestrator_node.py
│       └── constants.py
├── subflows/
│   ├── clarification/                  # 新建：Agent 1
│   │   ├── flows/
│   │   │   └── clarification_flow.py
│   │   └── nodes/
│   │       ├── conversation_node.py
│   │       └── trigger_decision_node.py
│   ├── summarization/                  # 新建：Agent 2
│   │   ├── flows/
│   │   │   └── summarization_flow.py
│   │   └── nodes/
│   │       ├── extract_requirements_node.py
│   │       └── structure_workflow_node.py
│   ├── deep_design_docs/               # 重构：Agent 3
│   │   └── flows/
│   │       └── deep_design_docs_flow.py  # 修改输入
│   └── quick_design/                   # 保留或废弃？
├── prompts/
│   └── templates/
│       └── agents/
│           ├── clarification/          # 新建
│           │   ├── conversation_prompt.py
│           │   └── decision_prompt.py
│           ├── summarization/          # 新建
│           │   ├── extraction_prompt.py
│           │   └── structuring_prompt.py
│           └── deep_design/            # 修改
├── templates/                          # 新建：模板系统
│   ├── __init__.py
│   ├── template_manager.py
│   ├── base_template.py
│   └── pocketflow/
│       └── design_template.md
├── persistence/
│   ├── task_manager.py                 # 新建：任务管理
│   └── session_state.py                # 修改：扩展字段
├── api/
│   └── agent_api.py                    # 修改：新增端点
└── cli/
    └── gtplanner_cli.py                # 修改：新增命令
🎨 实施路线图
Week 1: 核心Agent开发
Day 1-2: T1.1, T1.2 (Agent 1)
Day 3-4: T2.1, T2.2 (Agent 2)
Day 5: T3.1 (数据结构)
Week 2: 编排和集成
Day 1-3: T3.2 (异步编排器)
Day 4-5: T4.1, T4.2 (提示词)
Week 3: API和文档生成
Day 1-2: T5.1, T5.2 (API扩展)
Day 3-5: T6.1, T6.2 (Agent 3重构)
Week 4: 模板和测试
Day 1-2: T7.1, T7.2 (模板系统)
Day 3-5: T9.1, T9.2 (测试)
Week 5: 完善和发布
Day 1-2: T8.1, T8.2 (用户体验)
Day 3-4: T10.1-T10.4 (文档和兼容)
Day 5: 整体测试和修复
⚠️ 风险和注意事项
技术风险
并发控制: Agent 2后台执行时的状态同步
方案: 使用任务队列（TaskManager）+ 状态锁
LLM决策准确性: Agent 1判断何时触发总结
方案: 引入置信度阈值，低于阈值时询问用户
向后兼容: 现有API客户端适配
方案: 保留旧端点，新增版本标识/api/v2/
用户体验风险
Agent 1回复过于简短: 可能丢失上下文
方案: 在简短回复中嵌入关键信息摘要
Agent 2触发时机不当: 信息不足或过度延迟
方案: 提供手动触发按钮作为备选
迁移风险
现有session数据: 旧格式不兼容
方案: 提供迁移脚本 migrate_sessions.py
🚀 下一步行动
准备开始实施时，请确认：
✅ 架构设计: 异步三Agent协作模式
✅ 触发机制: 用户手动 + Agent自动判断
✅ 数据流: 对话历史 → 结构化摘要 → 技术文档
❓ quick_design保留: 是否保留快速设计模式？
❓ 模板优先级: 是否只实现PocketFlow模板（其他可后续扩展）？
❓ 旧API废弃: 是否立即废弃或保留过渡期？
总预估工时: 91小时（约3-4周，单人开发） 准备好后我将立即开始执行！🎯