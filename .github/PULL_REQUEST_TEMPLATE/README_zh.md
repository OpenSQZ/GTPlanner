# 拉取请求模板

本目录包含向 GTPlanner 智能工具推荐系统提交不同类型贡献时所使用的专用 PR (拉取请求) 模板。

## 可用模板

### 🔧 API 工具贡献 (`api_tool.md`)
当向系统贡献基于 API 的工具时，请使用此模板。

**适用场景：**
- Web API 和 REST 服务
- 基于云端的处理工具
- 外部服务集成
- 实时数据处理 API

**直接链接：** [创建 API 工具 PR](../../compare?template=api_tool.md)

### 📦 Python 包工具 (`python_package_tool.md`)
当贡献来自 PyPI 的 Python 包时，请使用此模板。

**适用场景：**
- PyPI 包和库
- 本地处理工具
- 数据分析包
- 实用工具库

**直接链接：** [创建 Python 包 PR](../../compare?template=python_package_tool.md)

### 📚 文档变更 (`documentation.md`)
此模板用于文档的更新和改进。

**适用场景：**
- README 文件更新
- API 文档变更
- 翻译更新
- 教程/指南的添加
- 文档错误修复

**直接链接：** [创建文档 PR](../../compare?template=documentation.md)

### 🛠️ 通用贡献 (`general.md`)
此模板用于通用的代码变更和改进。

**适用场景：**
- 错误修复
- 新功能添加
- 代码重构
- 性能改进
- 构建/持续集成 (CI) 变更

**直接链接：** [创建通用 PR](../../compare?template=general.md)

## 如何使用模板

### 方法一：URL 参数
在您创建 PR 的 URL 后面添加 `?template=template_name.md`：
```
https://github.com/your-org/GTPlanner/compare?template=api_tool.md
```

### 方法二：GitHub 界面
1. 点击“New pull request” (新建拉取请求)
2. 如果存在多个模板，GitHub 会显示模板选项
3. 为您的贡献选择合适的模板

### 方法三：手动选择
1. 正常创建一个新的 PR
2. 从相应的模板文件中复制内容
3. 替换掉默认的模板内容

## 模板使用指南

### 质量标准
所有贡献都必须满足以下标准：
- ✅ 信息完整准确
- ✅ 提供可行的示例和代码片段
- ✅ 经过适当的测试和验证
- ✅ 文档和描述清晰明了
- ✅ 不存在安全漏洞

### 工具贡献要求
对于 API 和 Python 包工具：
- **唯一标识符** 需遵循命名规范
- **全面的文档** 并附有示例
- 完成 **质量保证** 清单
- 提供 **测试验证** 及其结果
- 说明 **维护状态** 信息

### 按工具类型划分的必填字段

**API 工具 (APIS Tools):**
- `id`, `type`, `summary`, `description`, `examples`
- `base_url`: API 的基础 URL
- `endpoints`: 包含 `summary`, `method`, `path`, `inputs`, `outputs` 的数组

**Python 包工具 (PYTHON_PACKAGE Tools):**
- `id`, `type`, `summary`, `description`, `examples`
- `requirement`: PyPI 安装要求 (例如："package-name==1.0.0")

### 审查流程
1. **自动检查** - 模板完整性
2. **技术审查** - 功能性和准确性
3. **质量评估** - 是否符合标准
4. **安全审查** - 安全性和最佳实践
5. **社区反馈** - 用户体验验证

## 模板维护

这些模板由 GTPlanner 团队维护。如需改进模板或请求新模板：

1. 创建一个带有 `template` 标签的 issue
2. 描述所需的变更或新的模板类型
3. 提供理由和使用案例
4. 遵循标准的贡献流程

## 支持

如果您在选择或填写模板时需要帮助：
- 查看 [贡献指南](../../CONTRIBUTING.md)
- 在仓库中发起一个讨论 (discussion)
- 联系维护人员

---

**请记住：** 使用正确的模板有助于确保更快的审查速度和更有序的贡献管理！