# 预制件索引构建模式重构

## 概述

将预制件索引构建模式从"运行时动态管理"改为"CI/CD 集中构建"，简化架构并提高可靠性。

## 变更日期

2025-11-25

## 变更内容

### 1. 删除的文件

- `gtplanner/agent/utils/prefab_index_manager.py` - 运行时索引管理器（已删除）

### 2. 修改的文件

#### `gtplanner/agent/utils/startup_init.py`

**变更：**
- 移除了 `prefab_index_manager` 的导入和依赖
- 移除了 `_preload_prefab_index()` 函数
- 修改 `initialize_application()` 默认参数 `preload_index=False`
- 简化 `get_application_status()` 直接从配置读取索引名称
- 简化 `ensure_application_ready()` 移除索引检查逻辑

**新行为：**
- 启动时不再预加载或构建索引
- 只进行基本的环境检查（API Key、向量服务配置）

#### `gtplanner/agent/function_calling/agent_tools.py`

**变更：**
- 移除了 `ensure_prefab_index()` 的调用
- 直接从配置文件读取索引名称

**新代码：**
```python
# 从配置获取索引名称
from gtplanner.utils.config_manager import get_vector_service_config
vector_config = get_vector_service_config()
index_name = vector_config.get("prefabs_index_name", "document_gtplanner_prefabs")
```

#### `prefabs/releases/scripts/README.md`

**变更：**
- 更新了运行时行为说明
- 移除了 `PrefabIndexManager` 相关文档
- 更新了索引构建策略说明
- 添加了 v2.0 版本历史

### 3. 保留的文件

以下文件保持不变，继续用于索引构建：

- `prefabs/releases/scripts/build_index.py` - CI/CD 和手动索引构建脚本
- `gtplanner/agent/utils/prefab_indexer.py` - 底层索引构建器
- `.github/workflows/prefab-deploy-webhook.yml` - CI/CD 工作流

## 新的索引构建流程

### 1. CI/CD 自动构建（推荐）

**触发条件：**
- PR 合并到 main 分支
- 修改了 `prefabs/releases/community-prefabs.json`

**工作流：**
```yaml
# .github/workflows/prefab-deploy-webhook.yml
jobs:
  build-index:
    runs-on: ubuntu-latest
    steps:
      - name: Build prefab index
        run: |
          python3 prefabs/releases/scripts/build_index.py \
            --vector-service-url "$VECTOR_SERVICE_URL" \
            --input prefabs/releases/community-prefabs.json
```

### 2. 手动构建

```bash
# 切换到项目根目录
cd /path/to/GTPlanner

# 运行索引构建脚本
python3 prefabs/releases/scripts/build_index.py \
  --vector-service-url "http://your-vector-service" \
  --input prefabs/releases/community-prefabs.json
```

### 3. 运行时行为

**启动时：**
- ✅ 检查 AGENT_BUILDER_API_KEY
- ✅ 检查向量服务配置
- ❌ 不构建索引
- ❌ 不预加载索引

**使用索引时：**
```python
from gtplanner.utils.config_manager import get_vector_service_config

# 直接从配置读取索引名称
vector_config = get_vector_service_config()
index_name = vector_config.get("prefabs_index_name", "document_gtplanner_prefabs")
```

## 优势

### 1. 简化架构
- 移除了复杂的运行时索引管理逻辑
- 减少了代码维护负担
- 降低了出错可能性

### 2. 提高可靠性
- 索引构建在 CI/CD 中集中管理
- 失败时可以及时发现并修复
- 避免了运行时构建的不确定性

### 3. 加快启动速度
- 项目启动不再需要检查索引状态
- 不需要等待索引构建完成
- 减少了启动时的 I/O 操作

### 4. 统一管理
- 所有环境使用相同的索引构建流程
- CI/CD 日志清晰记录索引构建历史
- 便于追踪和调试

## 迁移指南

### 对于开发者

**之前：**
```python
# 旧代码会自动构建索引
from gtplanner.agent.utils.prefab_index_manager import ensure_prefab_index
index_name = await ensure_prefab_index()
```

**现在：**
```python
# 新代码直接读取配置
from gtplanner.utils.config_manager import get_vector_service_config
vector_config = get_vector_service_config()
index_name = vector_config.get("prefabs_index_name", "document_gtplanner_prefabs")
```

### 对于运维

**索引更新流程：**
1. 修改 `prefabs/releases/community-prefabs.json`
2. 提交 PR 并合并到 main 分支
3. GitHub Actions 自动构建索引
4. 检查 Actions 日志确认构建成功

**手动重建索引：**
```bash
# 使用构建脚本
python3 prefabs/releases/scripts/build_index.py \
  --vector-service-url "$VECTOR_SERVICE_URL"
```

## 配置要求

### GitHub Secrets

需要在 GitHub 仓库中配置以下 Secret：

- `VECTOR_SERVICE_URL`: 向量服务地址（例如：`http://your-vector-service:8000`）

### 本地配置

`gtplanner/config.yaml`:
```yaml
vector_service:
  base_url: "http://localhost:8000"  # 向量服务地址
  prefabs_index_name: "document_gtplanner_prefabs"  # 索引名称
```

## 故障排查

### 索引构建失败

**问题：** CI/CD 中索引构建失败

**解决方案：**
1. 检查 GitHub Actions 日志
2. 验证 `VECTOR_SERVICE_URL` Secret 是否正确配置
3. 确认向量服务可访问：`curl http://your-vector-service/health`
4. 验证 JSON 格式：`python3 -m json.tool prefabs/releases/community-prefabs.json`

### 索引数据不是最新

**问题：** 更新了 JSON 但搜索结果未更新

**解决方案：**
1. 检查 GitHub Actions 运行记录
2. 确认 "Build Prefab Index" job 是否成功
3. 手动触发 workflow 重建索引

## 相关链接

- [索引构建脚本](prefabs/releases/scripts/build_index.py)
- [CI/CD 工作流](.github/workflows/prefab-deploy-webhook.yml)
- [索引构建文档](prefabs/releases/scripts/README.md)

## 版本历史

- **v2.0** (2025-11-25): 重构为 CI/CD 集中构建模式
- **v1.0** (2025-11-24): 初始版本，支持运行时动态管理
