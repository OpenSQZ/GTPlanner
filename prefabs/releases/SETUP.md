# 仓库设置指南 (Repository Setup Guide)

> 本文档面向平台维护者，说明如何初始化和配置 `prefab-releases` 仓库

## 📋 初始化清单

### 1. GitHub 仓库设置

#### 基本设置
- [x] 创建仓库：`prefab-releases`
- [x] 设置为 Public 仓库
- [x] 添加仓库描述："AI 预制件生态系统的中央索引和发布管理平台"
- [x] 添加主题标签：`ai`, `prefab`, `automation`, `ci-cd`

#### 分支保护
进入 `Settings > Branches > Add rule`:

- [x] 分支名称模式：`main`
- [x] ✅ Require a pull request before merging
  - [x] ✅ Require approvals: 1
  - [x] ✅ Dismiss stale pull request approvals
- [x] ✅ Require status checks to pass before merging
  - [x] ✅ Require branches to be up to date
  - [x] 添加必需检查：`validate-pr`
- [x] ✅ Require conversation resolution before merging
- [x] ✅ Include administrators
- [x] ✅ Allow force pushes: 禁用
- [x] ✅ Allow deletions: 禁用

#### 权限设置
进入 `Settings > Collaborators and teams`:

- [ ] 创建 `Maintainers` 团队（Write 权限）
- [ ] 创建 `Contributors` 团队（Read 权限）
- [ ] 禁用 Fork 的直接推送

### 2. Actions 权限

进入 `Settings > Actions > General`:

- [x] **Actions permissions**: 
  - ✅ Allow all actions and reusable workflows
- [x] **Workflow permissions**:
  - ✅ Read repository contents and packages permissions
- [x] **Allow GitHub Actions to create and approve pull requests**: ❌

**注意**：本仓库采用被动同步模式，不需要配置任何 Secrets 或 Webhooks。

#### Dependabot 配置

- [x] 启用 Dependabot 安全更新
- [x] 创建 `.github/dependabot.yml` 配置文件
  - [x] GitHub Actions 依赖（每周更新）
  - [x] Python 依赖（每周更新）

### 3. 依赖安装

本仓库使用 `uv` 管理 Python 依赖。贡献者需要：

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync

# 运行验证脚本
uv run python3 scripts/local_validate.py
```

### 4. 文件完整性检查

确保所有必需文件存在：

```bash
cd prefab-releases

# 检查核心文件
ls -la community-prefabs.json  # 中央索引
ls -la schema.json              # JSON Schema
ls -la pyproject.toml           # uv 依赖配置

# 检查工作流
ls -la .github/workflows/pr-check.yml
ls -la .github/workflows/validate-index.yml

