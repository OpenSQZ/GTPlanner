# Changelog

本文档记录所有重要的变更和更新。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划中
- 自动化安全扫描
- 预制件使用统计
- 评分和评论系统

## [1.0.0] - 2024-01-XX

### 新增
- 🎉 初始版本发布
- ✅ 中央索引文件 `community-prefabs.json`
- ✅ JSON Schema 验证
- ✅ PR 自动化校验流程
- ✅ 被动同步机制（部署服务轮询）
- ✅ 完整的文档系统
- ✅ 贡献指南和模板
- ✅ 本地验证工具
- ✅ 使用 uv 管理依赖

### 特性
- **自动化验证**：JSON 格式、Schema、URL 可达性、构件内容一致性
- **安全审核**：人工代码审核机制
- **标准化流程**：PR 模板和清单
- **可扩展性**：支持持续添加新预制件

### 脚本
- `scripts/extract_pr_changes.py` - 提取 PR 变更
- `scripts/validate_schema.py` - Schema 验证
- `scripts/check_artifact_url.py` - URL 可达性检查
- `scripts/verify_artifact.py` - 构件内容验证
- `scripts/check_duplicates.py` - 重复检查
- `scripts/local_validate.py` - 本地验证工具

### 文档
- `README.md` - 主文档
- `CONTRIBUTING.md` - 贡献指南
- `CHANGELOG.md` - 变更日志
- `SECURITY.md` - 安全政策

## [0.1.0] - 2024-01-XX

### 新增
- 项目初始化
- 基础仓库结构
- PRD 和需求文档

---

**注意**: 本仓库的版本号代表仓库基础设施的版本，与预制件版本独立。

