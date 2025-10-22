### **PRD: 预制件发布仓库 (`prefab-releases`)**

**版本:** 2.0 (深度工程实现版)
**负责人:** [平台生态团队]

#### **1. 概述 (Overview)**
*   **使命:** 作为一个纯元数据 Git 仓库，它通过标准化的 Pull Request (PR) 流程，接收、验证并索引所有社区贡献的预制件。它是触发自动化部署流程的唯一入口，也是 AI 进行 RAG 发现的权威数据源。
*   **技术栈:** GitHub Actions (YAML), Python/Shell scripting (for CI), JSON Schema。
*   **核心原则:** 结构化数据、自动化校验、人工审核兜底。

---

#### **2. 仓库文件结构与核心组件**

*   **`community-prefabs.json`:**
    *   **描述:** 权威的中央索引文件，是一个根为 JSON 数组的文本文件。
    *   **对象 Schema:**
        ```json
{
  "id": "video-to-audio-v1",
  "version": "1.1.0",
  "author": "github-username",
  "repo_url": "https://github.com/github-username/my-prefab-repo",
  "artifact_url": "https://.../prefab-video-to-audio-1.1.0.whl",
  "name": "视频转音频转换器",
  "description": "一个高性能的预制件...",
  "tags": ["video", "audio", "ffmpeg"]
}
        ```
    *   **所有权:** 文件的 `main` 分支版本由平台维护者全权控制。社区贡献者只能通过 PR 提出修改建议。

*   **`.github/PULL_REQUEST_TEMPLATE.md`:**
    *   **描述:** 当贡献者创建 PR 时自动填充的模板。
    *   **内容:**
        ```markdown
        ---
        name: "🚀 Publish New Prefab Version"
        title: "feat(publish): <prefab-id>@<version>"
        ---
        
        ### Prefab Information
        
        - **Prefab ID:** `[your-prefab-id]`
        - **Version:** `[your-prefab-version]`
        
        ### Submission Checklist
        
        Please verify the following before submitting your pull request.
        
        - [ ] The `id` and `version` in my submission match the information above.
        - [ ] The `artifact_url` points to a valid `.whl` file attached to a public GitHub Release in my repository.
        - [ ] My `prefab-manifest.json` is valid and correctly describes my prefab's functions.
        - [ ] I have read and agree to the Contributor License Agreement.
        
        ### Description
        
        (Optional) Provide a brief description of the changes in this version.
        ```

*   **`.github/workflows/pr-check.yml`:**
    *   **描述:** 核心的自动化 PR 校验流水线。

---

#### **3. 功能性需求 (FR)**

**FR-1: 中央索引文件 (`community-prefabs.json`) 规范**
*   **Schema (JSON Schema):** 必须在仓库中提供一份 `schema.json` 文件，用于校验 `community-prefabs.json` 的结构。
*   **对象模型 (Pydantic-like):**
    ```python
    class PrefabIndexEntry(BaseModel):
        id: str
        version: constr(pattern=r'^\d+\.\d+\.\d+$') # Semantic Versioning
        author: str
        repo_url: HttpUrl
        artifact_url: HttpUrl
        name: str
        description: str
        tags: List[str] = []
    ```
*   **唯一性约束:** `(id, version)` 的组合在整个 JSON 数组中必须是唯一的。

