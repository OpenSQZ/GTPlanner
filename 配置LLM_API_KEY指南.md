# 配置 LLM API Key 指南

## 🎯 问题确认

### 当前症状
- ✅ API连接成功
- ✅ 收到所有流程事件
- ✅ 执行时间正常（87秒）
- ❌ `new_messages_count: 0` - **没有生成任何内容**
- ❌ 没有任何助手消息内容

### 根本原因
**LLM API Key 未配置**，后端无法调用 LLM 生成内容

---

## 🚀 立即解决方案

### 方式 1: PowerShell（临时设置）

```powershell
# 设置环境变量
$env:LLM_API_KEY="sk-your-real-api-key-here"
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_MODEL="gpt-4"

# 验证设置
echo "LLM_API_KEY: $env:LLM_API_KEY"
```

### 方式 2: CMD（临时设置）

```cmd
set LLM_API_KEY=sk-your-real-api-key-here
set LLM_BASE_URL=https://api.openai.com/v1
set LLM_MODEL=gpt-4
```

### 方式 3: 创建 .env 文件（推荐）

由于 .env 文件可能被 gitignore，创建方法如下：

```powershell
# 创建文件
@"
LLM_API_KEY=sk-your-real-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
"@ | Out-File -FilePath .env -Encoding UTF8
```

---

## ✅ 验证配置

### 1. 检查环境变量

```bash
python check_env_simple.py
```

应该显示：
```
[3/5] Environment Variables
  [OK] LLM_API_KEY: sk-proj...
  [OK] LLM_BASE_URL: https://...
  [OK] LLM_MODEL: gpt-4
```

### 2. 重新启动服务

```bash
# 如果服务正在运行，按 Ctrl+C 停止
python fastapi_main.py
```

### 3. 测试 API

**打开浏览器**: http://localhost:11211/static/test_chat.html

**输入**: "设计一个用户管理系统"

**应该看到**:
- ✅ SSE连接建立
- ✅ 收到事件流程
- ✅ **有实际的助手消息内容** ← 这是关键！
- ✅ 生成完整的PRD

---

## 📋 不同供应商的配置

### OpenAI 官方
```bash
LLM_API_KEY="sk-proj-xxxxxxxxxxxxx"
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-4"
```

### Azure OpenAI
```bash
LLM_API_KEY="your-azure-key"
LLM_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
LLM_MODEL="gpt-4"
```

### 国内代理服务
```bash
LLM_API_KEY="your-proxy-key"
LLM_BASE_URL="https://your-proxy-provider.com/v1"
LLM_MODEL="gpt-4"
```

### 本地模型（如 O llama3）
```bash
LLM_API_KEY="no-needed"
LLM_BASE_URL="http://localhost:8000/v1"
LLM_MODEL="llama3"
```

---

## 🎯 测试用例

配置后，测试以下场景：

### 场景 1: 简单PRD生成
```
输入: 设计一个待办事项应用
期望: 生成完整的PRD文档
```

### 场景 2: 技术规划
```
输入: 设计一个微服务架构的电商平台
期望: 包含技术选型、架构设计、API设计
```

### 场景 3: 功能需求
```
输入: 设计一个支持SaaS计费的项目管理平台
期望: 包含功能模块、计费逻辑、技术方案
```

---

## ⚠️ 常见问题

### Q1: 设置后还是不工作？

**A**: 确保在同一个 PowerShell 窗口中：
1. 设置环境变量
2. 不关闭窗口
3. 重新启动服务

### Q2: 如何永久保存？

**A**: 使用 `setx` 命令（仅限 Windows）：
```cmd
setx LLM_API_KEY "sk-your-key"
setx LLM_BASE_URL "https://api.openai.com/v1"
setx LLM_MODEL "gpt-4"
```

注意：需要重新打开终端才能生效

### Q3: 如何验证是否生效？

**A**: 
```bash
python -c "import os; print(os.getenv('LLM_API_KEY', 'NOT SET'))"
```

### Q4: API Key 从哪获取？

**OpenAI**: https://platform.openai.com/api-keys
**Azure**: Azure Portal → Azure OpenAI
**国内**: 根据您的服务提供商

---

## 🎉 配置成功的标志

配置成功后，你应该能看到：

### 在测试页面中
- 收到 `ASSISTANT_MESSAGE_CHUNK` 事件
- 有实际的文本内容输出
- 显示完整的PRD生成过程
- `new_messages_count` > 0

### 在后台日志中
```
INFO: 开始处理请求，用户输入长度: XX
INFO: 正在调用LLM...
INFO: LLM响应成功，生成了 N 条消息
INFO: 请求处理成功，生成 X 条新消息
```

---

**现在就去配置 API Key 并测试吧！** 🚀

