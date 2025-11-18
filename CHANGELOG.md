# 更新日志 (Changelog)

本文档记录了 GTPlanner 项目新的变更。

---

## [未发布] - 2025-11-16

### 🎉 新增功能

#### 1. 文档多格式导出功能
- **新增节点**：`NodeExportDocument` (`gtplanner/agent/nodes/node_export.py`)
  - 支持将已生成的设计文档导出为多种格式
  - 实现 Markdown 到 HTML、TXT 的转换
  - 预留 PDF 和 DOCX 格式接口（待实现）

- **新增工具**：`export_document` 工具 (`gtplanner/agent/function_calling/agent_tools.py`)
  - 支持通过 Function Calling 调用文档导出功能
  - 支持批量导出多种格式
  - 支持导出单个文档类型或所有文档

- **HTML 导出特性**：
  - 集成 Mermaid.js 用于流程图可视化渲染
  - 应用现代化 CSS 样式，提升视觉效果
  - 响应式设计，支持移动端和打印

- **使用方式**：
  ```bash
  # 在 CLI 中直接请求
  导出设计文档为HTML格式
  导出所有文档为HTML和TXT格式
  ```

### 🔧 改进

#### 1. 文件命名机制优化
- **问题**：生成的文档文件名固定（如 `design.md`），多次生成会覆盖之前的文件
- **解决方案**：为文件名添加时间戳，格式：`{base_name}_{YYYYMMDD_HHMMSS}.{extension}`
- **影响范围**：
  - 初始文档生成时自动添加时间戳（`cli_handler.py`）
  - 导出文档时自动添加时间戳（`node_export.py`）
- **示例**：
  - `design.md` → `design_20251116_175952.md`
  - `database_design.md` → `database_design_20251116_180015.md`

#### 2. 文档查找逻辑优化
- **问题**：`edit_document` 和 `view_document` 工具可能操作旧版本的文档
- **解决方案**：按 `timestamp` 降序排序，确保总是操作最新版本的文档
- **影响文件**：
  - `gtplanner/agent/subflows/document_edit/nodes/document_edit_node.py`
  - `gtplanner/agent/nodes/node_view_document.py`
- **实现逻辑**：
  1. 筛选匹配文档类型的文档
  2. 按 `timestamp` 降序排序
  3. 选择第一个（最新的）文档进行操作

#### 3. 中文模板本地化改进
- **问题**：中文模板中的标题为英文，与中文内容不协调
- **解决方案**：将所有英文标题替换为对应的中文标题
- **影响文件**：`gtplanner/agent/prompts/templates/agents/design/design_node.py`
- **修改内容**：
  | 英文标题 | 中文标题 |
  |---------|---------|
  | Standard Operating Procedure | 标准操作流程 |
  | Flow Design | 流程设计 |
  | Applicable Design Pattern | 适用的设计模式 |
  | Flow High-level Design | 流程高层设计 |
  | Flow Diagram | 流程图 |
  | Prefabs | 预制件 |
  | Utility Functions | 工具函数 |
  | Node Design | 节点设计 |
  | Shared Store | 共享存储 |
  | Node Steps | 节点步骤 |
- **额外改进**：节点步骤部分的标签也进行了中文化：
  - `Purpose` → `目的`
  - `Type` → `类型`
  - `Steps` → `步骤`
  - `Input` → `输入`
  - `Output` → `输出`
  - `Necessity` → `必要性`

#### 4. CLI 进度条显示优化
- **问题**：文档生成时没有进度提示，用户不知道需要等待多久，体验不佳
- **解决方案**：
  - 在 `design_node.py` 中实现流式输出，并通过元数据标识消息类型
  - 在 `cli_handler.py` 中检测文档生成类型的消息，显示进度条而不是流式内容
  - 使用 `rich` 库的进度条组件，显示生成进度和已用时间
- **技术实现**：
  - 流式输出架构保留（前端 SSE 正常接收流式内容）
  - 通过事件元数据 `message_type: "document_generation"` 标识文档生成任务
  - CLI 自动检测消息类型，长时间任务显示进度条，普通消息显示流式内容
  - 根据字符数估算进度（平均文档长度约 5000 字符）
- **影响文件**：
  - `gtplanner/agent/streaming/stream_types.py`：`assistant_message_start` 支持元数据参数
  - `gtplanner/agent/subflows/design/nodes/design_node.py`：实现流式输出并添加元数据标识
  - `gtplanner/agent/streaming/cli_handler.py`：添加进度条支持