# 检查脚本
ls -la scripts/*.py

# 检查文档
ls -la README.md CONTRIBUTING.md SECURITY.md
```

### 5. 初始提交

```bash
# 初始化 Git（如果还没有）
cd prefab-releases
git init

# 添加所有文件
git add .

# 创建初始提交
git commit -m "chore: initial repository setup

- Add central index file (community-prefabs.json)
- Add JSON Schema validation
- Add PR check workflow
- Add deployment trigger workflow
- Add validation scripts
- Add comprehensive documentation
"

# 添加远程仓库
git remote add origin https://github.com/The-Agent-Builder/Prefab-Releases.git

# 推送到 main 分支
git branch -M main
git push -u origin main
```

### 6. 测试自动化流程

#### 测试 PR 检查

创建一个测试 PR：

```bash
# 创建测试分支
git checkout -b test/pr-check

# 添加一个测试条目
# 编辑 community-prefabs.json，添加一个测试条目

git add community-prefabs.json
git commit -m "test: add test prefab entry"
git push origin test/pr-check

# 在 GitHub 上创建 PR，观察 CI 是否运行
```

检查项：
- [x] PR 检查自动触发
- [x] 所有验证步骤运行
- [x] 错误信息清晰可读
- [x] 分支保护规则生效

#### Issue 模板和自动化

- [x] 创建 Bug Report 模板 (`.github/ISSUE_TEMPLATE/bug_report.yml`)
- [x] 创建 Feature Request 模板 (`.github/ISSUE_TEMPLATE/feature_request.yml`)
- [x] 配置 Issue 模板选择器 (`.github/ISSUE_TEMPLATE/config.yml`)
- [x] 创建 Stale Bot 工作流 (`.github/workflows/stale.yml`)
  - Issues: 30 天无活动后标记，7 天后关闭
  - PRs: 14 天无活动后标记，7 天后关闭

### 7. 团队设置

#### 添加维护者

1. 进入 `Settings > Collaborators and teams`
2. 添加维护者到 `Maintainers` 团队
3. 确保他们有审核和合并 PR 的权限

#### 制定审核标准

创建内部文档，包括：
- [ ] 代码审核清单
- [ ] 安全检查清单
- [ ] 常见问题处理流程
- [ ] 紧急情况响应流程

### 8. 监控和日志

#### GitHub Actions 监控

- [ ] 设置 Actions 失败通知
- [ ] 定期检查 workflow 运行状态
- [ ] 监控 workflow 运行时间和成本

#### 索引文件监控

运行定期验证：
- [ ] 配置 `validate-index.yml` workflow
- [ ] 设置每日验证计划
- [ ] 监控索引文件大小和增长

### 9. 文档和公告

#### 发布公告

- [ ] 在社区渠道宣布仓库启用
- [ ] 发布贡献指南链接
- [ ] 提供示例预制件

#### 更新其他仓库

- [ ] 在 `Prefab-Template` README 中添加链接
- [ ] 更新官方文档站点

## 🔧 维护任务

### 日常维护
- 审核新的 PR（目标：24 小时内）
- 检查 CI/CD 状态
- 回复 Issues 和 Discussions

### 每周维护
- 审查索引文件增长
- 检查已发布预制件的可用性
- 更新文档（如需要）

### 每月维护
- 更新依赖包版本
- 审查安全报告
- 统计和报告生态系统增长

### 季度维护
- 审查和更新流程
- 收集社区反馈
- 规划新功能

## 📞 故障排除

### CI 检查失败
1. 检查 GitHub Actions 日志
2. 确认网络连接正常
3. 检查 Python 依赖是否可用
4. 验证 uv 安装是否正确

### 索引文件损坏
1. 从 Git 历史恢复
2. 验证 JSON 格式
3. 运行 `local_validate.py`
4. 重新部署

## 🔒 安全注意事项

- ✅ 审查所有新贡献者的第一个 PR
- ✅ 监控异常的提交模式
- ✅ 保持依赖项更新
- ✅ 启用 Dependabot 自动更新
- ✅ 定期审核已发布的预制件

## 📊 成功指标

跟踪以下指标：
- 预制件总数
- 活跃贡献者数量
- PR 平均处理时间
- 自动化检查通过率
- 预制件下载/使用量（如果有）

## 📚 参考资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Branch Protection 指南](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [JSON Schema 文档](https://json-schema.org/)

---

## ✅ 配置完成状态

### 通过 GitHub CLI 完成的配置

#### 1. 分支保护规则（main 分支）✅
- [x] 要求 Pull Request 审核（1 个批准）
- [x] 要求对话解决
- [x] 对管理员也生效
- [x] 禁止强制推送
- [x] 禁止删除分支
- [x] 撤销过时的 PR 批准
- [ ] ~~要求状态检查通过~~ （暂不设置，等第一个预制件 PR 后再配置）

> **注意**：`validate-pr` 检查只对修改 `community-prefabs.json` 的 PR 触发。
> 为避免文档类 PR 被阻塞，暂不设为必需检查。待首个预制件 PR 提交后，
> GitHub 会自动识别该检查，届时可在分支保护设置中将其设为必需。

#### 2. 仓库功能 ✅
- [x] Issues 已启用
- [x] Discussions 已启用
- [x] Projects 已启用
- [x] Wiki 已禁用

#### 3. Dependabot 配置 ✅
- [x] Dependabot 安全更新已启用
- [x] 创建 `.github/dependabot.yml`
  - GitHub Actions 依赖（每周更新）
  - Python 依赖（每周更新）
  - 自动标签：`dependencies`

#### 4. Issue 模板 ✅
- [x] Bug Report 模板（`.github/ISSUE_TEMPLATE/bug_report.yml`）
- [x] Feature Request 模板（`.github/ISSUE_TEMPLATE/feature_request.yml`）
- [x] Issue 模板配置（`.github/ISSUE_TEMPLATE/config.yml`）
  - 链接到文档
  - 链接到 Discussions

#### 5. 自动化工作流 ✅
- [x] PR 检查工作流（`.github/workflows/pr-check.yml`）
  - 提取变更
  - Schema 验证
  - URL 可访问性检查
  - 构件验证
  - 重复检查
- [x] 定期索引验证（`.github/workflows/validate-index.yml`）
  - 每天凌晨运行
  - 全量验证
- [x] Stale Bot（`.github/workflows/stale.yml`）
  - Issues: 30天 → 标记 stale → 7天后关闭
  - PRs: 14天 → 标记 stale → 7天后关闭

#### 6. 仓库主题标签
- [x] ai, prefab, automation, ci-cd (已存在)
- ⚠️  尝试添加但 API 格式问题未成功: python, knative, serverless
- 💡 **需要手动添加**：进入 Settings > About > Topics

### 需要手动完成的配置

以下配置需要在 GitHub 网页端完成：

#### 1. 团队管理 ⏸️
进入 `Settings > Collaborators and teams`:
- [ ] 创建 `Maintainers` 团队（Write 权限）
- [ ] 创建 `Contributors` 团队（Read 权限）
- [ ] 添加维护者成员

#### 2. 仓库主题补充 ⏸️
进入 `Settings > About > Topics`:
- [ ] 手动添加：`python`, `knative`, `serverless`

#### 3. 安全设置建议 ⏸️
进入 `Settings > Security`:
- [ ] 启用 Code scanning（可选）
- [ ] 启用 Secret scanning（已启用）
- [x] Dependabot alerts（已启用）

---

## 🎉 配置验证

运行以下命令验证配置：

```bash
# 查看分支保护规则
gh api /repos/The-Agent-Builder/Prefab-Releases/branches/main/protection | jq

# 查看仓库配置
gh repo view The-Agent-Builder/Prefab-Releases --json hasIssuesEnabled,hasDiscussionsEnabled,hasProjectsEnabled

# 查看所有工作流
gh workflow list -R The-Agent-Builder/Prefab-Releases

# 查看 Dependabot 配置
cat .github/dependabot.yml

# 查看 Issue 模板
ls -la .github/ISSUE_TEMPLATE/
```

---

**配置完成时间**: 2025-10-15  
**配置执行者**: GitHub CLI (gh)  
**分支保护生效时间**: 2025-10-15 14:30 UTC+8  
**相关 PR**: [#4 - 完善仓库配置和自动化](https://github.com/The-Agent-Builder/Prefab-Releases/pull/4)

---

**重要提示**：从配置分支保护规则开始，所有对 `main` 分支的修改都必须通过 Pull Request！

---

如有问题，请联系平台技术团队或在 Discussions 中提问。
