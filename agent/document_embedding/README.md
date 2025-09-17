# 文档嵌入模块

基于canvas.md设计文档实现的智能文档嵌入系统，为基于LLM的智能文档编辑功能提供核心的文档知识感知能力。

## 🎯 核心功能

### 1. 统一变更模型支持
- 将任何用户指令理解为"变更提案"
- 智能分析指令意图和影响范围
- 支持从单个错字修复到跨文件重构的统一处理

### 2. 会话级文档知识感知
- **会话隔离**: 每个会话的文档索引相互独立（`session-{sessionId}`命名空间）
- **RAG检索**: 检索增强生成，确保修改的准确性和上下文一致性
- **实时更新**: 文档变更后自动同步更新知识库

### 3. 智能文档处理
- **分层分割**: 基于Markdown结构的智能文档分割
- **富元数据**: 生成包含标题层级、块类型等丰富元数据的文本块
- **重叠处理**: 智能添加块间重叠，保证上下文连续性

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  DocumentProcessor  │    │  EmbeddingService   │    │  DocumentIndexer    │
│                 │    │                 │    │                 │
│ • 智能文档分割    │    │ • OpenAI兼容API  │    │ • 会话级命名空间  │
│ • Markdown结构   │    │ • 批量处理      │    │ • 向量数据库API  │
│ • 元数据生成     │    │ • 异步处理      │    │ • 增量更新      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ DocumentEmbedding │
                    │    Pipeline     │
                    │                 │
                    │ • 完整处理流程   │
                    │ • 统一接口      │
                    │ • 错误处理      │
                    └─────────────────┘
```

## 📚 主要组件

### DocumentProcessor
智能文档分割器，实现基于Markdown结构的分层分割策略：

```python
from agent.document_embedding import DocumentProcessor

processor = DocumentProcessor(
    chunk_size=1000,      # 目标块大小
    min_chunk_size=100,   # 最小块大小
    chunk_overlap=200     # 块重叠大小
)

chunks = processor.process_documents(session_id, documents)
```

### VectorServiceClient
向量服务客户端，基于OpenAPI规范提供统一的向量服务接口：

```python
from utils.vector_service_client import get_vector_service_client

client = get_vector_service_client()

embeddings = await service.embed_chunks(chunks)
```

### DocumentIndexer
会话级索引管理器，负责向量数据库操作：

```python
from agent.document_embedding import DocumentIndexer

indexer = DocumentIndexer()
result = await indexer.index_documents(session_id, chunks, embeddings)
```

## 🚀 快速开始

### 1. 基本使用

```python
import asyncio
from agent.document_embedding import index_documents, search_documents

async def main():
    # 准备文档数据
    documents = [
        {
            "documentId": "project-plan.md",
            "content": "# 项目计划\n\n本项目的代号是Alpha..."
        },
        {
            "documentId": "tech-spec.md", 
            "content": "# 技术规格\n\nAlpha模块需要暴露以下接口..."
        }
    ]
    
    # 索引文档
    response = await index_documents("session-123", documents)
    print(f"索引状态: {response.status}")
    print(f"处理文档: {response.indexed_documents}")
    print(f"生成块数: {response.total_chunks_created}")
    
    # 搜索文档
    results = await search_documents("session-123", "Alpha项目的技术栈是什么？")
    print(f"搜索结果: {results['total']} 个")

asyncio.run(main())
```

### 2. 使用完整流水线

```python
from agent.document_embedding import get_document_embedding_pipeline, IndexDocumentsRequest

# 获取流水线实例
pipeline = get_document_embedding_pipeline(
    embedding_model="text-embedding-3-small",
    chunk_size=1000,
    vector_service_url="http://localhost:8080"
)

# 创建索引请求
request = IndexDocumentsRequest(
    session_id="session-123",
    documents=documents
)

# 执行索引
response = await pipeline.index_documents(request)
```

## 🔌 API接口

文档嵌入API已成功接入FastAPI主应用，可通过以下地址访问：

**基础URL**: `http://localhost:11211/api/document-embedding`

