# 文档索引 (Documentation Index)

> 快速找到你需要的文档

## 🎯 按角色导航

### 👨‍💻 贡献者（Prefab 作者）
如果你想发布自己的预制件：

1. **快速入门** → [QUICKSTART.md](QUICKSTART.md)
   - 5 分钟快速发布指南
   
2. **详细指南** → [CONTRIBUTING.md](CONTRIBUTING.md)
   - 完整的贡献流程
   - 编写规范和最佳实践
   - 故障排除
   
3. **模板文档** → [Prefab-Template](https://github.com/The-Agent-Builder/Prefab-Template)
   - 如何开发预制件

### 👀 维护者（审核者）
如果你负责审核和管理 PR：

1. **仓库设置** → [SETUP.md](SETUP.md)
   - 初始化配置
   - GitHub 设置
   - 被动同步说明
   
2. **安全政策** → [SECURITY.md](SECURITY.md)
   - 安全审核清单
   - 漏洞报告流程
   
3. **维护指南** → [CONTRIBUTING.md](CONTRIBUTING.md) - 审核流程部分

### 🔍 用户（使用者）
如果你想了解或使用预制件：

1. **项目概述** → [README.md](README.md)
   - 项目介绍
   - 功能特性
   - 统计信息
   
2. **贡献者列表** → [CONTRIBUTORS.md](CONTRIBUTORS.md)
   - 查看所有贡献者

## 📚 按主题导航

### 入门指南
- [README.md](README.md) - 项目主文档
- [QUICKSTART.md](QUICKSTART.md) - 快速开始
- [prd.md](prd.md) - 产品需求文档
- [demand.md](demand.md) - 功能需求文档

### 贡献相关
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南
- [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) - PR 模板
- [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/) - Issue 模板

### 技术文档
- [schema.json](schema.json) - JSON Schema 定义
- [scripts/](scripts/) - 自动化脚本
- [.github/workflows/](.github/workflows/) - CI/CD 工作流

### 安全和政策
- [SECURITY.md](SECURITY.md) - 安全政策
- [LICENSE](LICENSE) - 开源许可证

### 历史和更新
- [CHANGELOG.md](CHANGELOG.md) - 变更日志
- [CONTRIBUTORS.md](CONTRIBUTORS.md) - 贡献者名单

### 运维文档
- [SETUP.md](SETUP.md) - 仓库初始化
- [.github/workflows/](.github/workflows/) - 自动化流程

## 🗂️ 文件组织

```
prefab-releases/
├── 📄 核心数据文件
│   ├── community-prefabs.json    # 中央索引（核心）
│   └── schema.json                # JSON Schema 定义
│
├── 📖 用户文档
│   ├── README.md                  # 主文档
│   ├── QUICKSTART.md             # 快速开始
│   ├── CONTRIBUTING.md           # 贡献指南
│   ├── SECURITY.md               # 安全政策
│   └── DOCS_INDEX.md             # 本文档
│
├── 📋 项目文档
│   ├── prd.md                     # 产品需求
│   ├── demand.md                  # 功能需求
│   ├── CHANGELOG.md              # 变更日志
│   └── CONTRIBUTORS.md           # 贡献者
│
├── ⚙️ 配置文件
│   ├── pyproject.toml            # uv 依赖配置
│   ├── LICENSE                    # 许可证
│   ├── .gitignore                # Git 忽略
│   └── .editorconfig             # 编辑器配置
│
├── 🔧 脚本目录 (scripts/)
│   ├── extract_pr_changes.py     # 提取 PR 变更
│   ├── validate_schema.py        # Schema 验证
│   ├── check_artifact_url.py     # URL 检查
│   ├── verify_artifact.py        # 构件验证
│   ├── check_duplicates.py       # 重复检查
│   └── local_validate.py         # 本地验证工具
│
└── 🤖 GitHub 配置 (.github/)
    ├── PULL_REQUEST_TEMPLATE.md  # PR 模板
    ├── ISSUE_TEMPLATE/           # Issue 模板
    │   ├── bug_report.md
    │   └── feature_request.md
    ├── workflows/                # CI/CD 工作流
    │   ├── pr-check.yml          # PR 检查
    │   └── validate-index.yml    # 索引验证
    └── dependabot.yml            # 依赖更新
```

## 🔍 常见问题速查

| 问题 | 查看文档 | 章节 |
|------|----------|------|
| 如何发布预制件？ | [QUICKSTART.md](QUICKSTART.md) | 全部 |
| PR 检查失败？ | [CONTRIBUTING.md](CONTRIBUTING.md) | 故障排除 |
| 索引文件格式？ | [README.md](README.md) | 索引文件规范 |
| 安全问题报告？ | [SECURITY.md](SECURITY.md) | 报告流程 |
| 如何初始化仓库？ | [SETUP.md](SETUP.md) | 全部 |
| 更新预制件版本？ | [CONTRIBUTING.md](CONTRIBUTING.md) | 版本管理 |
| 自动化流程说明？ | [README.md](README.md) | 自动化流程 |

## 🔗 外部资源

- [Prefab-Template](https://github.com/The-Agent-Builder/Prefab-Template) - 预制件开发模板
- [项目官网](https://your-website.com) - 官方文档站点

## 📞 获取帮助

- 🐛 **Bug 报告**: [GitHub Issues](https://github.com/The-Agent-Builder/Prefab-Releases/issues)
- 💬 **讨论交流**: [GitHub Discussions](https://github.com/The-Agent-Builder/Prefab-Releases/discussions)
- 📧 **邮件联系**: maintainers@example.com

---

**提示**: 建议从 [QUICKSTART.md](QUICKSTART.md) 或 [README.md](README.md) 开始阅读。

