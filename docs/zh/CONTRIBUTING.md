# 贡献指南

感谢你对 GTPlanner 的关注！我们欢迎各种形式的贡献。

---

## 🧩 贡献 Prefab（最推荐）

**这是最简单、最有影响力的贡献方式！**

### 为什么贡献 Prefab？

每个 Prefab 都会：
- ✅ **扩展 GTPlanner 的规划能力** - 让 GTPlanner 知道一个新的解决方案
- ✅ **被自动推荐** - 纳入 `community-prefabs.json` 后会被推荐系统使用
- ✅ **帮助整个社区** - 其他开发者可以直接使用你的 Prefab
- ✅ **获得认可** - 在社区中建立影响力

### Prefab 如何影响 GTPlanner？

当你的 Prefab 被合并到 `community-prefabs.json` 后：

1. **📋 进入推荐系统**
   - GTPlanner 在生成规划时会识别你的 Prefab
   - 根据需求场景自动推荐

2. **🎯 智能匹配**
   - 根据功能描述和标签进行智能匹配
   - 在合适的规划场景中被引用

3. **🔗 自动集成**
   - 规划文档中会包含 Prefab 的使用说明
   - 提供标准的集成方式

### 如何创建 Prefab？

#### 1. 使用模板

```bash
git clone https://github.com/The-Agent-Builder/Prefab-Template.git my-prefab
cd my-prefab
uv sync --dev
```

#### 2. 开发功能

编辑 `src/main.py`，实现你的功能：

```python
def my_function(param1: str, param2: int = 0) -> dict:
    """
    一句话描述功能
    
    Args:
        param1: 参数说明
        param2: 可选参数
    
    Returns:
        dict: {"success": bool, "result": any}
    """
    try:
        # 实现你的功能
        result = do_something(param1, param2)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

#### 3. 更新 Manifest

编辑 `prefab-manifest.json`：

```json
{
  "manifest_version": "3.0",
  "name": "my-awesome-prefab",
  "version": "1.0.0",
  "description": "简短描述你的 Prefab 功能",
  "author": "Your Name",
  "functions": [
    {
      "name": "my_function",
      "description": "详细的功能描述",
      "parameters": {
        "param1": {"type": "string", "description": "参数说明"},
        "param2": {"type": "integer", "description": "可选参数", "default": 0}
      },
      "returns": {
        "type": "object",
        "description": "返回值说明"
      }
    }
  ]
}
```

#### 4. 测试

```bash
# 运行测试
uv run pytest tests/ -v

# 验证 manifest
uv run python scripts/validate_manifest.py

# 本地测试功能
uv run python -c "from src.main import my_function; print(my_function('test'))"
```

#### 5. 发布

```bash
# 构建 wheel 包
uv build

