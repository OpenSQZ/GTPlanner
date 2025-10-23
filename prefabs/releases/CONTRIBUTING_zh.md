# 贡献指南 (Contributing Guide)

**Language**: [English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING_zh.md) | [日本語](CONTRIBUTING_ja.md)

---

感谢你对 AI 预制件生态系统的贡献！本文档将指导你如何向 GTPlanner 仓库提交你的预制件。

## 目录

- [贡献者许可协议](#贡献者许可协议)
- [准备工作](#准备工作)
- [提交流程](#提交流程)
- [编写规范](#编写规范)
- [自动化检查](#自动化检查)
- [审核流程](#审核流程)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

## 贡献者许可协议

通过提交 Pull Request，你同意：

1. **开源协议**：你的预制件将以 MIT 或兼容的开源协议发布
2. **代码所有权**：你确认拥有提交代码的所有权或合法授权
3. **质量承诺**：你的代码经过充分测试且不包含恶意内容
4. **维护责任**：你承诺对你发布的预制件进行基本的维护和支持

## 准备工作

### 1. 创建你的预制件

首先，使用官方模板创建你的预制件：

```bash
# 1. 克隆模板仓库
git clone https://github.com/The-Agent-Builder/Prefab-Template.git my-prefab
cd my-prefab

# 2. 安装依赖
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
uv sync --dev

# 3. 开发你的功能
# 编辑 src/main.py 和 prefab-manifest.json

# 4. 运行测试
uv run pytest tests/ -v
uv run python scripts/validate_manifest.py

# 5. 创建 Release
git tag v1.0.0
git push origin v1.0.0
```

详细的预制件开发指南请参考 [Prefab-Template 文档](https://github.com/The-Agent-Builder/Prefab-Template)。

### 2. 发布你的构件

在你的 GitHub 仓库中：

1. 进入 "Releases" 页面
2. 点击 "Create a new release"
3. 选择或创建 tag（如 `v1.0.0`）
4. 上传构建生成的 `.whl` 文件
5. 发布 Release

**重要**：确保 Release 是公开的（public），否则自动化检查会失败。

### 3. Fork 本仓库

```bash
# 在 GitHub 上 Fork 本仓库
# 然后克隆你的 fork
git clone https://github.com/your-username/GTPlanner.git
cd GTPlanner
```

## 提交流程

### 第一步：创建分支

```bash
# 创建一个描述性的分支名
git checkout -b publish/your-prefab-id-1.0.0
```

### 第二步：编辑索引文件

编辑 `community-prefabs.json`，在数组末尾添加你的条目：

```json
[
  {
    "id": "existing-prefab",
    "version": "1.0.0",
    ...
  },
  {
    "id": "your-prefab-id",
    "version": "1.0.0",
    "author": "your-github-username",
    "repo_url": "https://github.com/your-username/your-prefab-repo",
    "name": "你的预制件名称",
    "description": "详细描述你的预制件功能，包括主要特性和使用场景",
    "tags": ["category1", "feature1", "tool-name"]
  }
]
```

**注意**：
- 确保 JSON 格式正确（使用在线工具如 jsonlint.com 验证）
- 最后一个对象后不要加逗号
- 使用 UTF-8 编码

### 第三步：本地验证（可选但推荐）

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装验证依赖
uv sync

# 验证 JSON 格式
python3 -c "import json; json.load(open('community-prefabs.json'))"

# 使用本地验证工具
uv run python3 scripts/local_validate.py
```

### 第四步：提交并推送

```bash
git add community-prefabs.json
git commit -m "feat(publish): your-prefab-id@1.0.0"
git push origin publish/your-prefab-id-1.0.0
```

**Commit 信息规范**：
- 格式：`feat(publish): <prefab-id>@<version>`
- 示例：`feat(publish): video-to-audio@1.2.0`

### 第五步：创建 Pull Request

1. 访问你的 fork 仓库页面
2. 点击 "Compare & pull request" 按钮
3. 填写 PR 模板中的信息
4. 确保所有清单项都已勾选
5. 提交 PR

### 第六步：等待审核

- **自动检查**（约 2-5 分钟）：CI 会自动验证你的提交
- **人工审核**（约 24 小时内）：维护者会审查代码和功能
- **合并**：审核通过后，PR 会被合并到 main 分支
- **部署**：部署服务会定时轮询索引文件并自动部署你的预制件

## 编写规范

### ID 命名规范

预制件 ID 应该：

- 使用 kebab-case 格式（小写字母和连字符）
- 描述性强，清晰表达功能
- 长度 3-64 字符
- 在整个生态系统中唯一

**好的例子**：
- `video-to-audio`
- `image-background-remover`
- `pdf-text-extractor`

**不好的例子**：
- `VideoToAudio`（不是 kebab-case）
- `v2a`（不够描述性）
- `my-awesome-super-amazing-video-converter-tool`（太长）

### 版本号规范

遵循 [语义化版本规范 (SemVer)](https://semver.org/lang/zh-CN/)：

- **格式**：`MAJOR.MINOR.PATCH`
- **MAJOR**：不兼容的 API 变更
- **MINOR**：向后兼容的功能新增
- **PATCH**：向后兼容的问题修复

**示例**：
- `1.0.0` - 首个稳定版本
- `1.1.0` - 新增功能
- `1.1.1` - Bug 修复
- `2.0.0` - 重大变更

### 描述规范

**name（名称）**：
- 简洁明了，3-100 字符
- 使用中文或英文
- 描述预制件的核心功能

**description（描述）**：
- 详细说明功能，10-500 字符
- 包括：
  - 核心功能
  - 主要用途
  - 技术特点（可选）
- 避免：
  - 营销性语言
  - 夸大宣传
  - 无关信息

**示例**：

```json
{
  "name": "视频转音频转换器",
  "description": "使用 FFmpeg 从视频文件中提取音频轨道，支持 MP4、AVI、MKV 等常见格式，输出高质量 MP3 或 WAV 音频文件。"
}
```

### 标签规范

**tags（标签）**：
- 使用小写字母和连字符
- 每个预制件最多 10 个标签
- 标签应该是：
  - 功能分类（如 `video`, `audio`, `image`）
  - 技术栈（如 `ffmpeg`, `opencv`, `pytorch`）
  - 应用场景（如 `conversion`, `editing`, `analysis`）

**推荐标签类别**：
- **媒体类型**：`video`, `audio`, `image`, `text`, `pdf`
- **操作类型**：`conversion`, `editing`, `analysis`, `generation`
- **技术工具**：`ffmpeg`, `opencv`, `pillow`, `pandas`

## 自动化检查

你的 PR 会经过以下自动检查：

| 检查项 | 说明 | 常见问题 |
|--------|------|----------|
| **文件修改** | 只能修改 `community-prefabs.json` | 不要修改其他文件 |
| **JSON 格式** | 验证 JSON 语法正确性 | 检查逗号、括号、引号 |
| **Schema 验证** | 验证字段类型和格式 | 确保所有必填字段存在 |
| **URL 可达性** | 检查自动构造的 .whl URL 可访问 | Release 必须是 public |
| **Manifest 一致性** | 验证 .whl 中的 manifest | id 和 version 必须匹配 |
| **重复检查** | 确保没有重复条目 | (id, version) 必须唯一 |

如果某项检查失败，点击查看详细日志，根据错误提示修复问题。

## 审核流程

### 自动化阶段（即时）

1. 所有 CI 检查必须通过
2. 任何失败都会阻止合并

### 人工审核阶段（24小时内）

维护者会检查：

1. **代码质量**
   - 访问你的 `repo_url`
   - 查看 `src/main.py` 代码
   - 评估代码结构和风格

2. **安全性**
   - 检查是否有恶意代码模式
   - 验证依赖项的安全性
   - 评估潜在风险

3. **功能性**
   - 确认描述准确
   - 评估实用性
   - 检查是否与现有预制件冲突

4. **贡献者信誉**
   - 查看 GitHub 个人资料
   - 检查贡献历史
   - 评估可信度

### 可能的结果

- **批准并合并**：一切正常，PR 被合并
- **请求修改**：需要你修复一些问题
- **拒绝**：不符合质量或安全标准（会说明原因）

## 最佳实践

### 代码质量

1. **遵循 Python 规范**
   - 使用 PEP 8 代码风格
   - 添加类型提示
   - 编写文档字符串

2. **充分测试**
   - 单元测试覆盖核心功能
   - 集成测试验证完整流程
   - 边界情况测试

3. **错误处理**
   - 捕获所有可能的异常
   - 返回结构化的错误信息
   - 提供有用的错误消息

### 依赖管理

1. **最小化依赖**
   - 只添加必要的依赖
   - 优先使用标准库
   - 避免过大的依赖包

2. **指定版本**
   - 在 `pyproject.toml` 中明确版本范围
   - 避免使用不稳定版本

3. **安全性**
   - 定期更新依赖
   - 使用已知安全的包
   - 避免有安全漏洞的版本

### 文档

1. **README 完整**
   - 清晰的使用说明
   - 功能示例
   - 依赖说明
   - 常见问题

2. **函数文档**
   - 每个函数都有文档字符串
   - 参数和返回值说明清楚
   - 提供使用示例

3. **Manifest 准确**
   - 描述与实际功能一致
   - 参数说明完整
   - 类型定义正确

### 版本管理

1. **语义化版本**
   - 严格遵循 SemVer 规范
   - 重大变更更新主版本号
   - 向后兼容更新次版本号

2. **变更日志**
   - 在 README 或 CHANGELOG 中记录变更
   - 说明新增功能、修复问题、破坏性变更

3. **稳定性**
   - 首次发布使用 1.0.0
   - 测试版使用 0.x.x
   - 确保版本稳定后再发布

## 故障排除

### 常见问题

#### 1. JSON 格式错误

**错误信息**：`Invalid JSON format`

**解决方法**：
```bash
# 使用 Python 验证 JSON
python3 -c "import json; json.load(open('community-prefabs.json'))"

# 或使用在线工具
# https://jsonlint.com/
```

常见错误：
- 多余的逗号
- 缺少引号
- 括号不匹配
- 使用了非 UTF-8 字符

#### 2. URL 不可访问

**错误信息**：`Failed to access artifact URL`

**解决方法**：
1. 确认 Release 是 public 的
2. 检查 URL 是否正确（复制粘贴到浏览器测试）
3. 确认 .whl 文件已成功上传
4. 等待 GitHub CDN 同步（可能需要几分钟）

#### 3. Manifest 不一致

**错误信息**：`ID/Version mismatch`

**解决方法**：
1. 检查 `prefab-manifest.json` 中的 `id` 和 `version`
2. 确保与 `community-prefabs.json` 中的条目完全一致
3. 重新构建并上传 .whl 文件

#### 4. 重复条目

**错误信息**：`Duplicate (id, version) combination`

**解决方法**：
1. 检查是否已经存在相同的 (id, version)
2. 如果要发布新版本，使用新的版本号
3. 如果要更新现有版本，需要联系维护者

#### 5. Schema 验证失败

**错误信息**：`Schema validation failed`

**解决方法**：
1. 检查所有必填字段是否存在
2. 验证字段格式（如 URL、版本号）
3. 确认值的类型正确（字符串、数组等）

### 获取帮助

如果遇到问题：

1. **查看日志**：点击失败的 CI 检查，查看详细错误信息
2. **搜索 Issues**：可能其他人遇到过相同问题
3. **提问讨论**：在 GitHub Discussions 中提问
4. **联系维护者**：在 PR 中 @ 维护者或发送邮件

## 发布后

### 验证部署

PR 合并后：

1. 检查部署通知（如果配置了）
2. 等待几分钟让系统同步
3. 验证预制件在平台上可用

### 维护

作为预制件作者，你应该：

1. **响应问题**：及时回复 Issues 和讨论
2. **修复 Bug**：发现问题及时修复并发布新版本
3. **更新依赖**：定期更新依赖库
4. **改进功能**：根据反馈持续改进

### 更新版本

发布新版本时：

1. 在你的仓库中开发新功能
2. 运行完整的测试
3. 创建新的 Release（新的版本号）
4. 提交新的 PR 到本仓库（添加新条目）

**注意**：不要修改已存在的条目，而是添加新的条目。

## 成功案例

查看已发布的预制件获取灵感：

```bash
# 查看所有预制件
cat community-prefabs.json | jq '.'

# 按作者查看
cat community-prefabs.json | jq '.[] | select(.author=="username")'

# 按标签查看
cat community-prefabs.json | jq '.[] | select(.tags[] | contains("video"))'
```

## 联系我们

- **报告问题**：[GitHub Issues](https://github.com/OpenSQZ/GTPlanner/issues)
- **讨论交流**：[GitHub Discussions](https://github.com/OpenSQZ/GTPlanner/discussions)

---

**感谢你的贡献！让我们一起构建更强大的 AI 预制件生态系统！**

