# Research Agent 数据流向文档

## 概述

Research Agent 是 GTPlanner 中负责研究调研的专业 Agent，使用 pocketflow 框架实现。本文档详细记录了 Research Agent 的数据流向、共享变量变化和节点调用过程。

**✅ 已验证**: 本文档基于真实测试结果更新，所有功能已通过完整测试验证。

## 架构概览

```
Research Agent 主流程
├── 并发批处理多个关键词
├── 每个关键词执行独立的子流程
└── 最终聚合所有结果

子流程架构（单个关键词）：
NodeSearch → NodeURL → LLMAnalysisNode → ResultAssemblyNode
```

## 文件结构

```
agent/subflows/research/
├── __init__.py                     # 主包导入
├── nodes/                          # 节点文件夹
│   ├── __init__.py                # 节点包导入
│   ├── llm_analysis_node.py       # LLM分析节点
│   ├── result_assembly_node.py    # 结果组装节点
│   └── process_research_node.py   # 研究处理节点
├── flows/                          # 流程文件夹
│   ├── __init__.py                # 流程包导入
│   ├── keyword_research_flow.py   # 关键词研究子流程
│   └── research_flow.py           # 主研究流程
├── utils/                          # 工具文件夹
│   ├── __init__.py                # 工具包导入
│   └── research_aggregator.py     # 研究结果聚合器
└── test/                           # 测试文件夹
    ├── __init__.py                # 测试包导入
    ├── test_research_flow.py      # 基础测试
    ├── test_real_api.py           # 真实API测试
    ├── debug_data_flow.py         # 数据流调试
    └── debug_search.py            # 搜索功能调试
```

## 共享变量结构（基于pocketflow最佳实践）

### 子流程共享变量（pocketflow字典类型）

```python
subflow_shared = {
    # === 输入参数 ===
    "current_keyword": str,           # 当前处理的关键词
    "analysis_requirements": str,     # LLM分析的具体要求
    "search_keywords": List[str],     # 搜索关键词列表
    "max_search_results": int,        # 最大搜索结果数量

    # === 流程中间数据（各节点通过shared["key"]填充） ===
    "first_search_result": dict,     # NodeSearch填充：首条搜索结果
    "all_search_results": List[dict], # NodeSearch填充：所有搜索结果
    "url_content": str,               # NodeURL填充：解析的网页内容
    "url_title": str,                 # NodeURL填充：网页标题
    "url_metadata": dict,             # NodeURL填充：网页元数据
    "llm_analysis": dict,             # LLMAnalysisNode填充：分析结果
    "analyzed_keyword": str,          # LLMAnalysisNode填充：已分析的关键词
    "keyword_report": dict            # ResultAssemblyNode填充：最终报告
}

# 重要：所有节点都使用 shared["key"] 访问，而不是 shared.attribute
```

### 主流程共享状态（对象类型）

```python
shared.research_findings = {
    "research_report": List[dict],    # 所有关键词的研究报告
    "aggregated_summary": dict,       # 聚合后的总结
    "research_metadata": {            # 研究元数据
        "research_keywords": List[str],
        "total_keywords": int,
        "successful_keywords": int,
        "success_rate": float,
        "research_completed_at": float,
        "research_success": bool
    }
}
```

## 详细数据流向

### 1. NodeSearch (搜索节点)

#### 调用前共享变量状态
```python
{
    "current_keyword": "Python编程",
    "analysis_requirements": "重点关注Python编程的基础概念和应用场景",
    "search_keywords": ["Python编程"],
    "max_search_results": 5,
    "first_search_result": {},        # 空
    "all_search_results": [],         # 空
    "url_content": "",                # 空
    "llm_analysis": {},               # 空
    "keyword_report": {}              # 空
}
```

#### 节点处理过程
1. **prep()**: 从 `search_keywords` 获取关键词
2. **exec()**: 调用 Jina 搜索 API
3. **post()**: 保存搜索结果到共享变量

#### 调用后共享变量状态
```python
{
    "current_keyword": "Python编程",
    "analysis_requirements": "重点关注Python编程的基础概念和应用场景",
    "search_keywords": ["Python编程"],
    "max_search_results": 5,
    "first_search_result": {          # ✅ 新增
        "title": "Python 教程— Python 3.13.5 文档",
        "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html",
        "snippet": "Python 是一门易于学习、功能强大的编程语言...",
        "search_keyword": "Python编程",
        "rank": 1,
        "source_type": "docs",
        "relevance_score": 0.8
    },
    "all_search_results": [           # ✅ 新增
        {...},  # 10个搜索结果
        {...},
        ...
    ],
    "url_content": "",                # 未变
    "llm_analysis": {},               # 未变
    "keyword_report": {}              # 未变
}
```

### 2. NodeURL (URL解析节点)

#### 调用前共享变量状态
```python
# 继承上一步的状态，重点关注：
{
    "first_search_result": {
        "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html"
    },
    "url_content": "",                # 待填充
    "url_title": "",                  # 待填充
    "url_metadata": {}                # 待填充
}
```

#### 节点处理过程
1. **prep()**: 从 `first_search_result.url` 获取URL
2. **exec()**: 调用 Jina Web API 解析网页
3. **post()**: 保存解析结果到共享变量

#### 调用后共享变量状态
```python
{
    # ... 其他变量保持不变 ...
    "url_content": "Python 教程 — Python 3.13.5 文档\n\n...",  # ✅ 新增 10000+字符
    "url_title": "Python 教程— Python 3.13.5 文档",              # ✅ 新增
    "url_metadata": {                                            # ✅ 新增
        "author": "",
        "publish_date": "",
        "tags": [],
        "description": "Python官方教程文档"
    }
}
```