**FR-2: 自动化 PR 校验 (`pr-check.yml`)**
*   **触发条件:** `on: pull_request: types: [opened, synchronize, reopened]`
*   **Job 1: `validate-pr` (核心校验逻辑)**
    *   **环境:** `ubuntu-latest`, Python 3.11, `curl`, `unzip`, `jq`
    *   **核心步骤:**
        1.  **Checkout & Diff:**
            *   `actions/checkout@v4` with `fetch-depth: 0`
            *   使用 `git diff --name-only origin/main...HEAD` 校验，确保只有 `community-prefabs.json` 被修改。
        2.  **提取变更内容:**
            *   使用 `jq` 和 `git diff` 结合，精确地提取出 PR 中新增或修改的那个 JSON 对象，存入一个临时文件 `changed_entry.json`。
        3.  **Schema 校验:**
            *   使用 JSON Schema 校验工具 (如 `jsonschema` in Python) 验证 `changed_entry.json` 符合规范。
        4.  **链接可达性校验:**
            *   `artifact_url = $(jq -r .artifact_url changed_entry.json)`
            *   `curl --silent --fail --location --head "$artifact_url"`: 校验 URL 是否返回 200-299 状态码。
        5.  **构件内容完整性校验 (The Deep Dive):**
            *   **下载:** `curl --silent --fail --location -o artifact.whl "$artifact_url"`
            *   **创建临时目录:** `mkdir temp_whl && cd temp_whl`
            *   **解压:** `unzip ../artifact.whl`
            *   **查找 Manifest:** 检查 `prefab-manifest.json` 是否存在于解压后的目录结构中。
            *   **内容一致性断言:**
                *   `manifest_id = $(jq -r .id prefab-manifest.json)`
                *   `manifest_version = $(jq -r .version prefab-manifest.json)`
                *   `pr_id = $(jq -r .id ../changed_entry.json)`
                *   `pr_version = $(jq -r .version ../changed_entry.json)`
                *   断言 `manifest_id` == `pr_id` 并且 `manifest_version` == `pr_version`。
*   **成功/失败:**
    *   如果所有步骤通过，Action 成功，PR 显示绿色的对勾。
    *   任何一步失败，Action 必须使用 `exit 1` 失败，并通过 `echo "::error::Error message"` 在 PR 页面留下清晰、可操作的错误注解。

**FR-3: 合并后 Webhook 触发**
*   **配置:** 在 GitHub 仓库的 `Settings > Webhooks` 中，配置一个新的 Webhook。
*   **Payload URL:** 指向 `prefab-factory` 服务的 `POST /v1/deploy` 端点。
*   **Content type:** `application/json`
*   **Secret:** 设置一个强壮的、随机的 Secret Token，用于 `prefab-factory` 进行签名验证。
*   **Events:** 只订阅 `push` 事件。
*   **Webhook 载荷过滤器 (可选但推荐):** GitHub Actions 可以被配置为在 `main` 分支有 push 时触发，然后一个 Action 步骤负责检查 commit 内容，仅当 `community-prefabs.json` 发生变更时，才向 `prefab-factory` 发送 Webhook。这可以防止不相关的 `main` 分支更新（如修改 README）触发不必要的部署。
    *   **Action 逻辑:**
        1.  `on: push: branches: [main]`
        2.  `actions/checkout@v4` with `fetch-depth: 2`
        3.  `git diff --name-only HEAD^ HEAD | grep "community-prefabs.json"`: 如果此命令成功，则继续。
        4.  提取变更内容，构造 `DeployRequestPayload`，并使用 `curl` 发送到 `prefab-factory`。

---

#### **4. 平台维护者工作流 (Maintainer's Workflow)**

1.  **接收通知:** 收到一个新的 PR 通知。
2.  **检查自动化校验:** 查看 `pr-check.yml` Action 是否已成功通过。如果失败，要求贡献者修复。
3.  **人工审核 (核心安全关卡):**
    *   **代码抽样:** 访问 PR 中提供的 `repo_url`，大致浏览一下 `src/main.py` 的代码，检查是否有明显的恶意行为（如 `os.system`, `eval`）、无限循环或不合理的资源消耗。
    *   **信誉检查:** 检查贡献者 (`author`) 的 GitHub 个人资料，判断其是否可信。
4.  **合并:** 如果一切看起来正常，点击 "Merge Pull Request"。
5.  **监控:** 在内部监控频道查看 `prefab-factory` 的部署通知，确保部署成功。

