# 预制件发布仓库 (Prefab Releases)

> **AI 预制件生态系统的中央索引和发布管理平台**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PR Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## 📖 概述

`prefab-releases` 是 AI 预制件生态系统的**权威发布仓库**，负责：

- 🗂️ **中央索引**：维护所有已发布预制件的元数据
- ✅ **自动校验**：通过 CI/CD 自动验证提交的预制件
- 🔍 **可发现性**：为 AI 和用户提供预制件发现入口
- 📡 **被动同步**：部署服务定时轮询索引文件获取更新

## 🏗️ 仓库结构

```
prefab-releases/
├── community-prefabs.json          # 中央索引文件（核心）
├── schema.json                     # JSON Schema 定义
├── pyproject.toml                  # uv 依赖配置
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md   # PR 提交模板
│   └── workflows/
│       ├── pr-check.yml            # 自动化 PR 校验
│       └── validate-index.yml      # 定期索引验证
├── scripts/                        # 自动化脚本
│   ├── extract_pr_changes.py      # 提取 PR 变更
│   ├── validate_schema.py         # Schema 验证
│   ├── check_artifact_url.py      # URL 可达性检查
│   ├── verify_artifact.py         # 构件内容验证
│   ├── check_duplicates.py        # 重复检查
│   └── local_validate.py          # 本地验证工具
├── README.md                       # 本文档
└── CONTRIBUTING.md                 # 贡献指南
```

## 🎯 快速开始

### 对于贡献者：发布你的预制件