### 3. LLMAnalysisNode (LLM分析节点)

#### 调用前共享变量状态
```python
# 重点关注：
{
    "url_content": "Python 教程 — Python 3.13.5 文档...",  # 10000+字符
    "current_keyword": "Python编程",
    "analysis_requirements": "重点关注Python编程的基础概念和应用场景",
    "llm_analysis": {},               # 待填充
    "analyzed_keyword": ""            # 待填充
}
```

#### 节点处理过程
1. **prep()**: 获取URL内容、关键词和分析需求
2. **exec()**: 调用LLM API进行内容分析
3. **post()**: 保存分析结果到共享变量

#### 调用后共享变量状态
```python
{
    # ... 其他变量保持不变 ...
    "llm_analysis": {                 # ✅ 新增
        "key_insights": [
            "Python被设计为易于学习且功能强大的编程语言，适合有编程基础的学习者",
            "Python适用于脚本编写和快速应用开发，支持面向对象编程"
        ],
        "relevant_information": "Python是一种解释型、高级编程语言...",
        "technical_details": [
            "Python支持多种编程范式",
            "Python有丰富的标准库"
        ],
        "recommendations": [
            "建议从基础语法开始学习",
            "多做实践项目"
        ],
        "relevance_score": 0.9,
        "summary": "Python教程内容分析"
    },
    "analyzed_keyword": "Python编程"   # ✅ 新增
}
```

### 4. ResultAssemblyNode (结果组装节点)

#### 调用前共享变量状态
```python
# 所有前面步骤的数据都已准备好：
{
    "current_keyword": "Python编程",
    "first_search_result": {...},
    "url_content": "...",
    "llm_analysis": {...},
    "keyword_report": {}              # 待填充
}
```

#### 节点处理过程
1. **prep()**: 收集所有相关数据
2. **exec()**: 组装成完整的关键词报告
3. **post()**: 保存最终报告到共享变量

#### 调用后共享变量状态（最终状态）
```python
{
    # ... 所有前面的变量保持不变 ...
    "keyword_report": {               # ✅ 新增 - 最终产物
        "keyword": "Python编程",
        "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html",
        "title": "Python 教程— Python 3.13.5 文档",
        "content": "Python 教程 — Python 3.13.5 文档...",  # 截取前1000字符
        "analysis": {
            "key_insights": [
                "Python被设计为易于学习且功能强大的编程语言，适合有编程基础的学习者",
                "Python适用于脚本编写和快速应用开发，支持面向对象编程"
            ],
            "relevant_information": "Python是一种解释型、高级编程语言...",
            "technical_details": [
                "Python支持多种编程范式",
                "Python有丰富的标准库"
            ],
            "recommendations": [
                "建议从基础语法开始学习",
                "多做实践项目"
            ],
            "relevance_score": 0.9,
            "summary": "Python教程内容分析"
        },
        "processed_at": 1704067200.123
    }
}
```

## 主流程聚合过程

### ResearchFlow 并发处理

对每个关键词执行上述子流程，收集所有 `keyword_report`：

```python
research_report = [
    {
        "keyword": "Python编程",
        "url": "https://docs.python.org/...",
        "analysis": {...},
        ...
    },
    {
        "keyword": "机器学习", 
        "url": "https://zh.wikipedia.org/...",
        "analysis": {...},
        ...
    }
    # ... 更多关键词报告
]
```

### ResearchAggregator 结果聚合

```python
aggregated_summary = {
    "overall_summary": "完成了5个关键词的研究分析，平均相关性: 0.85",
    "key_findings": [
        "Python被设计为易于学习且功能强大的编程语言",
        "机器学习是人工智能的核心技术",
        # ... 去重后的所有洞察
    ],
    "technical_insights": [
        "Python支持多种编程范式",
        "机器学习算法需要大量数据训练",
        # ... 去重后的技术细节
    ],
    "recommendations": [
        "建议从基础语法开始学习",
        "多做实践项目",
        # ... 去重后的建议
    ],
    "coverage_analysis": {
        "total_keywords": 5,
        "successful_keywords": 4,
        "average_relevance": 0.85,
        "high_quality_results": 3
    }
}
```

## 错误处理机制

### 节点级错误处理
- 每个节点的 `post()` 方法检查 `exec_res` 中的错误
- 返回 "error" 动作，流程直接结束
- 错误信息保存到共享变量中

### 关键词级错误隔离
- 单个关键词失败不影响其他关键词
- 使用独立的共享变量实例
- 并发处理确保错误隔离

### 流程级降级处理
- LLM分析失败时使用模拟结果
- 搜索API失败时使用模拟数据
- 确保流程能够完整执行

## 配置和环境

### 必需的环境变量
```bash
JINA_API_KEY=your_jina_api_key_here
LLM_API_KEY=your_llm_api_key_here
LLM_MODEL=deepseek-v3
```

### 配置文件
- `settings.toml`: 主配置文件
- `.env`: 环境变量文件
- `utils/config_manager.py`: 配置管理器

## 测试和调试

### 测试文件
- `test_research_flow.py`: 基础功能测试
- `test_real_api.py`: 真实API测试
- `debug_data_flow.py`: 数据流调试
- `debug_search.py`: 搜索功能调试

### 调试技巧
1. 使用调试脚本查看每个阶段的数据
2. 检查共享变量的变化过程
3. 验证API调用的返回结果
4. 监控错误处理机制

---

*本文档记录了 Research Agent 的完整数据流向，为开发和维护提供参考。*
