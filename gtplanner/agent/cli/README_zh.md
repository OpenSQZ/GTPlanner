# GTPlanner CLI 使用指南

**Language**: [English](README.md) | [简体中文](README_zh.md) | [日本語](README_ja.md)

---

GTPlanner 提供功能强大的命令行界面，支持交互模式和直接执行模式。

![GTPlanner CLI](../../../assets/cil.png)

---

## 目录

- [快速开始](#快速开始)
- [交互模式](#交互模式)
- [直接执行模式](#直接执行模式)
- [会话管理](#会话管理)
- [命令参数](#命令参数)
- [CLI 命令](#cli-命令)
- [多语言支持](#多语言支持)
- [使用技巧](#使用技巧)

---

## 快速开始

### 启动交互式 CLI

```bash
# 方式 1: 使用启动脚本（推荐）
python gtplanner.py

# 方式 2: 直接运行 CLI
python gtplanner/agent/cli/gtplanner_cli.py

# 方式 3: 使用 uv
uv run python gtplanner.py
```

### 直接处理需求

```bash
# 不进入交互模式，直接生成规划
python gtplanner.py "设计一个图片描述生成器"

# 使用详细模式
python gtplanner.py --verbose "创建会议纪要自动生成助手"

# 指定语言
python gtplanner.py --language zh "为视频字幕提取工具生成PRD"
```

---

## 交互模式

### 启动交互模式

```bash
python gtplanner.py
```

启动后会看到欢迎界面：

```
╔══════════════════════════════════════════════════════════════╗
║                     GTPlanner CLI                            ║
║              AI驱动的PRD生成工具                              ║
╚══════════════════════════════════════════════════════════════╝

📋 新会话已创建: session_20241023_123456
💡 输入你的需求开始规划，或输入 /help 查看可用命令

你:
```

### 输入需求

直接输入你的需求描述：

```
创建一个智能邮件摘要助手，包括：
1. 自动读取邮件内容
2. 提取关键信息和行动项
3. 生成简洁摘要
4. 支持多语言邮件
5. 输出结构化报告
```

### 实时响应

GTPlanner 会流式显示处理过程：

```
🤖 GTPlanner 正在思考...

📊 [短期规划] 正在分析需求...
✅ 已生成初步规划方案

🔍 [技术调研] 正在搜索相关技术...
✅ 找到 3 个相关 Prefab

📝 [文档生成] 正在生成 PRD...
✅ PRD 生成完成
```

---

## 直接执行模式

不进入交互模式，直接处理单个需求：

### 基础用法

```bash
python gtplanner.py "你的需求描述"
```

### 示例

```bash
# 简单需求
python gtplanner.py "设计一个语音转文字助手"

# 详细需求
python gtplanner.py "设计一个PDF文档分析助手：
1. 自动提取文本和表格
2. 生成文档摘要
3. 支持多文档对比
4. 智能问答功能
5. 导出Markdown格式"

# 带参数
python gtplanner.py --verbose --language zh "创建视频字幕生成工具"
```

---

## 会话管理

GTPlanner 自动保存所有对话历史，支持随时加载和继续。

### 查看所有会话

在交互模式中：
```
你: /sessions
```

输出示例：
```
📋 可用会话:

1. session_20241023_123456 (2024-10-23 12:34:56)
   最后消息: 设计一个图片描述生成器
   
2. session_20241023_100000 (2024-10-23 10:00:00)
   最后消息: 创建会议纪要助手

使用 /load <session_id> 加载会话
```

### 加载指定会话

**在交互模式中：**
```
你: /load session_20241023_123456
```

**启动时加载：**
```bash
python gtplanner.py --load session_20241023_123456
```

### 创建新会话

```
你: /new
```

### 删除会话

```
你: /delete session_20241023_123456
```

---

## 命令参数

### 位置参数

```bash
python gtplanner.py [需求描述]
```

如果提供需求描述，将直接执行（非交互模式）。

### 可选参数

| 参数 | 短参数 | 说明 | 示例 |
|------|--------|------|------|
| `--verbose` | `-v` | 显示详细处理信息 | `python gtplanner.py -v "需求"` |
| `--load` | `-l` | 加载指定会话 | `python gtplanner.py -l session_id` |
| `--language` | `-L` | 设置界面语言 | `python gtplanner.py -L zh "需求"` |

### 参数组合

```bash
# 加载会话 + 详细模式
python gtplanner.py --load session_123 --verbose

# 指定语言 + 详细模式
python gtplanner.py --language zh --verbose "设计系统"

# 所有参数
python gtplanner.py -L zh -v -l session_123
```

---

## CLI 命令

在交互模式中可用的命令（以 `/` 开头）：

### 基础命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示所有可用命令 |
| `/quit` 或 `/exit` | 退出 CLI |

### 会话管理命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/new` | 创建新会话 | `/new` |
| `/sessions` | 列出所有会话 | `/sessions` |
| `/load <id>` | 加载指定会话 | `/load session_123` |
| `/delete <id>` | 删除指定会话 | `/delete session_123` |

### 调试命令

| 命令 | 说明 |
|------|------|
| `/verbose` | 切换详细模式开关 |
| `/stats` | 显示当前会话统计信息 |

### 命令示例

```
你: /help
📋 可用命令:
  /help     - 显示此帮助信息
  /new      - 创建新会话
  /sessions - 列出所有会话
  /load <id> - 加载指定会话
  ...

你: /stats
📊 会话统计:
  会话 ID: session_20241023_123456
  消息数: 10
  创建时间: 2024-10-23 12:34:56
  最后更新: 2024-10-23 13:00:00
```

---

## 多语言支持

GTPlanner CLI 支持多种语言界面。

### 支持的语言

| 语言 | 代码 | 示例 |
|------|------|------|
| 中文 | `zh` | `python gtplanner.py --language zh` |
| 英文 | `en` | `python gtplanner.py --language en` |
| 日文 | `ja` | `python gtplanner.py --language ja` |
| 西班牙文 | `es` | `python gtplanner.py --language es` |
| 法文 | `fr` | `python gtplanner.py --language fr` |

### 设置语言

**方式 1：启动时指定**
```bash
python gtplanner.py --language zh "设计一个智能问答助手"
```

**方式 2：配置文件**

在 `settings.toml` 中设置：
```toml
[default]
language = "zh"
```

**方式 3：自动检测**

不指定语言时，GTPlanner 会根据输入内容自动检测：

```bash
# 自动识别为中文
python gtplanner.py "设计一个文档分析助手"

# 自动识别为英文
python gtplanner.py "Design a video summary generator"
```

### 语言切换

在交互模式中，可以在会话过程中切换语言（通过输入不同语言的文本）。

---

## 使用技巧

### 1. 高效的需求描述

**好的需求描述：**
```
创建一个智能代码审查助手，包括：
1. 自动检测代码质量问题
2. 提供优化建议和示例
3. 支持多种编程语言
4. 生成审查报告
5. 集成到 Git 工作流
```

**不太好的需求描述：**
```
做一个代码检查工具
```

### 2. 使用详细模式调试

遇到问题时启用详细模式：

```bash
python gtplanner.py --verbose "你的需求"
```

详细模式会显示：
- 每个步骤的详细信息
- Prefab 调用过程
- 错误堆栈信息

### 3. 会话管理最佳实践

- **命名规范**：虽然会话 ID 自动生成，但可以通过需求描述识别
- **定期清理**：删除不需要的旧会话
- **导出重要内容**：将生成的 PRD 保存到文件

### 4. 批量处理

使用脚本批量处理多个需求：

```bash
#!/bin/bash
# batch_plan.sh

needs=(
    "设计语音转文字助手"
    "设计图片描述生成器"
    "设计文档摘要工具"
)

for need in "${needs[@]}"; do
    echo "处理: $need"
    python gtplanner.py "$need" > "output_$(date +%s).txt"
done
```

### 5. 输出重定向

保存输出到文件：

```bash
# 保存到文件
python gtplanner.py "设计智能翻译助手" > translation_prd.txt

# 同时显示和保存
python gtplanner.py "设计视频摘要工具" | tee video_summary_prd.txt
```

### 6. 组合使用参数

```bash
# 最佳实践：加载会话 + 详细模式 + 指定语言
python gtplanner.py \
    --load session_123 \
    --verbose \
    --language zh
```

---

## 高级用法

### 环境变量

设置环境变量以覆盖默认行为：

```bash
# 设置默认语言
export GTPLANNER_LANGUAGE="zh"

# 设置日志级别
export GTPLANNER_LOG_LEVEL="DEBUG"
```

### 自定义启动脚本

创建个人启动脚本 `my_gtplanner.sh`：

```bash
#!/bin/bash
# my_gtplanner.sh

# 设置环境
export GTPLANNER_LANGUAGE="zh"
export GTPLANNER_LOG_LEVEL="INFO"

# 启动 CLI
cd /path/to/GTPlanner
python gtplanner.py --verbose "$@"
```

使用：
```bash
chmod +x my_gtplanner.sh
./my_gtplanner.sh "你的需求"
```

---

## 常见问题

### Q1: 如何退出交互模式？

```
你: /quit
# 或
你: /exit
# 或按 Ctrl+C
```

### Q2: 会话保存在哪里？

会话默认保存在 `gtplanner_conversations.db` (SQLite 数据库)。

### Q3: 可以导出会话历史吗？

可以直接读取数据库或使用 CLI 复制输出。未来版本会提供导出功能。

### Q4: CLI 支持 Windows 吗？

完全支持！建议使用 Windows Terminal 以获得最佳体验。

### Q5: 如何禁用流式输出？

流式输出是 CLI 的核心特性，暂不支持禁用。如需非流式，请使用 API。

---

## 相关文档

- [快速开始](../../../docs/zh/README.md#快速开始)
- [配置指南](../../../docs/configuration_zh.md)
- [API 文档](../api/README_zh.md)
- [MCP 文档](../../../mcp/README_zh.md)

---

<p align="center">
  需要帮助？<a href="https://github.com/wang316902972/GTPlanner/issues">提交 Issue</a>
</p>