### POST /api/document-embedding/index-documents
文档首次索引接口

```json
{
  "sessionId": "session-uuid-1234",
  "documents": [
    {
      "documentId": "1.md",
      "content": "# 项目计划\n\n本项目的代号是Alpha..."
    }
  ]
}
```

### POST /api/document-embedding/search
文档检索接口

```json
{
  "sessionId": "session-uuid-1234",
  "query": "Alpha项目的技术栈是什么？",
  "topK": 5
}
```

### POST /api/document-embedding/update-knowledge-base
知识库更新接口

```json
{
  "sessionId": "session-uuid-1234",
  "updatedDocuments": [
    {
      "documentId": "1.md",
      "content": "# 项目计划 (更新版)\n\n本项目的代号已更新为Omega..."
    }
  ]
}
```

## ⚙️ 配置说明

### 环境变量
```bash
# LLM配置（用于嵌入API）
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=text-embedding-3-small

# 向量服务配置
VECTOR_SERVICE_BASE_URL=http://localhost:8080
VECTOR_SERVICE_TIMEOUT=30
```

### settings.toml配置
```toml
[default.vector_service]
base_url = "http://localhost:8080"
timeout = 30
vector_field = "content"

[default.embedding]
model = "text-embedding-3-small"
chunk_size = 1000
min_chunk_size = 100
chunk_overlap = 200
batch_size = 100
```

## 🧪 测试

运行测试脚本：

```bash
cd agent/document_embedding
python test_embedding.py
```

测试包括：
- 文档处理器测试
- 嵌入服务测试  
- 索引器测试
- 完整流水线测试

## 📋 依赖要求

- Python 3.8+
- FastAPI
- OpenAI Python SDK
- requests
- dynaconf
- 向量数据库服务（兼容openapi.json规范）

## 🔄 与canvas.md设计的对应关系

| canvas.md设计 | 实现组件 | 说明 |
|--------------|---------|------|
| 会话级首次索引 | `DocumentEmbeddingPipeline.index_documents()` | POST /index-documents接口 |
| 智能文本分割 | `DocumentProcessor` | 分层分割策略 |
| 向量化 | `VectorServiceClient` | 基于OpenAPI规范的向量服务 |
| 会话级存储 | `DocumentIndexer` | session-{sessionId}命名空间 |
| 知识库更新 | `DocumentEmbeddingPipeline.update_knowledge_base()` | POST /update-knowledge-base接口 |
| RAG检索 | `DocumentIndexer.search_documents()` | 会话级检索 |

## 🚀 快速启动

### 1. 启动FastAPI应用

```bash
# 启动主应用（包含文档嵌入API）
python fastapi_main.py

# 或使用uvicorn
uvicorn fastapi_main:app --host 0.0.0.0 --port 11211 --reload
```

### 2. 测试API接口

```bash
# 运行集成测试
python test_document_embedding_api.py

# 或使用HTTP客户端测试
# 参考 test_document_embedding.http 文件
```

### 3. 健康检查

```bash
curl http://localhost:11211/api/document-embedding/health
```

## 🧪 测试文件

- `test_document_embedding_api.py` - Python集成测试脚本
- `test_document_embedding.http` - HTTP客户端测试文件
- `test_embedding.py` - 单元测试脚本

## 🚧 后续开发

1. **变更提案接口**: 实现POST /propose-changes接口
2. **增量更新优化**: 实现更精细的增量更新逻辑
3. **性能优化**: 添加缓存和批处理优化
4. **监控指标**: 添加详细的性能监控和日志
5. **错误恢复**: 实现更完善的错误处理和恢复机制

## 📖 更多信息

- 详细设计文档: [canvas.md](../../canvas.md)
- 向量数据库API规范: [openapi.json](../../openapi.josn)
- 项目整体架构: [系统架构文档](../../docs/system-architecture.md)
