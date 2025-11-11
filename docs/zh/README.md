# GTPlanner: AI驱动的PRD生成工具

<p align="center">
  <img src="../../assets/banner.png" width="800" alt="GTPlanner Banner"/>
</p>

<p align="center">
  <strong>一款智能体需求描述文档（Agent PRD）生成工具，能将自然语言描述转化为结构化的、适用于 Vibe coding 的技术文档。</strong>
</p>

<p align="center">
  <a href="#概览">概览</a> •
  <a href="#web-ui-推荐">Web UI</a> •
  <a href="#mcp-集成">MCP 集成</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#配置">配置</a> •
  <a href="#项目结构">项目结构</a> •
  <a href="#prefab-生态系统">Prefab 生态系统</a> •
  <a href="#参与贡献">参与贡献</a> •
  <a href="#许可证">许可证</a>
</p>

<p align="center">
  <strong>语言版本:</strong>
  <a href="../../README.md">English</a> •
  <a href="README.md">简体中文</a> •
  <a href="../ja/README.md">日本語</a>
</p>

---

## 引言——如何让Agent自动帮你干活？

- 首先，你得定义活是什么：输入有哪些，具体操作步骤是什么，输出什么内容？如何定义任务成功了？。这些内容一般称为SOP，**能被SOP化的工作，就能被AI自动化。**
- 其次，你得给Agent合适的工具，人能用OFFICE全家桶, 能上网冲浪，能管理文件存数据等等。如果要Agent干活，这些工具也得给他。
- 最后，你得告诉Agent按照什么形式来组织成果。

这些定义在Agent语境下，有个更合适的词语，叫做上下文工程。具体来说，在Code Agent(Claude Code/Cursor/Augment/Devin/...)开始编码Agent前，我们希望用文档明确：
- design.md：定义活儿是什么。
- prefab.md：定义有哪些工具，如何使用。我们称为**预制件**。
- starter-kit：定义开发框架，可用环境等（这一部分不同项目间基本不变）。

这就是GTPlanner想做的事情，简化搭建Agent的流程。

## 为什么选择GTPlanner

GTPlanner的目标是帮您轻松生成一份Agent PRD，也即AI能够读懂的标准操作程序（standard operating procedure , SOP）。快速自动化你手边的任务。GTPlanner的设计哲学是：
- 追求**确定性**：通过清晰的SOP（Agent PRD）消除AI的歧义，确保其执行路径和结果高度可控且可预测。
- 追求**可组合**: 将SOP分解为可复用的“预制件”（Prefab）和任务模块，像搭积木一样组合它们，以构建更复杂的工作流。
- 追求**自由度**：我们不绑定执行平台（如n8n），而是直接使用最简的AI框架和原生python代码进行构建，从而保证最大限度的灵活和自由。

---

## Web UI (推荐)

为了获得最佳体验，我们强烈推荐使用 Web UI。它提供了为现代开发者量身打造的流畅 AI 规划工作流。

![GTPlanner Web UI](../../assets/web.gif)

**核心优势:**
- **智能规划助手**：AI 辅助快速生成系统架构和项目计划
- **即时文档生成**：自动创建全面的技术文档
- **完美适配 Vibe Coding**：优化输出，适配 Cursor、Windsurf、GitHub Copilot
- **团队协作**：多格式导出，方便共享

