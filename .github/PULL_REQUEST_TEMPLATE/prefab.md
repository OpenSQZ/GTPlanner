# Prefab Contribution

感谢您为 GTPlanner 贡献预制件！请完整填写此模板，确保您的预制件符合我们的质量标准。

## 预制件信息

**预制件 ID:** `your-prefab-id`
> 格式：小写字母、数字和连字符，例如 `browser-automation-agent`

**预制件名称:**
> 预制件的可读名称，例如 "浏览器自动化代理"

**版本号:** `x.x.x`
> 语义化版本号，例如 `0.1.0`、`1.2.3`

**作者:**
> 您的名字或组织名

**GitHub 仓库:**
> 预制件源码仓库地址，例如 `https://github.com/your-org/your-prefab`

**简短描述 (Summary):**
> 一句话描述预制件的功能（建议 100 字以内）

**详细描述 (Description):**
```
详细描述预制件的功能，包括：
- 解决什么问题
- 核心功能和特性
- 典型使用场景
- 技术实现方式（如使用的主要库、API 等）
```

**标签 (Tags):**
> 添加 3-5 个相关标签，例如：`["ai", "automation", "web-scraping"]`

## 发布包信息

**GitHub Release URL:**
> 预制件的 GitHub Release 页面地址
> 例如：`https://github.com/your-org/your-prefab/releases/tag/v0.1.0`

**Wheel 文件名:**
> 发布的 Python Wheel 包文件名
> 例如：`your_prefab-0.1.0-py3-none-any.whl`

**Wheel 文件下载链接:**
> 完整的 wheel 文件下载地址
> 例如：`https://github.com/your-org/your-prefab/releases/download/v0.1.0/your_prefab-0.1.0-py3-none-any.whl`

## 预制件功能

**提供的函数:**

### 函数 1
- **函数名:** `function_name`
- **功能描述:** 简要描述函数的作用
- **参数说明:**
  - `param1` (类型): 参数描述
  - `param2` (类型): 参数描述
- **返回值:** 返回值说明
- **使用示例:**
```python
result = function_name(
    param1="value1",
    param2="value2"
)
```

### 函数 2 (如果有)
> 按相同格式添加更多函数说明

**所需的密钥/环境变量:**
- `SECRET_NAME_1`: 密钥用途说明
- `SECRET_NAME_2`: 密钥用途说明

## 质量保证

**本地测试完成情况:**
- [ ] 已在本地成功运行所有测试用例
- [ ] Flake8 代码风格检查通过
- [ ] Pytest 单元测试通过
- [ ] prefab-manifest.json 验证通过
- [ ] 已构建 Wheel 包并验证内容
- [ ] 版本号已在 pyproject.toml、prefab-manifest.json 中保持一致

**测试环境:**
- Python 版本: 3.x.x
- 操作系统: macOS/Linux/Windows
- 测试框架: pytest

**功能测试结果:**
```
测试场景 1: 基本功能测试
- 输入: xxx
- 预期输出: xxx
- 实际输出: ✅ 符合预期

测试场景 2: 错误处理测试
- 输入: xxx
- 预期输出: xxx
- 实际输出: ✅ 符合预期
```

## CI/CD 验证检查清单

根据 `prefab-pr-check.yml` 工作流，您的 PR 将自动验证以下内容：

**文件修改范围:**
- [ ] 仅修改了 `prefabs/releases/community-prefabs.json`
- [ ] 没有修改其他文件

**JSON 格式验证:**
- [ ] community-prefabs.json 格式正确（有效的 JSON 数组）
- [ ] 包含所有必需字段：id, version, author, repo_url, name, description, tags

**Wheel 包验证:**
- [ ] GitHub Release URL 可访问（返回 200 状态码）
- [ ] Wheel 文件下载链接可访问
- [ ] Wheel 包中包含 `prefab-manifest.json` 文件
- [ ] manifest 中的版本号与 community-prefabs.json 一致

**唯一性检查:**
- [ ] 预制件 ID 在 community-prefabs.json 中唯一（没有重复）
- [ ] 如果是更新现有预制件，新版本号大于旧版本号

## 文档和资源

**README.md:**
> 仓库中是否包含完整的 README 文档？
- [ ] 包含安装说明
- [ ] 包含使用示例
- [ ] 包含 API 文档
- [ ] 包含测试说明

**示例代码:**
> 是否提供了工作示例？
- [ ] 提供了基本使用示例
- [ ] 提供了高级功能示例
- [ ] 示例代码经过测试

**许可证:**
> 项目使用的开源许可证: MIT / Apache 2.0 / 其他

## 预制件在 community-prefabs.json 中的条目

请粘贴您要添加到 `community-prefabs.json` 的 JSON 对象：

```json
{
  "id": "your-prefab-id",
  "version": "0.1.0",
  "author": "your-name",
  "repo_url": "https://github.com/your-org/your-prefab",
  "name": "预制件名称",
  "description": "预制件功能描述",
  "tags": ["tag1", "tag2", "tag3"]
}
```

**注意事项:**
1. 新增预制件时，将条目添加到数组末尾
2. 更新现有预制件时，只修改对应的版本号和描述
3. 确保 JSON 格式正确（注意逗号、引号等）
4. tags 数组建议包含 3-5 个相关标签

## 贡献者检查清单

- [ ] 我已阅读并理解 GTPlanner 的预制件规范
- [ ] 我已在本地完整测试预制件功能
- [ ] GitHub Release 已创建并包含 wheel 文件
- [ ] Wheel 包中包含 prefab-manifest.json
- [ ] 版本号在所有文件中保持一致
- [ ] 预制件 ID 唯一且遵循命名规范
- [ ] 所有必需字段已填写完整
- [ ] JSON 格式正确无误
- [ ] 这不是重复的预制件
- [ ] 我有权限贡献此预制件

## 审核者检查清单

**For maintainers:**

- [ ] PR 仅修改 community-prefabs.json
- [ ] 预制件 ID 唯一且符合命名规范
- [ ] 所有必需信息已提供
- [ ] GitHub Release 可访问且包含正确的 wheel 文件
- [ ] Wheel 包结构正确（包含 prefab-manifest.json）
- [ ] 版本号一致性验证通过
- [ ] 功能描述准确清晰
- [ ] 标签选择恰当
- [ ] 没有重复功能
- [ ] CI/CD 检查全部通过

---

## 额外说明

**特殊依赖或要求:**
> 如果预制件有特殊的系统依赖、资源要求等，请在此说明

**已知限制:**
> 列出预制件的已知限制或注意事项

**后续计划:**
> 是否有计划的功能改进或版本更新

---

### 需要帮助？

- 查看 [预制件开发文档](../docs/prefab-development.md)（如果有）
- 参考现有预制件示例：[community-prefabs.json](../prefabs/releases/community-prefabs.json)
- 查看 [CI/CD 验证流程](.github/workflows/prefab-pr-check.yml)
- 在 Issues 中提问或寻求帮助