1. **准备你的预制件**
   - 使用 [Prefab-Template](https://github.com/The-Agent-Builder/Prefab-Template) 创建预制件
   - 确保通过所有本地测试和验证
   - 在你的仓库中创建 Release 并上传 `.whl` 文件

2. **Fork 本仓库**
   ```bash
   # 点击页面右上角的 "Fork" 按钮
   # 然后克隆你的 fork
   git clone https://github.com/your-username/prefab-releases.git
   cd prefab-releases
   ```

3. **添加你的预制件条目**
   
   编辑 `community-prefabs.json`，添加一个新的条目：
   ```json
   {
     "id": "your-prefab-id",
     "version": "1.0.0",
     "author": "your-github-username",
     "repo_url": "https://github.com/your-username/your-prefab-repo",
     "name": "你的预制件名称",
     "description": "详细描述你的预制件功能，至少10个字符",
     "tags": ["tag1", "tag2", "tag3"]
   }
   ```

   > **注意**：`artifact_url` 会自动构造为：`{repo_url}/releases/download/v{version}/{id}-{version}.whl`  
   > 请确保你的 GitHub Release 文件名符合此规范！

4. **提交并创建 Pull Request**
   ```bash
   git checkout -b publish/your-prefab-id-1.0.0
   git add community-prefabs.json
   git commit -m "feat(publish): your-prefab-id@1.0.0"
   git push origin publish/your-prefab-id-1.0.0
   ```
   
   然后在 GitHub 上创建 Pull Request。

5. **等待审核和部署**
   - ✅ 自动化 CI 会验证你的提交
   - 👀 通过后，维护者会进行人工审核
   - 🎉 审核通过后合并
   - ⏰ 部署服务会定时轮询索引文件并自动部署

### 对于维护者：审核 PR

1. **检查自动化状态**
   - 确认所有 CI 检查都通过（绿色对勾）
   - 如果失败，要求贡献者修复

2. **人工审核清单**
   - [ ] 访问 `repo_url`，检查源代码质量
   - [ ] 检查是否有明显的恶意代码（如 `eval`, `exec`, 不安全的系统调用）
   - [ ] 验证 `author` 的 GitHub 信誉（账号年龄、贡献历史）
   - [ ] 确认功能描述准确、标签合理
   - [ ] 检查是否与现有预制件冲突或重复

3. **合并或拒绝**
   - 如果一切正常，点击 "Merge Pull Request"
   - 如果有问题，留下评论并标记为 "Request Changes"

## 📋 索引文件规范

### `community-prefabs.json` 结构

这是一个 JSON 数组，每个对象代表一个预制件版本：

```json
[
  {
    "id": "string",           // 预制件唯一标识（kebab-case）
    "version": "string",      // 语义化版本号（x.y.z）
    "author": "string",       // GitHub 用户名
    "repo_url": "string",     // 源码仓库 URL
    "name": "string",         // 人类可读的名称
    "description": "string",  // 详细描述
    "tags": ["string"]        // 标签数组（可选）
  }
]
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 预制件唯一标识，使用 kebab-case 格式，3-64 字符 |
| `version` | string | ✅ | 遵循语义化版本规范，格式：`major.minor.patch` |
| `author` | string | ✅ | GitHub 用户名，1-39 字符 |
| `repo_url` | string | ✅ | 必须是 `https://github.com/` 开头的有效 URL |
| ~~`artifact_url`~~ | ~~string~~ | ❌ | **已移除**，自动从 `repo_url` + `version` + `id` 构造 |
| `name` | string | ✅ | 预制件显示名称，3-100 字符 |
| `description` | string | ✅ | 功能描述，10-500 字符 |
| `tags` | array | ❌ | 标签列表，用于分类和搜索，最多 10 个 |

### 约束条件

- **(id, version) 唯一性**：同一个 `id` 和 `version` 的组合在整个数组中必须唯一
- **单一变更**：每个 PR 只能添加或修改一个条目
- **只读性**：除非特殊情况，已发布的条目不应被修改或删除

## 🔧 自动化流程

### PR 校验流程 (`pr-check.yml`)

当你创建或更新 PR 时，会自动执行以下检查：

1. **文件变更检查**：确保只修改了 `community-prefabs.json`
2. **提取变更**：识别新增、版本更新或元数据修改
3. **Schema 验证**：验证 JSON 格式和字段完整性
4. **URL 可达性**：检查自动构造的 `.whl` URL 是否可访问
5. **构件验证**：
   - 下载 `.whl` 文件（URL 自动构造）
   - 解压并查找 `prefab-manifest.json`
   - 验证 manifest 中的 `id` 和 `version` 与 PR 一致
6. **重复检查**：确保没有重复的 (id, version) 组合

所有检查通过后，PR 会显示绿色对勾 ✅。

### 部署同步机制

本仓库采用 **Webhook 推送模式**：

1. **索引文件**：`community-prefabs.json` 作为权威数据源
2. **自动触发**：PR 合并到 main 时，GitHub Actions 自动触发部署
3. **Webhook 调用**：通过 HMAC-SHA256 签名的 HTTP POST 请求通知部署服务
4. **实时部署**：部署服务收到请求后立即处理，实现秒级响应
5. **解耦设计**：部署服务可以独立升级，只需保持 API 兼容

**优势**：
- ✅ 实时响应，无延迟（相比轮询模式的 5 分钟延迟）
- ✅ 资源高效，按需触发（无需持续轮询）
- ✅ 安全验证，签名保证请求合法性
- ✅ 状态可查，支持通过 job_id 查询部署进度
- ✅ 易于扩展，支持多个部署服务订阅

## 🛡️ 安全性

### 自动化安全检查

- ✅ JSON Schema 验证
- ✅ URL 可达性验证
- ✅ Manifest 一致性验证
- ✅ 重复条目检测

### 人工安全审核

维护者会检查：
- 代码中是否存在恶意模式
- 贡献者的信誉和历史
- 功能描述是否准确
- 依赖项是否合理

### 安全建议

**对于贡献者：**
- 不要在代码中硬编码敏感信息
- 使用可信的第三方库
- 遵循最小权限原则

**对于维护者：**
- 始终进行人工审核
- 对首次贡献者保持警惕
- 定期审计已发布的预制件

## 📊 统计信息

```bash
# 查看已发布的预制件数量
cat community-prefabs.json | jq 'length'

# 按作者统计
cat community-prefabs.json | jq -r '.[].author' | sort | uniq -c | sort -rn

# 按标签统计
cat community-prefabs.json | jq -r '.[].tags[]' | sort | uniq -c | sort -rn

# 查找特定预制件的所有版本
cat community-prefabs.json | jq '.[] | select(.id=="your-prefab-id")'
```

## 🤝 贡献

我们欢迎社区贡献！在提交 PR 之前，请阅读：

- [贡献指南](CONTRIBUTING.md) - 详细的提交流程和规范
- [Prefab-Template](https://github.com/The-Agent-Builder/Prefab-Template) - 预制件模板仓库

## 📝 常见问题

### Q: 可以修改已发布的条目吗？

A: 一般不建议。预制件遵循不可变原则，如果需要更新，应该发布新版本。特殊情况（如 URL 失效）需要联系维护者。

### Q: 如何更新我的预制件？

A: 在你的仓库中发布新版本，然后提交新的 PR 添加新的条目（新的 version）。

### Q: 我的 PR 自动检查失败了怎么办？

A: 查看 Actions 日志，根据错误信息修复问题。常见问题：
- JSON 格式错误
- URL 无法访问
- manifest 信息不一致
- 重复的条目

### Q: 审核需要多久？

A: 通常在 24 小时内。如果超过 48 小时没有反馈，可以在 PR 中 @ 维护者。

### Q: 我可以删除我的预制件吗？

A: 已发布的预制件不建议删除，因为可能有用户依赖。如果确实需要下架，请联系维护者并说明原因。

## 📞 联系方式

- 🐛 报告问题：[GitHub Issues](https://github.com/The-Agent-Builder/Prefab-Releases/issues)
- 💬 讨论交流：[GitHub Discussions](https://github.com/The-Agent-Builder/Prefab-Releases/discussions)
- 📧 邮件联系：maintainers@example.com

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**感谢你为 AI 预制件生态系统做出贡献！** 🎉

