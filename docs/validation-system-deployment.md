# GTPlanner 请求验证系统部署指南

## 📋 目录

1. [部署概览](#部署概览)
2. [环境准备](#环境准备)
3. [配置管理](#配置管理)
4. [部署步骤](#部署步骤)
5. [性能调优](#性能调优)
6. [监控配置](#监控配置)
7. [安全配置](#安全配置)
8. [故障排除](#故障排除)

---

## 🎯 部署概览

GTPlanner请求验证系统支持多种部署模式：

- **单机部署**: 适用于开发和小规模测试
- **容器化部署**: 使用Docker的标准化部署
- **微服务部署**: 与现有GTPlanner服务集成
- **云原生部署**: 支持Kubernetes等容器编排

### 系统要求

**最低要求:**
- Python 3.8+
- 内存: 512MB
- CPU: 1核心
- 磁盘: 100MB

**推荐配置:**
- Python 3.11+
- 内存: 2GB
- CPU: 2核心
- 磁盘: 1GB

**生产环境:**
- Python 3.11+
- 内存: 4GB+
- CPU: 4核心+
- 磁盘: 10GB+

---

## 🔧 环境准备

### 1. Python环境

```bash
# 创建虚拟环境
python -m venv gtplanner_validation_env

# 激活虚拟环境
# Windows
gtplanner_validation_env\Scripts\activate
# Linux/Mac
source gtplanner_validation_env/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 依赖包

创建 `requirements.txt`:

```txt
# 核心依赖
fastapi>=0.100.0
uvicorn>=0.20.0
pydantic>=2.0.0
dynaconf>=3.1.0

# 可选依赖
redis>=4.0.0          # Redis缓存支持
psutil>=5.9.0         # 系统监控
aiofiles>=23.0.0      # 异步文件操作

# 开发依赖
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
```

### 3. 目录结构

```
GTPlanner/
├── agent/
│   └── validation/          # 验证系统
├── settings.toml           # 配置文件
├── fastapi_main.py        # FastAPI应用
├── requirements.txt       # 依赖列表
├── logs/                  # 日志目录
├── cache/                 # 缓存目录
└── docs/                  # 文档目录
```

---

## ⚙️ 配置管理

### 1. 分环境配置

#### 开发环境 (settings.dev.toml)

```toml
[default.validation]
enabled = true
mode = "lenient"
enable_parallel_validation = false
enable_caching = false

[default.validation.logging]
level = "DEBUG"
console_enabled = true
log_successful_validations = true

[default.validation.error_handling]
mask_sensitive_data = false
include_stack_trace = true
```

#### 测试环境 (settings.test.toml)

```toml
[default.validation]
enabled = true
mode = "strict"
enable_parallel_validation = true
enable_caching = true

[default.validation.logging]
level = "INFO"
console_enabled = false
log_successful_validations = false

[default.validation.error_handling]
mask_sensitive_data = true
include_stack_trace = false
```

#### 生产环境 (settings.prod.toml)

```toml
[default.validation]
enabled = true
mode = "strict"
enable_parallel_validation = true
enable_caching = true
enable_metrics = true

[default.validation.logging]
level = "WARNING"
console_enabled = false
log_successful_validations = false

[default.validation.error_handling]
mask_sensitive_data = true
include_stack_trace = false
max_error_message_length = 200

[default.validation.cache]
backend = "redis"  # 生产环境使用Redis
max_size = 10000
default_ttl = 600
```

### 2. 环境变量配置

```bash
# 生产环境变量
export ENV_FOR_DYNACONF=production
export GTPLANNER_VALIDATION_ENABLED=true
export GTPLANNER_VALIDATION_MODE=strict
export GTPLANNER_VALIDATION_MAX_REQUEST_SIZE=1048576
export GTPLANNER_VALIDATION_REQUESTS_PER_MINUTE=60

# Redis配置（如果使用）
export REDIS_URL=redis://localhost:6379/0

# 日志配置
export GTPLANNER_LOGGING_LEVEL=INFO
export GTPLANNER_LOGGING_FILE_ENABLED=true
export GTPLANNER_LOGGING_CONSOLE_ENABLED=false
```

---

## 🚀 部署步骤

### 1. 单机部署

```bash
# 1. 克隆代码
git clone <repository_url>
cd GTPlanner

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
cp settings.toml settings.local.toml
# 编辑 settings.local.toml

# 4. 启动服务
python fastapi_main.py
```

### 2. Docker部署

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs cache

# 设置环境变量
ENV ENV_FOR_DYNACONF=production
ENV GTPLANNER_VALIDATION_ENABLED=true

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "fastapi_main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  gtplanner:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV_FOR_DYNACONF=production
      - GTPLANNER_VALIDATION_ENABLED=true
      - GTPLANNER_VALIDATION_MODE=strict
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./logs:/app/logs
      - ./cache:/app/cache
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

#### 部署命令

```bash
# 构建和启动
docker-compose up -d

# 查看日志
docker-compose logs -f gtplanner

# 健康检查
curl http://localhost:8000/health
curl http://localhost:8000/api/validation/status
```

### 3. Kubernetes部署

#### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gtplanner-validation
  labels:
    app: gtplanner-validation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gtplanner-validation
  template:
    metadata:
      labels:
        app: gtplanner-validation
    spec:
      containers:
      - name: gtplanner
        image: gtplanner:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENV_FOR_DYNACONF
          value: "production"
        - name: GTPLANNER_VALIDATION_ENABLED
          value: "true"
        - name: GTPLANNER_VALIDATION_MODE
          value: "strict"
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/validation/status
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: gtplanner-validation-service
spec:
  selector:
    app: gtplanner-validation
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
```

---

## 📊 监控配置

### 1. 应用监控

#### Prometheus指标导出

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# 定义指标
validation_requests_total = Counter('validation_requests_total', 
                                   'Total validation requests', 
                                   ['endpoint', 'status'])

validation_duration_seconds = Histogram('validation_duration_seconds',
                                       'Validation duration in seconds',
                                       ['validator'])

validation_errors_total = Counter('validation_errors_total',
                                 'Total validation errors',
                                 ['error_code', 'validator'])

@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    return Response(generate_latest(), media_type="text/plain")

# 在观察者中更新指标
class PrometheusMetricsObserver(IValidationObserver):
    async def on_validation_complete(self, result: ValidationResult):
        validation_requests_total.labels(
            endpoint=result.metadata.get('endpoint', 'unknown'),
            status=result.status.value
        ).inc()
        
        validation_duration_seconds.observe(result.execution_time)
        
        for error in result.errors:
            validation_errors_total.labels(
                error_code=error.code,
                validator=error.validator or 'unknown'
            ).inc()
```

### 2. 日志聚合

#### ELK Stack集成

```python
import logging
from pythonjsonlogger import jsonlogger

# 配置JSON日志格式
json_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)
json_handler.setFormatter(formatter)

logger = logging.getLogger("validation")
logger.addHandler(json_handler)
logger.setLevel(logging.INFO)
```

#### Logstash配置

```ruby
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "gtplanner-validation" {
    json {
      source => "message"
    }
    
    # 解析验证事件
    if [validation_event] {
      mutate {
        add_tag => ["validation"]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "gtplanner-validation-%{+YYYY.MM.dd}"
  }
}
```

### 3. 健康检查

```python
@app.get("/health")
async def health_check():
    """详细的健康检查"""
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "components": {}
    }
    
    # 检查验证系统状态
    try:
        from agent.validation.factories.config_factory import ConfigFactory
        config_factory = ConfigFactory()
        config = config_factory.create_from_template("standard")
        
        health_status["components"]["validation_config"] = {
            "status": "healthy",
            "enabled": config.get("enabled", False)
        }
    except Exception as e:
        health_status["components"]["validation_config"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # 检查缓存状态
    try:
        from agent.validation.utils.cache_manager import ValidationCacheManager
        cache_manager = ValidationCacheManager()
        cache_stats = await cache_manager.get_stats()
        
        health_status["components"]["cache"] = {
            "status": "healthy",
            "stats": cache_stats
        }
    except Exception as e:
        health_status["components"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # 检查注册表状态
    try:
        from agent.validation.core.validation_registry import get_global_registry
        registry = get_global_registry()
        registry_stats = registry.get_registry_stats()
        
        health_status["components"]["registry"] = {
            "status": "healthy",
            "validators": registry_stats["total_registered_validators"]
        }
    except Exception as e:
        health_status["components"]["registry"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
    
    # 确定总体状态
    component_statuses = [comp["status"] for comp in health_status["components"].values()]
    if all(status == "healthy" for status in component_statuses):
        health_status["status"] = "healthy"
    elif any(status == "unhealthy" for status in component_statuses):
        health_status["status"] = "degraded"
    else:
        health_status["status"] = "unknown"
    
    return health_status
```

---

## 🔧 配置管理

### 1. 配置文件层次

```
配置优先级（从高到低）:
1. 环境变量 (GTPLANNER_*)
2. 本地配置文件 (settings.local.toml)
3. 环境配置文件 (settings.prod.toml)
4. 主配置文件 (settings.toml)
5. 默认值
```

### 2. 生产环境配置

#### settings.prod.toml

```toml
[default.validation]
enabled = true
mode = "strict"
max_request_size = 1048576
enable_rate_limiting = true
requests_per_minute = 60
enable_caching = true
cache_ttl = 300
enable_metrics = true
enable_parallel_validation = true

# 生产环境验证器配置
[[default.validation.validators]]
name = "security"
type = "security"
enabled = true
priority = "critical"
[default.validation.validators.config]
enable_xss_protection = true
enable_sql_injection_detection = true
enable_sensitive_data_detection = true
enable_script_detection = true

[[default.validation.validators]]
name = "rate_limit"
type = "rate_limit"
enabled = true
priority = "high"
[default.validation.validators.config]
requests_per_minute = 60
requests_per_hour = 1000
enable_ip_based_limiting = true
burst_size = 10

# 生产环境端点配置
[default.validation.endpoints]
"/api/chat/agent" = ["security", "rate_limit", "size", "format", "content", "language", "session"]
"/api/mcp/*" = ["security", "rate_limit", "format", "content"]
"/health" = ["size"]

# 缓存配置
[default.validation.cache]
enabled = true
backend = "redis"  # 生产环境使用Redis
default_ttl = 600
max_size = 10000

# 指标配置
[default.validation.metrics]
enabled = true
include_timing = true
include_success_rate = true
export_interval = 60

# 日志配置
[default.validation.logging]
enabled = true
level = "INFO"
file_enabled = true
console_enabled = false
include_request_details = false  # 生产环境关闭详细信息
log_successful_validations = false
log_failed_validations = true

# 错误处理配置
[default.validation.error_handling]
include_suggestions = true
include_error_codes = true
mask_sensitive_data = true
max_error_message_length = 200
```

### 3. 配置验证

部署前验证配置：

```python
from agent.validation.factories.config_factory import ConfigFactory

def validate_deployment_config():
    """验证部署配置"""
    config_factory = ConfigFactory()
    
    # 加载生产配置
    config = config_factory.create_from_env("production")
    
    # 验证配置
    validation_result = config_factory.validate_config(config)
    
    if not validation_result.is_valid:
        print("❌ 配置验证失败:")
        for error in validation_result.errors:
            print(f"  - {error}")
        return False
    
    if validation_result.warnings:
        print("⚠️ 配置警告:")
        for warning in validation_result.warnings:
            print(f"  - {warning}")
    
    print("✅ 配置验证通过")
    return True

# 部署前检查
if __name__ == "__main__":
    validate_deployment_config()
```

---

## 🚀 部署步骤

### 1. 标准部署流程

```bash
#!/bin/bash
# deploy.sh - 部署脚本

set -e

echo "🚀 开始部署GTPlanner验证系统..."

# 1. 环境检查
python --version
pip --version

# 2. 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt

# 3. 配置验证
echo "⚙️ 验证配置..."
python -c "
from agent.validation.factories.config_factory import ConfigFactory
factory = ConfigFactory()
config = factory.create_from_env('production')
result = factory.validate_config(config)
assert result.is_valid, f'配置无效: {result.errors}'
print('✅ 配置验证通过')
"

# 4. 数据库初始化（如果需要）
echo "🗄️ 初始化数据库..."
python -c "
from agent.persistence.create_database import create_database
create_database()
print('✅ 数据库初始化完成')
"

# 5. 预热验证器
echo "🔥 预热验证器..."
python -c "
import asyncio
from agent.validation.utils.performance_optimizer import get_global_optimizer
from agent.validation.factories.validator_factory import ValidatorFactory

async def prewarm():
    optimizer = get_global_optimizer()
    factory = ValidatorFactory()
    factory.register_default_validators()
    # await optimizer.prewarm_common_validators(factory.create_validator)
    print('✅ 验证器预热完成')

asyncio.run(prewarm())
"

# 6. 启动服务
echo "🚀 启动服务..."
uvicorn fastapi_main:app --host 0.0.0.0 --port 8000 --workers 4

echo "✅ 部署完成！"
```

### 2. 蓝绿部署

```bash
#!/bin/bash
# blue_green_deploy.sh

BLUE_PORT=8000
GREEN_PORT=8001
HEALTH_CHECK_URL="http://localhost"

echo "🔄 开始蓝绿部署..."

# 1. 启动绿色环境
echo "🟢 启动绿色环境..."
uvicorn fastapi_main:app --host 0.0.0.0 --port $GREEN_PORT &
GREEN_PID=$!

# 2. 等待绿色环境就绪
echo "⏳ 等待绿色环境就绪..."
for i in {1..30}; do
    if curl -f $HEALTH_CHECK_URL:$GREEN_PORT/health > /dev/null 2>&1; then
        echo "✅ 绿色环境就绪"
        break
    fi
    sleep 2
done

# 3. 健康检查
echo "🔍 绿色环境健康检查..."
if ! curl -f $HEALTH_CHECK_URL:$GREEN_PORT/api/validation/status > /dev/null 2>&1; then
    echo "❌ 绿色环境健康检查失败"
    kill $GREEN_PID
    exit 1
fi

# 4. 切换流量（这里需要负载均衡器配置）
echo "🔄 切换流量到绿色环境..."
# 更新负载均衡器配置...

# 5. 停止蓝色环境
echo "🔵 停止蓝色环境..."
# 停止蓝色环境进程...

echo "✅ 蓝绿部署完成！"
```

---

## ⚡ 性能调优

### 1. 验证性能优化

```python
# 高性能配置
performance_config = {
    "validation": {
        "enable_parallel_validation": True,
        "mode": "fail_fast",  # 快速失败
        "enable_caching": True
    },
    "cache": {
        "use_partitioned_cache": True,
        "partition_count": 32,  # 增加分区数
        "max_size": 5000,
        "default_ttl": 600
    },
    "concurrency": {
        "max_concurrent_validations": 200,
        "max_concurrent_per_validator": 20
    }
}

# 应用优化配置
from agent.validation.utils.performance_optimizer import get_global_optimizer
optimizer = get_global_optimizer()
optimizer.optimize_for_production()
```

### 2. 内存优化

```python
# 内存优化配置
memory_config = {
    "cache": {
        "max_size": 1000,      # 限制缓存大小
        "cleanup_interval": 30  # 频繁清理
    },
    "logging": {
        "max_content_length": 100,  # 限制日志内容长度
        "log_successful_validations": False
    },
    "metrics": {
        "max_history_size": 500  # 限制历史记录大小
    }
}
```

### 3. 数据库优化

```sql
-- 为验证相关表创建索引
CREATE INDEX idx_validation_logs_timestamp ON validation_logs(timestamp);
CREATE INDEX idx_validation_logs_status ON validation_logs(status);
CREATE INDEX idx_validation_logs_endpoint ON validation_logs(endpoint);

-- 定期清理旧数据
DELETE FROM validation_logs WHERE timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

---

## 🔒 安全配置

### 1. 生产环境安全设置

```toml
[default.validation]
# 严格安全模式
mode = "strict"

# 启用所有安全验证
[[default.validation.validators]]
name = "security"
[default.validation.validators.config]
enable_xss_protection = true
enable_sql_injection_detection = true
enable_sensitive_data_detection = true
enable_script_detection = true

# 严格的频率限制
[[default.validation.validators]]
name = "rate_limit"
[default.validation.validators.config]
requests_per_minute = 30    # 严格限制
burst_size = 5              # 小突发
enable_ip_based_limiting = true

# 安全的错误处理
[default.validation.error_handling]
mask_sensitive_data = true
include_stack_trace = false
max_error_message_length = 100
```

### 2. 网络安全

```python
# CORS安全配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 限制域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],             # 限制方法
    allow_headers=["Content-Type", "Authorization"],
)

# 安全头配置
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

### 3. 访问控制

```python
# IP白名单中间件
ALLOWED_IPS = ["192.168.1.0/24", "10.0.0.0/8"]

@app.middleware("http")
async def ip_whitelist(request: Request, call_next):
    client_ip = request.client.host
    
    if not is_ip_allowed(client_ip, ALLOWED_IPS):
        return JSONResponse(
            status_code=403,
            content={"error": "IP not allowed"}
        )
    
    return await call_next(request)
```

---

## 🚨 故障排除

### 1. 常见部署问题

#### 问题: 验证中间件不生效

**症状**: 请求没有被验证，直接通过

**排查步骤**:
```python
# 1. 检查中间件是否正确添加
print(app.middleware_stack)

# 2. 检查配置是否正确加载
from agent.validation.factories.config_factory import ConfigFactory
config = ConfigFactory().create_from_env()
print("验证启用:", config.get("enabled"))

# 3. 检查路径匹配
validation_middleware = ValidationMiddleware(app, config)
test_request = MockRequest("/api/test")
should_validate = validation_middleware._should_validate(test_request)
print("应该验证:", should_validate)
```

#### 问题: 内存泄漏

**症状**: 长时间运行后内存持续增长

**排查步骤**:
```python
# 1. 检查缓存大小
cache_stats = await cache_manager.get_stats()
print("缓存统计:", cache_stats)

# 2. 清理过期缓存
cleaned = await cache_manager.cleanup_expired()
print("清理过期项:", cleaned)

# 3. 检查观察者内存使用
metrics = metrics_observer.get_current_metrics()
print("指标历史大小:", len(metrics.get("validator_execution_counts", {})))

# 4. 重置指标（如果需要）
metrics_observer.reset_metrics()
```

#### 问题: 性能下降

**症状**: 验证执行时间逐渐增长

**排查步骤**:
```python
# 1. 检查验证器性能
for validator_name in metrics["validator_avg_times"]:
    performance = metrics_observer.get_validator_performance(validator_name)
    if performance["avg_execution_time"] > 0.1:
        print(f"⚠️ {validator_name} 性能下降: {performance}")

# 2. 检查缓存命中率
cache_rates = metrics["validator_cache_rates"]
for validator, rate in cache_rates.items():
    if rate < 0.5:
        print(f"⚠️ {validator} 缓存命中率低: {rate:.1%}")

# 3. 检查并发情况
concurrency_stats = optimizer.get_optimization_stats()["concurrency_stats"]
if concurrency_stats["active_validations"] > concurrency_stats["max_concurrent_validations"] * 0.8:
    print("⚠️ 并发度过高，考虑增加限制")
```

### 2. 日志分析

#### 验证失败日志分析

```bash
# 查看最近的验证失败
grep "验证失败" logs/gtplanner_*.log | tail -20

# 统计错误类型
grep "error_code" logs/gtplanner_*.log | \
    sed 's/.*"error_code": "\([^"]*\)".*/\1/' | \
    sort | uniq -c | sort -nr

# 查看性能问题
grep "execution_time" logs/gtplanner_*.log | \
    awk -F'"execution_time": ' '{print $2}' | \
    awk '{if($1>0.1) print "慢验证:", $1}'
```

#### 监控告警日志

```bash
# 查看告警历史
grep "ALERT" logs/gtplanner_*.log | tail -10

# 统计告警频率
grep "ALERT" logs/gtplanner_*.log | \
    awk '{print $1, $2}' | \
    uniq -c | sort -nr
```

---

## 📊 运维监控

### 1. 关键指标监控

```python
# 关键性能指标 (KPI)
kpi_thresholds = {
    "validation_success_rate": 0.95,      # 验证成功率 > 95%
    "avg_execution_time": 0.1,            # 平均执行时间 < 100ms
    "cache_hit_rate": 0.7,                # 缓存命中率 > 70%
    "error_rate": 0.05,                   # 错误率 < 5%
    "memory_usage": 2048,                 # 内存使用 < 2GB
    "concurrent_validations": 100          # 并发验证 < 100
}

# 监控脚本
def check_system_health():
    metrics = get_current_metrics()
    alerts = []
    
    for metric, threshold in kpi_thresholds.items():
        current_value = metrics.get(metric, 0)
        
        if metric in ["validation_success_rate", "cache_hit_rate"]:
            if current_value < threshold:
                alerts.append(f"{metric} 低于阈值: {current_value:.1%} < {threshold:.1%}")
        else:
            if current_value > threshold:
                alerts.append(f"{metric} 超过阈值: {current_value} > {threshold}")
    
    return alerts
```

### 2. 自动化运维

#### 自动重启脚本

```bash
#!/bin/bash
# auto_restart.sh

MAX_MEMORY_MB=2048
MAX_ERROR_RATE=0.1

while true; do
    # 检查内存使用
    MEMORY_USAGE=$(ps -o pid,rss,comm -p $(pgrep -f fastapi_main) | awk 'NR>1{print $2}')
    
    if [ "$MEMORY_USAGE" -gt "$MAX_MEMORY_MB" ]; then
        echo "⚠️ 内存使用过高: ${MEMORY_USAGE}MB，重启服务..."
        systemctl restart gtplanner
        sleep 30
    fi
    
    # 检查错误率
    ERROR_RATE=$(curl -s http://localhost:8000/api/validation/metrics | \
                jq '.overall_error_rate // 0')
    
    if (( $(echo "$ERROR_RATE > $MAX_ERROR_RATE" | bc -l) )); then
        echo "⚠️ 错误率过高: $ERROR_RATE，重启服务..."
        systemctl restart gtplanner
        sleep 30
    fi
    
    sleep 60
done
```

#### 自动清理脚本

```python
#!/usr/bin/env python3
# cleanup.py - 自动清理脚本

import asyncio
import time
from agent.validation.utils.cache_manager import ValidationCacheManager
from agent.validation.observers.metrics_observer import MetricsObserver

async def cleanup_validation_system():
    """清理验证系统"""
    
    print("🧹 开始清理验证系统...")
    
    # 1. 清理过期缓存
    cache_manager = ValidationCacheManager()
    expired_count = cache_manager.cache.cleanup_expired()
    print(f"✅ 清理过期缓存: {expired_count} 项")
    
    # 2. 重置指标（如果需要）
    metrics_observer = MetricsObserver()
    metrics = metrics_observer.get_current_metrics()
    
    # 如果运行时间超过24小时，重置指标
    if metrics.get("uptime_seconds", 0) > 86400:
        metrics_observer.reset_metrics()
        print("✅ 重置指标数据")
    
    # 3. 清理日志文件（保留最近7天）
    import os
    import glob
    from datetime import datetime, timedelta
    
    log_files = glob.glob("logs/gtplanner_*.log")
    cutoff_date = datetime.now() - timedelta(days=7)
    
    for log_file in log_files:
        file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        if file_time < cutoff_date:
            os.remove(log_file)
            print(f"✅ 删除旧日志: {log_file}")
    
    print("🎉 清理完成")

if __name__ == "__main__":
    asyncio.run(cleanup_validation_system())
```

---

## 🔧 生产环境优化

### 1. 系统级优化

```bash
# 系统参数优化
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
echo "fs.file-max = 100000" >> /etc/sysctl.conf
sysctl -p

# 进程限制优化
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf
```

### 2. 应用级优化

```python
# uvicorn生产配置
uvicorn fastapi_main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --max-requests 10000 \
    --max-requests-jitter 1000 \
    --timeout-keep-alive 65 \
    --access-log \
    --log-level info
```

### 3. 负载均衡配置

#### Nginx配置

```nginx
upstream gtplanner_validation {
    server 127.0.0.1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.gtplanner.com;
    
    # 验证相关的特殊配置
    client_max_body_size 2M;
    client_body_timeout 30s;
    client_header_timeout 30s;
    
    location /api/ {
        proxy_pass http://gtplanner_validation;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 验证系统特定头部
        proxy_set_header X-Request-ID $request_id;
        proxy_set_header X-Client-IP $remote_addr;
        
        # 超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://gtplanner_validation;
        access_log off;
    }
    
    # 验证状态（仅内网访问）
    location /api/validation/ {
        allow 192.168.1.0/24;
        allow 10.0.0.0/8;
        deny all;
        
        proxy_pass http://gtplanner_validation;
    }
}
```

---

## 📈 监控和告警

### 1. Grafana监控面板

```json
{
  "dashboard": {
    "title": "GTPlanner 验证系统监控",
    "panels": [
      {
        "title": "验证成功率",
        "type": "stat",
        "targets": [
          {
            "expr": "validation_success_rate",
            "legendFormat": "成功率"
          }
        ]
      },
      {
        "title": "验证执行时间",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, validation_duration_seconds_bucket)",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "错误类型分布",
        "type": "piechart",
        "targets": [
          {
            "expr": "validation_errors_total",
            "legendFormat": "{{error_code}}"
          }
        ]
      }
    ]
  }
}
```

### 2. 告警规则

```yaml
# alerting_rules.yml
groups:
- name: gtplanner_validation
  rules:
  - alert: ValidationSuccessRateLow
    expr: validation_success_rate < 0.95
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "验证成功率过低"
      description: "验证成功率 {{ $value }} 低于95%"

  - alert: ValidationLatencyHigh
    expr: histogram_quantile(0.95, validation_duration_seconds_bucket) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "验证延迟过高"
      description: "95%验证延迟 {{ $value }}s 超过100ms"

  - alert: ValidationErrorRateHigh
    expr: rate(validation_errors_total[5m]) > 0.1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "验证错误率过高"
      description: "验证错误率 {{ $value }} 超过10%"
```

---

## 🔄 持续集成/持续部署

### 1. CI/CD流水线

```yaml
# .github/workflows/validation-system.yml
name: GTPlanner Validation System CI/CD

on:
  push:
    branches: [main, develop]
    paths: ['agent/validation/**']
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run validation system tests
      run: |
        cd GTPlanner
        python tests/validation/test_comprehensive_validation.py
    
    - name: Performance benchmark
      run: |
        cd GTPlanner
        python -c "
        import asyncio
        from tests.validation.performance_test import run_performance_benchmark
        asyncio.run(run_performance_benchmark())
        "
    
    - name: Generate coverage report
      run: |
        pytest --cov=agent.validation --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        # 部署到生产环境
        echo "部署验证系统到生产环境"
```

### 2. 部署验证脚本

```python
#!/usr/bin/env python3
# validate_deployment.py

import asyncio
import requests
import time

async def validate_deployment(base_url: str = "http://localhost:8000"):
    """验证部署是否成功"""
    
    print(f"🔍 验证部署: {base_url}")
    
    # 1. 健康检查
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ 健康检查通过")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 2. 验证系统状态检查
    try:
        response = requests.get(f"{base_url}/api/validation/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ 验证系统状态: {status_data.get('status', 'unknown')}")
        else:
            print(f"❌ 验证系统状态检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 验证系统状态异常: {e}")
        return False
    
    # 3. 功能测试
    try:
        test_data = {
            "session_id": "deployment_test_session",
            "dialogue_history": [
                {"role": "user", "content": "部署测试消息", "timestamp": "2023-01-01T12:00:00Z"}
            ],
            "tool_execution_results": {},
            "session_metadata": {"language": "zh"}
        }
        
        response = requests.post(
            f"{base_url}/api/chat/agent",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 功能测试通过")
        else:
            print(f"❌ 功能测试失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 功能测试异常: {e}")
        return False
    
    # 4. 恶意请求测试
    try:
        malicious_data = {
            "session_id": "test_session",
            "dialogue_history": [
                {"role": "user", "content": "<script>alert('xss')</script>", "timestamp": "2023-01-01T12:00:00Z"}
            ],
            "tool_execution_results": {},
            "session_metadata": {}
        }
        
        response = requests.post(
            f"{base_url}/api/chat/agent",
            json=malicious_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 403:
            print("✅ 安全检测正常")
        else:
            print(f"⚠️ 安全检测可能有问题: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ 安全测试异常: {e}")
    
    print("🎉 部署验证完成")
    return True

if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = asyncio.run(validate_deployment(base_url))
    sys.exit(0 if success else 1)
```

---

## 📋 部署检查清单

### 部署前检查

- [ ] **代码检查**
  - [ ] 所有测试通过
  - [ ] 代码覆盖率 > 80%
  - [ ] 性能基准测试通过
  - [ ] 安全扫描通过

- [ ] **配置检查**
  - [ ] 生产环境配置文件就绪
  - [ ] 环境变量配置正确
  - [ ] 敏感信息已脱敏
  - [ ] 配置验证通过

- [ ] **依赖检查**
  - [ ] Python版本兼容
  - [ ] 所有依赖包已安装
  - [ ] 数据库连接正常
  - [ ] Redis连接正常（如果使用）

### 部署后检查

- [ ] **功能检查**
  - [ ] 健康检查端点正常
  - [ ] 验证系统状态正常
  - [ ] API端点验证正常
  - [ ] 错误响应格式正确

- [ ] **性能检查**
  - [ ] 响应时间 < 100ms
  - [ ] 内存使用正常
  - [ ] CPU使用率正常
  - [ ] 缓存命中率 > 70%

- [ ] **监控检查**
  - [ ] 日志记录正常
  - [ ] 指标收集正常
  - [ ] 告警配置正确
  - [ ] 监控面板数据正常

---

*本部署指南版本: 1.0.0*  
*最后更新: 2025年9月*  
*GTPlanner 团队*
