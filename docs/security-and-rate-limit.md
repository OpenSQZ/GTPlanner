# 安全与限流配置指南

## 概述
本指南介绍如何为 GTPlanner 启用 API Key 鉴权与进程内滑动窗口限流，并说明相关配置项与运维建议。

## 配置项

- `security.enable_api_key_auth` (bool, 默认 false): 是否启用 API Key 鉴权。
- `security.api_keys` (list 或 map):
  - 列表形式：`["key1", "key2"]`，租户 ID 默认为 `default`。
  - 映射形式：`{"key1" = "tenantA", "key2" = "tenantB"}`，可区分多租户。
- `rate_limit.enabled` (bool, 默认 false): 是否启用限流。
- `rate_limit.window_seconds` (int): 滑动时间窗（秒）。
- `rate_limit.max_requests` (int): 时间窗内允许的最大请求数。
- `rate_limit.per_tenant` (bool, 默认 true): 是否按租户维度限流（基于 API Key）。
- `sse.idle_timeout_seconds` (int, 默认 120): SSE 空闲超时时间，超时后主动关闭连接。

以上配置可在 `settings.toml` 中设置，或通过环境变量覆盖（优先级更高，前缀 `GTPLANNER_`）。

### 环境变量示例（Windows PowerShell）
```powershell
$env:GTPLANNER_SECURITY_ENABLE_API_KEY_AUTH="true"
$env:GTPLANNER_SECURITY_API_KEYS='["tenantA-xxxx","tenantB-yyyy"]'
$env:GTPLANNER_RATE_LIMIT_ENABLED="true"
$env:GTPLANNER_RATE_LIMIT_WINDOW_SECONDS="60"
$env:GTPLANNER_RATE_LIMIT_MAX_REQUESTS="120"
$env:GTPLANNER_RATE_LIMIT_PER_TENANT="true"
$env:GTPLANNER_SSE_IDLE_TIMEOUT_SECONDS="120"
```

## 路由保护范围
- 受保护：`POST /api/chat/agent`
- 公开：`GET /health`、`GET /api/status`

## 状态与健康检查
- `GET /health`：返回鉴权与限流开关、工具索引状态、LLM 配置探针。
- `GET /api/status`：返回 SSE 配置、限流配置与最近拒绝计数（1/5/15 分钟桶累计值）。

## 运维建议
- 单实例或开发环境可使用内存限流（当前实现）。
- 多副本部署建议采用外置存储（如 Redis）实现分布式限流；本项目保留内存实现作为默认，不强依赖外部基础设施。
- 建议为 API Key 配置不同配额以区分租户/环境（生产、预发、测试）。