[立刻体验 Live Demo](https://the-agent-builder.com/)

---

## MCP 集成

<details>
<summary>点击展开 MCP 集成说明</summary>

GTPlanner 支持 Model Context Protocol (MCP)，可直接在 AI 编程工具中使用。

<table>
<tr>
<td width="50%">

**Cherry Studio 中使用**
![MCP in Cherry Studio](../../assets/Cherry_Studio_2025-06-24_01-05-49.png)

</td>
<td width="50%">

**Cursor 中使用**
![MCP in Cursor](../../assets/Cursor_2025-06-24_01-12-05.png)

</td>
</tr>
</table>

详细配置指南 → [MCP 文档](../../mcp/README_zh.md)

</details>

---

## 快速开始

### 在线极速体验（无需安装）

[体验 Web UI](https://the-agent-builder.com/) - 所见即所得的规划与文档生成体验

### 本地运行

#### 环境准备

- **Python ≥ 3.10**（推荐 3.11+）
- **包管理器**: [uv](https://github.com/astral-sh/uv)（推荐）
- **LLM API Key**: OpenAI / Anthropic / Azure OpenAI / 自建兼容端点

#### 安装

```bash
git clone https://github.com/OpenSQZ/GTPlanner.git
cd GTPlanner

# 使用 uv 安装依赖
uv sync
```

#### 配置

复制配置模板并设置 API Key：

```bash
cp .env.example .env
# 编辑 .env 文件，设置必需的环境变量
```

**必需配置：**
```bash
LLM_API_KEY="your-api-key-here"
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-5"
```

详细配置指南（包括常见供应商、Langfuse 等）→ [配置文档](../configuration_zh.md)

### CLI 使用

#### 交互模式

```bash
python gtplanner.py
```

进入后直接输入需求，例如：
```
创建一个视频分析助手，可以自动提取视频字幕、生成摘要和关键要点。
```

#### 直接执行

```bash
python gtplanner.py "设计一个文档分析助手，支持PDF、Word文档解析和智能问答"
```

CLI 详细文档（会话管理、参数说明等）→ [CLI 文档](../../gtplanner/agent/cli/README_zh.md)

### API 使用

启动 FastAPI 服务：

```bash
uv run fastapi_main.py
# 默认运行在 http://0.0.0.0:11211
```

访问 `http://0.0.0.0:11211/docs` 查看 API 文档

API 详细文档（端点说明、使用示例等）→ [API 文档](../../gtplanner/agent/api/README_zh.md)

### MCP 集成

```bash
cd mcp
uv sync
uv run python mcp_service.py
```

MCP 详细文档（客户端配置、可用工具等）→ [MCP 文档](../../mcp/README_zh.md)

---

## 配置

GTPlanner 支持多种配置方式：

- **环境变量** (.env 文件)：API Key、Base URL、Model 等
- **配置文件** (settings.toml)：语言、追踪、向量服务等
- **Langfuse 追踪**（可选）：执行过程追踪和性能分析

完整配置指南 → [配置文档](../configuration_zh.md)

---

## 项目结构

```
GTPlanner/
├── README.md                  # 主文档
├── gtplanner.py              # CLI 启动脚本
├── fastapi_main.py           # API 服务入口
├── settings.toml             # 配置文件
│
├── gtplanner/                # 核心代码
│   ├── agent/               # Agent 系统
│   │   ├── cli/            # → [CLI 文档](../../gtplanner/agent/cli/README_zh.md)
│   │   ├── api/            # → [API 文档](../../gtplanner/agent/api/README_zh.md)
│   │   ├── flows/          # 控制流程
│   │   ├── subflows/       # 专业子流程
│   │   └── ...
│   └── utils/              # 辅助函数
│
├── prefabs/                 # Prefab 生态系统
│   ├── README_zh.md        # → [Prefab 文档](../../prefabs/README_zh.md)
│   └── releases/           # 发布管理
│       ├── community-prefabs.json  # Prefab 注册表
│       └── CONTRIBUTING_zh.md # → [Prefab 贡献指南](../../prefabs/releases/CONTRIBUTING_zh.md)
│
├── mcp/                    # MCP 服务
│   └── README_zh.md       # → [MCP 文档](../../mcp/README_zh.md)
│
├── docs/                   # 文档
│   ├── zh/                # 中文文档
│   ├── ja/                # 日文文档
│   ├── configuration.md   # 配置指南
│   └── architecture/      # 架构文档
│
├── workspace/             # 运行时目录
│   ├── logs/             # 日志
│   └── output/           # 输出文档
│
└── tests/                # 测试
```

系统架构文档 → [架构文档](../architecture/README.md)

---

## Prefab 生态系统

GTPlanner 通过 Prefab 生态系统实现能力扩展。每个 Prefab 都是一个标准化、可复用的 AI 功能组件。

### 什么是 Prefab？

Prefab 是即用型的 AI 功能模块，可以：
- **被发现**：GTPlanner 自动识别可用 Prefab
- **被部署**：PR 合并后自动部署到平台
- **被集成**：通过标准 API 调用
- **版本管理**：语义化版本控制

### Prefab 如何增强 GTPlanner？

当你贡献一个 Prefab 到 `community-prefabs.json` 时：

1. **扩展规划能力**：GTPlanner 知道了一个新的解决方案
2. **智能推荐**：GTPlanner 会在生成规划时推荐合适的 Prefab
3. **自动集成**：规划文档中会包含 Prefab 的使用说明

**示例 Prefab：**
- **媒体处理**：[视频处理 Prefab](../../Video-processing/) - 视频转音频、字幕提取
- **数据服务**：[高德天气 Prefab](../../Amap-Weather/) - 天气查询
- **文档处理**：PDF 解析、Excel 处理
- **AI 服务**：语音识别、图像识别

### 快速上手

**使用 Prefab：**

通过 Prefab Gateway 网关调用任何已发布的 Prefab：

```bash
# 1. 在 AgentBuilder 平台创建 API Key
# 2. 通过网关调用 Prefab
curl -X POST "https://gateway.agentbuilder.com/v1/prefabs/{prefab-id}/execute" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"function": "function_name", "parameters": {...}}'
```

**浏览可用 Prefab：**
```bash
cat prefabs/releases/community-prefabs.json | jq '.'
```

**创建自己的 Prefab：**
```bash
git clone https://github.com/The-Agent-Builder/Prefab-Template.git my-prefab
cd my-prefab
uv sync --dev
# 开发、测试、发布
```

完整 Prefab 文档 → [Prefab 指南](../../prefabs/README_zh.md)  
网关调用详情 → [Prefab 使用指南](../../prefabs/README_zh.md#对于用户使用-prefab)

---

## 参与贡献

我们深信，一个卓越的工具离不开社区的智慧与共建。GTPlanner 期待您的参与！

### 贡献 Prefab（最简单的贡献方式）

**为什么贡献 Prefab？**

每个 Prefab 都会：
- 扩展 GTPlanner 的规划能力
- 帮助其他开发者解决问题
- 被自动纳入推荐系统
- 获得社区认可

**如何贡献？**

1. 使用模板创建 Prefab → [Prefab-Template](https://github.com/The-Agent-Builder/Prefab-Template)
2. 开发并测试你的功能
3. 发布 GitHub Release 并上传 `.whl` 文件
4. 向 `prefabs/releases/community-prefabs.json` 提交 PR

**Prefab 影响力：**
- **进入推荐系统**：`community-prefabs.json` 中的 Prefab 会被 GTPlanner 识别
- **智能匹配**：规划时自动推荐给合适的场景
- **自动部署**：PR 合并后自动部署到 Prefab 平台

详细贡献指南 → [Prefab 贡献文档](../../prefabs/releases/CONTRIBUTING_zh.md)

### 贡献核心代码

通过评测驱动的开发方式，提升 GTPlanner 的规划质量和系统性能。

核心代码贡献 → [贡献指南](CONTRIBUTING.md)

### 分享实践案例

分享您的使用经验，帮助社区发掘 GTPlanner 的全部潜力：

- **使用案例**：真实项目中的应用
- **GTPlanner 生成的 PRD**：展示规划质量
- **教程和最佳实践**：帮助新用户上手

提交案例 → 在 `docs/examples/community-cases/` 创建 PR


如有疑问欢迎扫码进群：
<img src="https://github.com/user-attachments/assets/5fc4f146-9558-4444-b360-2217eb646162" width="400" alt="联系二维码">


---

## 许可证

本项目基于 MIT 许可证。详情请参阅 [LICENSE](../../LICENSE.md) 文件。

---

## 致谢

- 基于 [PocketFlow](https://github.com/The-Pocket/PocketFlow) 异步工作流引擎构建
- 配置管理由 [Dynaconf](https://www.dynaconf.com/) 提供支持
- 旨在通过 MCP 协议与 AI 助手无缝集成

---

<p align="center">
  <strong>GTPlanner</strong> - 用 AI 的力量将您的想法转换为结构化的施工图。
</p>