- **用户体验提升**：
  - 文档生成时显示清晰的进度条：`🤖 AI 正在生成设计文档... ████████░░░░░░░░ 45% 0:12`
  - 避免流式输出刷屏，界面更整洁
  - 实时显示进度百分比和已用时间
  - 普通对话消息仍保持流式显示，响应及时

### 📝 修改的文件列表

#### 新增文件
- `gtplanner/agent/nodes/node_export.py` - 文档导出节点实现（839 行）

#### 修改文件
- `gtplanner/agent/function_calling/agent_tools.py`
  - 添加 `export_document_tool` 工具定义
  - 添加 `_execute_export_document` 执行函数
  - 在 `execute_agent_tool` 中添加路由逻辑

- `gtplanner/agent/nodes/__init__.py`
  - 导出 `NodeExportDocument` 类

- `gtplanner/agent/streaming/cli_handler.py`
  - 修改 `_handle_design_document` 方法，添加时间戳到文件名
  - 删除重复的方法定义
  - 改进文档类型识别（设计文档 vs 数据库设计文档）

- `gtplanner/agent/subflows/document_edit/nodes/document_edit_node.py`
  - 改进文档查找逻辑，按时间戳排序获取最新文档

- `gtplanner/agent/nodes/node_view_document.py`
  - 改进文档查找逻辑，按时间戳排序获取最新文档

- `gtplanner/agent/prompts/templates/agents/design/design_node.py`
  - 将中文模板中的所有英文标题替换为中文
  - 将节点步骤部分的英文标签替换为中文

- `gtplanner/agent/prompts/templates/system/orchestrator.py`
  - 添加 `export_document` 工具的使用说明

- `gtplanner/agent/streaming/stream_types.py`
  - 修改 `assistant_message_start` 方法，支持可选的 `metadata` 参数
  - 允许在消息开始事件中传递元数据，用于标识消息类型

- `gtplanner/agent/subflows/design/nodes/design_node.py`
  - 在 `prep_async` 中传递 `streaming_session` 到 `prep_result`
  - 在 `exec_async` 中实现流式调用，支持实时发送生成内容
  - 添加元数据标识 `message_type: "document_generation"`

- `gtplanner/agent/streaming/cli_handler.py`
  - 添加 `rich` 库的进度条支持（带 try-except 处理）
  - 修改 `_handle_message_start`：检测消息类型，文档生成显示进度条
  - 修改 `_handle_message_chunk`：长时间任务更新进度条，普通消息显示流式内容
  - 修改 `_handle_message_end`：完成进度条并关闭
  - 修改 `close` 方法：确保进度条正确关闭

### 🧪 测试建议

1. **导出功能测试**：
   - 生成设计文档后，测试导出为 HTML、TXT 格式
   - 验证文件名包含时间戳
   - 检查 HTML 中 Mermaid 图表是否正确渲染
   - 验证批量导出功能

2. **文件命名测试**：
   - 多次生成文档，验证不会覆盖
   - 检查文件名格式是否正确（时间戳格式）
   - 验证不同文档类型的时间戳独立

3. **文档查找测试**：
   - 生成多个版本的文档
   - 使用 `view_document` 验证查看的是最新版本
   - 使用 `edit_document` 验证编辑的是最新版本

4. **中文模板测试**：
   - 生成中文设计文档
   - 验证所有标题均为中文
   - 验证节点步骤部分的标签为中文

5. **进度条功能测试**：
   - 生成设计文档，验证显示进度条而不是流式输出
   - 检查进度条是否显示进度百分比和已用时间
   - 验证普通对话消息仍显示流式内容
   - 检查前端 SSE 是否正常接收流式内容（进度条不影响流式架构）

### ⚠️ 已知限制

- PDF 和 DOCX 格式暂未实现（已预留接口，返回 `NotImplementedError`）
- HTML 中的 Mermaid 图表需要浏览器 JavaScript 支持才能渲染
- 文件命名使用时间戳，可能产生较多文件（建议定期清理旧文件）

### 📚 相关文档

- 文档导出功能详细使用指南：`docs/export_document_usage.md`
- CLI 使用文档：`gtplanner/agent/cli/README_zh.md`

---

## 格式说明

- `🎉 新增功能`：新增的功能特性
- `🔧 改进`：对现有功能的改进和优化
- `🐛 修复`：问题修复
- `📝 文档`：文档更新
- `⚡ 性能`：性能优化
- `🔒 安全`：安全相关更新

---

## 版本历史

本文档从 2025-11-16 开始维护。