# 在 GitHub 创建 Release
gh release create v1.0.0 \
  --title "Release v1.0.0" \
  --notes "Initial release" \
  dist/*.whl
```

#### 6. 提交到 GTPlanner

向 `prefabs/releases/community-prefabs.json` 提交 PR：

```json
{
  "id": "my-awesome-prefab",
  "version": "1.0.0",
  "author": "YourGitHubUsername",
  "repo_url": "https://github.com/YourGitHubUsername/my-awesome-prefab",
  "name": "My Awesome Prefab",
  "description": "简短描述",
  "tags": ["category", "feature"]
}
```

### Prefab 类型示例

#### 数据处理类
- PDF 文本提取
- Excel 数据分析
- 图片格式转换
- 视频字幕提取

#### AI 服务类
- 语音识别
- 图像描述生成
- 文本摘要
- 智能翻译

#### 集成服务类
- 天气查询 API
- 地图服务
- 支付接口
- 消息推送

#### 参考示例
- [视频处理 Prefab](../../Video-processing/)
- [高德天气 Prefab](../../Amap-Weather/)
- [Prefab 模板](https://github.com/The-Agent-Builder/Prefab-Template)

📖 详细指南 → [Prefab 贡献文档](../../prefabs/releases/CONTRIBUTING.md)

---

## 💻 贡献核心代码

通过评测驱动的开发方式，提升 GTPlanner 的规划质量和性能。

### 开发流程

#### 1. Fork 和克隆

```bash
# Fork 仓库
gh repo fork OpenSQZ/GTPlanner --clone

cd GTPlanner
```

#### 2. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

#### 3. 安装开发环境

```bash
uv sync --dev
```

#### 4. 进行开发

- 遵循现有代码风格
- 添加必要的测试
- 更新相关文档

#### 5. 运行测试

```bash
# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_specific.py -v

# 代码风格检查
uv run flake8 gtplanner/ --max-line-length=120
```

#### 6. 提交代码

```bash
git add .
git commit -m "feat: add new feature"
# 或
git commit -m "fix: fix specific bug"
```

提交信息格式：
- `feat:` - 新功能
- `fix:` - Bug 修复
- `docs:` - 文档更新
- `refactor:` - 重构
- `test:` - 测试相关
- `chore:` - 构建/工具相关

#### 7. 推送并创建 PR

```bash
git push origin feature/your-feature-name

# 创建 PR
gh pr create --title "Feature: Your Feature Name" \
  --body "Description of your changes"
```

### 代码规范

- **Python 版本**: 3.11+
- **代码风格**: PEP 8
- **最大行长**: 120 字符
- **类型提示**: 所有函数都应有类型提示
- **文档字符串**: 使用 Google 风格

### 测试要求

- 新功能必须包含测试
- 测试覆盖率 > 80%
- 所有测试必须通过

---

## 📚 分享实践案例

分享你的使用经验，帮助社区发掘 GTPlanner 的潜力。

### 案例类型

#### 1. 使用案例

分享真实项目中的应用：
- 项目背景和需求
- 如何使用 GTPlanner
- 生成的规划方案
- 实际效果和收益

#### 2. GTPlanner 生成的 PRD

展示 GTPlanner 的输出质量：
- 完整的 PRD 文档
- 使用的 Prefab 列表
- 规划的亮点

#### 3. 教程和最佳实践

帮助其他用户更好地使用：
- 特定场景的使用技巧
- 参数调优经验
- 常见问题解决方案

### 提交方式

1. 在 `docs/examples/community-cases/` 创建新文件

2. 文件命名格式：
   ```
   YYYY-MM-DD-case-title.md
   ```

3. 包含以下内容：
   ```markdown
   # 案例标题
   
   **作者**: Your Name
   **日期**: 2024-10-23
   **标签**: [GTPlanner, Prefab, 实践案例]
   
   ## 背景
   ...
   
   ## 使用 GTPlanner
   ...
   
   ## 生成的规划
   ...
   
   ## 效果和收益
   ...
   ```

4. 提交 PR

---

## 📝 文档贡献

帮助改进文档：

### 文档类型

- 📖 **用户指南**: 使用教程、最佳实践
- 🔧 **技术文档**: API 文档、架构说明
- 🌍 **翻译**: 其他语言版本
- 💡 **示例**: 代码示例、配置示例

### 文档规范

- 使用简洁清晰的语言
- 包含代码示例
- 添加必要的截图
- 保持格式一致

---

## ❓ 提问和讨论

### GitHub Issues

- 🐛 **Bug 报告**: 使用 Bug Report 模板
- 💡 **功能建议**: 使用 Feature Request 模板
- 🧩 **Prefab 提交**: 使用 Prefab Submission 模板

### GitHub Discussions

- 💬 一般性讨论
- 🤔 使用问题
- 💡 想法交流

---

## 🎯 贡献优先级

### 高优先级（最有价值）

1. **🧩 贡献 Prefab** - 直接扩展 GTPlanner 能力
2. **📝 分享 PRD 案例** - 展示真实效果
3. **🐛 修复 Bug** - 提高稳定性

### 中优先级

4. **📖 改进文档** - 降低使用门槛
5. **✨ 新功能** - 增强功能
6. **🌍 翻译** - 支持更多语言

### 低优先级

7. **♻️ 代码重构** - 需要充分理由
8. **🎨 样式调整** - 非关键性改进

---

## 📋 Pull Request 检查清单

提交 PR 前确认：

- [ ] 代码遵循项目规范
- [ ] 所有测试通过
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] Commit 信息清晰
- [ ] PR 描述详细

---

## 🙏 行为准则

- 尊重所有贡献者
- 保持友好和专业
- 接受建设性反馈
- 帮助新贡献者

---

## 🔗 相关资源

- [Prefab 贡献指南](../../prefabs/releases/CONTRIBUTING.md)
- [Prefab 模板](https://github.com/The-Agent-Builder/Prefab-Template)
- [GitHub Issues](https://github.com/OpenSQZ/GTPlanner/issues)
- [GitHub Discussions](https://github.com/OpenSQZ/GTPlanner/discussions)

---

<p align="center">
  感谢你的贡献！🎉
</p>
